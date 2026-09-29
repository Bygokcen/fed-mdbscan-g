"""Count-derived audit report; completeness is determined by the frozen manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from simulation.run_batch_experiments import (
    _atomic_write_json, _atomic_write_csv, _read_valid_unit, _sha256_json, BatchContractError,
)


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def f1(tp, fp, fn):
    return ratio(2 * tp, 2 * tp + fp + fn)


def summarise_unit(unit, job):
    records = unit['records']
    metadata = unit['run_metadata']
    counts = {k: sum(r[k] for r in records) for k in ['tp', 'fp', 'tn', 'fn']}
    alerts = {k: sum(r.get(k, 0) for r in records)
              for k in ['alert_tp', 'alert_fp', 'alert_tn', 'alert_fn']}
    row = dict(job=job['id'], phase=job['phase'], dataset=job['dataset'],
               scenario=job['scenario']['id'], method=unit['method'], seed=unit['seed'],
               accuracy=records[-1]['accuracy'], balanced_accuracy=records[-1].get('balanced_accuracy'),
               **counts, f1=f1(counts['tp'], counts['fp'], counts['fn']),
               fpr=ratio(counts['fp'], counts['fp'] + counts['tn']),
               tpr=ratio(counts['tp'], counts['tp'] + counts['fn']),
               **alerts, alert_precision=ratio(alerts['alert_tp'], alerts['alert_tp'] + alerts['alert_fp']),
               alert_recall=ratio(alerts['alert_tp'], alerts['alert_tp'] + alerts['alert_fn']),
               alert_clean_fpr=ratio(alerts['alert_fp'], alerts['alert_fp'] + alerts['alert_tn']),
               attack_prevalence=ratio(alerts['alert_tp'] + alerts['alert_fn'], len(records)),
               server_seconds_mean=float(np.mean([r.get('server_total_time', r['time_elapsed']) for r in records])),
               round_seconds_mean=float(np.mean([r.get('round_total_time', r['time_elapsed']) for r in records])),
               fallback_rounds=sum(bool(r['fallback_applied']) for r in records),
               active_clients=records[-1].get('n_active'),
               max_malicious_ratio=max(r['n_malicious'] / r['n_participants'] for r in records),
               moved_samples=metadata.get('partition_repair', {}).get('moved_samples'),
               backdoor_asr=records[-1].get('backdoor_asr'),
               dataset_identity_sha256=_sha256_json(metadata['dataset_identity']),
               model_identity_sha256=metadata['model_identity']['sha256'],
               partition_sha256=metadata['partition_sha256'],
               initial_model_sha256=metadata['initial_model_sha256'],
               schedule_sha256=metadata.get('schedule_sha256'),
               payload_sha256=unit['payload_sha256'])
    active_rounds = [r for r in records if r.get('attack_active')]
    first_active = active_rounds[0]['round'] if active_rounds else None
    detections = [r['round'] for r in active_rounds if r.get('attack_alert')]
    row['onset_alert_delay'] = detections[0] - first_active if detections else None
    row['onset_detected'] = bool(detections) if active_rounds else None
    post = [r for r in records if active_rounds and r['round'] > active_rounds[-1]['round']]
    row['post_attack_alert_fpr'] = ratio(sum(bool(r.get('attack_alert')) for r in post), len(post))
    groups = {}
    for r in records:
        for name, c in r.get('group_confusion', {}).items():
            g = groups.setdefault(name, {'fp': 0, 'tn': 0})
            g['fp'] += c['fp']
            g['tn'] += c['tn']
    group_rows = [dict(job=row['job'], dataset=row['dataset'], scenario=row['scenario'],
                       method=row['method'], seed=row['seed'], group=name, **c,
                       fpr=ratio(c['fp'], c['fp'] + c['tn'])) for name, c in groups.items()]
    return row, group_rows


def paired_rows(rows):
    lookup = {(r['phase'], r['dataset'], r['scenario'], r['method'], r['seed']): r for r in rows}
    pairs = []
    for row in rows:
        candidates = []
        if row['phase'] == 'main':
            candidates.append(('attack_minus_clean', ('clean', row['dataset'], row['scenario'], row['method'], row['seed'])))
            if row['method'] != 'fed_mdbscan_g':
                candidates.append(('method_minus_full', ('main', row['dataset'], row['scenario'], 'fed_mdbscan_g', row['seed'])))
        elif row['phase'] == 'ablation':
            candidates.append(('ablation_minus_full', ('main', row['dataset'], row['scenario'], 'fed_mdbscan_g', row['seed'])))
        elif row['phase'] == 'oracle':
            candidates.append(('oracle_minus_attacked', ('main', row['dataset'], row['scenario'], row['method'], row['seed'])))
        elif row['method'] != 'fed_mdbscan_g':
            candidates.append(('method_minus_full', (row['phase'], row['dataset'], row['scenario'], 'fed_mdbscan_g', row['seed'])))
        for contrast, key in candidates:
            reference = lookup.get(key)
            if reference is None:
                continue
            if any(row[k] is None or row[k] != reference[k] for k in
                   ['dataset_identity_sha256', 'model_identity_sha256', 'partition_sha256', 'initial_model_sha256', 'schedule_sha256']):
                raise BatchContractError(f'paired identity mismatch: {row["job"]}/{row["method"]}')
            pair = {k: row[k] for k in ['phase', 'dataset', 'scenario', 'method', 'seed']}
            pair.update(contrast=contrast, reference_job=reference['job'], reference_method=reference['method'])
            for k in ['accuracy', 'balanced_accuracy', 'fpr', 'f1', 'backdoor_asr', 'server_seconds_mean']:
                pair[f'{k}_delta'] = (row[k] - reference[k]
                                      if row.get(k) is not None and reference.get(k) is not None else None)
            pairs.append(pair)
    return pairs


def aggregate_cells(rows):
    if not rows:
        return []
    cells = []
    for key, group in pd.DataFrame(rows).groupby(['phase', 'dataset', 'scenario', 'method'], sort=False):
        cell = dict(zip(['phase', 'dataset', 'scenario', 'method'], key))
        cell['n_seeds'] = len(group)
        for name in ['accuracy', 'balanced_accuracy', 'f1', 'fpr', 'tpr', 'server_seconds_mean', 'backdoor_asr']:
            values = pd.to_numeric(group[name], errors='coerce').dropna()
            cell[name + '_mean'] = float(values.mean()) if len(values) else None
            cell[name + '_std'] = float(values.std(ddof=1)) if len(values) > 1 else None
        counts = {k: int(group[k].sum()) for k in ['tp', 'fp', 'tn', 'fn']}
        cell.update(counts)
        cell['f1_pooled_counts'] = f1(counts['tp'], counts['fp'], counts['fn'])
        cells.append(cell)
    return cells


def report_campaign(root):
    from simulation.run_audit_campaign import load_manifest, verify_snapshot, job_config
    root = Path(root).resolve()
    output = root / 'report'
    output.mkdir(exist_ok=True)
    _atomic_write_json(str(output / 'completeness.json'), {'complete': False, 'status': 'validating'})
    (output / 'report.md').write_text('# Audit-v2 deney raporu\n\nDoğrulama sürüyor; nihai sonuç değildir.\n')
    for name in ['units.csv', 'cells.csv', 'benign_groups.csv', 'paired_deltas.csv', 'paired_summary.csv']:
        (output / name).unlink(missing_ok=True)
    manifest = load_manifest(root)
    verify_snapshot(root, manifest)
    rows, groups, missing, invalid = [], [], [], []
    for job in manifest['jobs']:
        config = job_config(root, job)
        for method in job['methods']:
            for seed in job['seeds']:
                path = Path(config['output_dir']) / 'runs' / f'{method}_seed{seed}.json'
                if not path.exists():
                    missing.append(str(path.relative_to(root)))
                    continue
                try:
                    unit = _read_valid_unit(path, job['scenario']['id'], method, seed, config)
                    if unit['run_metadata']['dataset_identity'] != manifest['dataset_identities'][job['dataset']]:
                        raise BatchContractError('unit dataset differs from campaign manifest')
                    row, group_rows = summarise_unit(unit, job)
                    rows.append(row)
                    groups.extend(group_rows)
                except (BatchContractError, ValueError, TypeError, KeyError) as exc:
                    invalid.append({'path': str(path.relative_to(root)), 'error': str(exc)})
    try:
        pairs = paired_rows(rows)
    except BatchContractError as exc:
        pairs = []
        invalid.append({'path': 'paired_comparisons', 'error': str(exc)})
    report = dict(complete=not missing and not invalid, valid_units=len(rows),
                  expected_units=manifest['expected_units'], missing=missing, invalid=invalid,
                  manifest_sha256=manifest['manifest_sha256'])
    output = root / 'report'
    output.mkdir(exist_ok=True)
    for filename, data in [('units.csv', rows), ('cells.csv', aggregate_cells(rows)),
                           ('benign_groups.csv', groups), ('paired_deltas.csv', pairs)]:
        _atomic_write_csv(str(output / filename), data)
    if pairs:
        frame = pd.DataFrame(pairs)
        summary = frame.groupby(['phase', 'dataset', 'scenario', 'method', 'contrast'], sort=False).agg(
            n_seeds=('seed', 'size'), accuracy_delta_mean=('accuracy_delta', 'mean'),
            accuracy_delta_std=('accuracy_delta', 'std')).reset_index()
        _atomic_write_csv(str(output / 'paired_summary.csv'), summary.to_dict('records'))
    else:
        _atomic_write_csv(str(output / 'paired_summary.csv'), [])
    _atomic_write_json(str(output / 'completeness.json'), report)
    lines = ['# Audit-v2 deney raporu', '',
             f"Durum: {'TAMAMLANDI' if report['complete'] else 'KISMİ — nihai sonuç değildir'}. "
             f"Doğrulanan birim: {len(rows)}/{manifest['expected_units']}.", '',
             'Her birim bir yöntem/tohum/senaryodur. Doğruluk son round değeridir; standart sapma bağımsız tohumlar üzerindedir. '
             'F1 her birimde gerçek TP/FP/FN toplamlarından hesaplanır; hücrelerde bu F1 değerlerinin ortalaması ve '
             'havuzlanmış count F1 ayrı sütunlardır. Payda sıfırsa metrik boş bırakılır.', '',
             'Eşlenmiş farklarda veri bölünmesi, başlangıç modeli ve katılım takvimi hashleri eşleşmek zorundadır. '
             'Üç tohumla anlamlılık veya genel üstünlük iddiası üretilmez. Grupların dürüst istemci FPR değerleri '
             '`benign_groups.csv` içindedir; küçük grupların paydaları mutlaka dikkate alınmalıdır.', '',
             '`server_seconds_mean` filtreleme, kök model eğitimi ve toplulaştırmayı içerir; '
             'istemci eğitimi/iletişim için ayrı gerçek dağıtık maliyet ölçümü değildir. '
             '`fedavg` uniform mean, `sample_weighted_mean` örnek sayısıyla ağırlıklı ortalamadır.', '',
             'Oracle yalnızca değerlendirici kontrolüdür. MinMax/MinSum tüm dürüst güncellemeleri bilen saldırılardır. '
             'CIFAR-10 koşulları keşif amaçlıdır; yakınsama ayrıca incelenmelidir. '
             'FLAME/FLTrust varyantları makaledeki bileşenlere yaklaştırılmış yerel uygulamalardır; '
             'orijinal yazar koduyla birebir doğrulama ve gizlilik garantisi iddia edilmez.', '',
             f"Geçersiz birim: {len(invalid)}; eksik birim: {len(missing)}. Ayrıntılar: `completeness.json`."]
    temporary = output / 'report.md.tmp'
    temporary.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    temporary.replace(output / 'report.md')
    if invalid:
        raise BatchContractError(f'{len(invalid)} invalid campaign units; see completeness.json')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', required=True)
    args = parser.parse_args()
    print(json.dumps(report_campaign(args.campaign), ensure_ascii=False))
