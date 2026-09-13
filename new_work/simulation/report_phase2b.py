"""
Faz 2b — Paper-ready aggregation report.

Reads:
    new_work/results/heterogeneous_v3_<dataset>/scenario_<id>/runs/*.json

Produces (under new_work/results/phase2b_report/):
    table_final_accuracy.csv      rows = scenario, cols = method (×3 datasets)
    table_fpr.csv                 same shape, FPR
    table_tpr.csv                 same shape, TPR
    table_alert_quality.csv       Fed-MDBSCAN-G only: TP/FP/FN/TN + prec/rec
    summary.json                  machine-readable consolidated view
    console.txt                   human-readable summary print

Metric conventions (paper):
    accuracy_final     = round (max_round) mean across seeds
    accuracy_last5     = mean of last 5 rounds across seeds
    accuracy_round_mean= mean across all rounds × seeds (DIAGNOSTIC ONLY)
    fpr / tpr          = mean across all rounds × seeds
    alert_*            = cumulative counts across all rounds × seeds

Round-mean accuracy is included for inspection but the paper should report
accuracy_final (and last5 in parentheses for stability).
"""

import os
import json
import glob
from collections import defaultdict

import numpy as np
import pandas as pd


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(REPO_ROOT, 'results')
OUT_DIR = os.path.join(RESULTS_DIR, 'phase2b_report')
DATASETS = ['mnist', 'fashion_mnist', 'har']
METHODS = ['fed_mdbscan_g', 'fed_dbscan', 'fed_rra', 'fed_g2l',
           'fedavg', 'krum', 'coord_median', 'fltrust', 'flame']

METHOD_LABELS = {
    'fed_mdbscan_g': 'Fed-MDBSCAN-G',
    'fed_dbscan':    'Fed-DBSCAN',
    'fed_rra':       'FedRRA',
    'fed_g2l':       'FedG2L',
    'fedavg':        'FedAvg',
    'krum':          'Multi-Krum',
    'coord_median':  'Coord-Median',
    'fltrust':       'FLTrust',
    'flame':         'FLAME',
    'qian_mdbscan_vanilla': 'Qian-MDBSCAN (vanilla)',
}


def _load_unit_records(scenario_dir, method, seeds):
    """Load every unit JSON for (method, seeds) and return concatenated records."""
    all_records = []
    seeds_done = []
    for seed in seeds:
        path = os.path.join(scenario_dir, 'runs', f'{method}_seed{seed}.json')
        if not os.path.exists(path):
            continue
        try:
            with open(path) as f:
                unit = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        recs = unit.get('records', [])
        all_records.extend(recs)
        seeds_done.append(seed)
    return all_records, seeds_done


def _aggregate_method(records):
    """Compute paper-ready summary for one (scenario, dataset, method)."""
    if not records:
        return None
    df = pd.DataFrame(records)
    if len(df) == 0:
        return None

    max_round = int(df['round'].max())
    final_mask = df['round'] == max_round
    last5_mask = df['round'] >= max_round - 4

    summary = {
        'n_records':             int(len(df)),
        'max_round':             max_round,
        'accuracy_final':        float(df.loc[final_mask, 'accuracy'].mean()),
        'accuracy_final_std':    float(df.loc[final_mask, 'accuracy'].std()) if final_mask.sum() > 1 else 0.0,
        'accuracy_last5':        float(df.loc[last5_mask, 'accuracy'].mean()),
        'accuracy_last5_std':    float(df.loc[last5_mask, 'accuracy'].std()) if last5_mask.sum() > 1 else 0.0,
        'accuracy_round_mean':   float(df['accuracy'].mean()),  # diagnostic only
        'fpr_mean':              float(df['fpr'].mean()),
        'fpr_std':               float(df['fpr'].std()) if len(df) > 1 else 0.0,
        'tpr_mean':              float(df['tpr'].mean()),
        'tpr_std':               float(df['tpr'].std()) if len(df) > 1 else 0.0,
        'time_mean':             float(df['time_elapsed'].mean()),
    }

    # Fed-MDBSCAN-G xAI alert metrics (cumulative)
    if 'alert_tp' in df.columns:
        atp = int(df['alert_tp'].sum())
        afp = int(df['alert_fp'].sum())
        afn = int(df['alert_fn'].sum())
        atn = int(df['alert_tn'].sum())
        total = atp + afp + afn + atn
        summary.update({
            'alert_tp': atp, 'alert_fp': afp,
            'alert_fn': afn, 'alert_tn': atn,
            'alert_total': total,
            'alert_accuracy':  (atp + atn) / max(total, 1),
            'alert_precision': atp / max(atp + afp, 1),
            'alert_recall':    atp / max(atp + afn, 1),
        })
        for col, out_key in [
            ('density_gap_detected', 'density_gap_rate'),
            ('attack_gate', 'attack_gate_rate'),
            ('attack_alert', 'attack_alert_rate'),
            ('l0_rejected_count', 'l0_rejected_mean'),
            ('l2_rejected_count', 'l2_rejected_mean'),
        ]:
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors='coerce').fillna(0)
                summary[out_key] = float(vals.mean())
    return summary


def collect_all():
    """Walk results/ and aggregate every (dataset, scenario, method) cell."""
    out = defaultdict(lambda: defaultdict(dict))   # out[ds][sid][method] = summary
    scenarios_meta = {}                            # sid -> {label, alpha, ...}
    for ds in DATASETS:
        ds_dir = os.path.join(RESULTS_DIR, f'heterogeneous_v3_{ds}')
        if not os.path.isdir(ds_dir):
            continue
        for sc_dir in sorted(glob.glob(os.path.join(ds_dir, 'scenario_*'))):
            sid = os.path.basename(sc_dir).replace('scenario_', '')
            sc_meta_path = os.path.join(sc_dir, 'scenario_summary.json')
            if not os.path.exists(sc_meta_path):
                continue
            with open(sc_meta_path) as f:
                sc_meta = json.load(f)
            scenarios_meta[sid] = {
                'label': sc_meta.get('label', sid),
                'alpha': sc_meta.get('alpha'),
                'malicious_ratio': sc_meta.get('malicious_ratio'),
                'attack_type': sc_meta.get('attack_type'),
            }
            seeds = sc_meta.get('seeds', [42, 137, 2024])
            for method in METHODS + ['qian_mdbscan_vanilla']:
                recs, _ = _load_unit_records(sc_dir, method, seeds)
                summary = _aggregate_method(recs)
                if summary is not None:
                    out[ds][sid][method] = summary
    return out, scenarios_meta


def _table_metric(out, scenarios_meta, metric_key, methods=METHODS):
    """Build a long-form DataFrame: rows = (dataset, scenario), cols = methods."""
    rows = []
    for sid in sorted(scenarios_meta.keys(), key=lambda s: tuple(int(p) if p.isdigit() else p for p in s.split('.'))):
        for ds in DATASETS:
            cell = {'dataset': ds, 'scenario': sid, 'label': scenarios_meta[sid]['label']}
            for m in methods:
                v = out.get(ds, {}).get(sid, {}).get(m, {}).get(metric_key)
                cell[m] = v
            rows.append(cell)
    return pd.DataFrame(rows)


def _table_alert_quality(out, scenarios_meta):
    rows = []
    for sid in sorted(scenarios_meta.keys(), key=lambda s: tuple(int(p) if p.isdigit() else p for p in s.split('.'))):
        for ds in DATASETS:
            s = out.get(ds, {}).get(sid, {}).get('fed_mdbscan_g', {})
            if not s or 'alert_tp' not in s:
                continue
            rows.append({
                'dataset': ds, 'scenario': sid, 'label': scenarios_meta[sid]['label'],
                'attack_present': scenarios_meta[sid]['malicious_ratio'] > 0,
                'TP': s['alert_tp'], 'FP': s['alert_fp'],
                'FN': s['alert_fn'], 'TN': s['alert_tn'],
                'precision': s['alert_precision'], 'recall': s['alert_recall'],
                'density_gap_rate': s.get('density_gap_rate'),
                'attack_gate_rate': s.get('attack_gate_rate'),
                'attack_alert_rate': s.get('attack_alert_rate'),
            })
    return pd.DataFrame(rows)


def _print_console(out, scenarios_meta):
    lines = []
    lines.append('=' * 110)
    lines.append('  Fed-MDBSCAN-G — Faz 2b paper-ready summary')
    lines.append('=' * 110)
    lines.append('')
    lines.append('  metric: accuracy_final  (round 30, 3-seed mean)')
    lines.append('  rows = (scenario, dataset),  cols = methods')
    lines.append('')

    sids_sorted = sorted(scenarios_meta.keys(),
                        key=lambda s: tuple(int(p) if p.isdigit() else p for p in s.split('.')))

    short = {
        'fed_mdbscan_g': 'MDB-G', 'fed_dbscan': 'F-DBS', 'fed_rra': 'F-RRA',
        'fed_g2l': 'F-G2L', 'fedavg': 'FAvg', 'krum': 'Krum',
        'coord_median': 'CMed', 'fltrust': 'FLTr', 'flame': 'FLAME',
    }
    header = f"  {'Scenario':<28} {'ds':<10} " + ' '.join(f"{short[m]:>7}" for m in METHODS)
    lines.append(header)
    lines.append('  ' + '-' * (len(header) - 2))

    for sid in sids_sorted:
        for ds in DATASETS:
            scell = scenarios_meta[sid]
            label = scell['label'][:26]
            cells = []
            for m in METHODS:
                v = out.get(ds, {}).get(sid, {}).get(m, {}).get('accuracy_final')
                cells.append(f"{v:>7.3f}" if v is not None else f"{'—':>7}")
            lines.append(f"  {sid+' '+label:<28} {ds:<10} " + ' '.join(cells))
        lines.append('')

    return '\n'.join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out, scenarios_meta = collect_all()

    # 1) Final accuracy table
    df_acc = _table_metric(out, scenarios_meta, 'accuracy_final')
    df_acc.to_csv(os.path.join(OUT_DIR, 'table_final_accuracy.csv'), index=False)
    df_last5 = _table_metric(out, scenarios_meta, 'accuracy_last5')
    df_last5.to_csv(os.path.join(OUT_DIR, 'table_last5_accuracy.csv'), index=False)

    # 2) FPR / TPR
    _table_metric(out, scenarios_meta, 'fpr_mean').to_csv(
        os.path.join(OUT_DIR, 'table_fpr.csv'), index=False)
    _table_metric(out, scenarios_meta, 'tpr_mean').to_csv(
        os.path.join(OUT_DIR, 'table_tpr.csv'), index=False)

    # 3) Alert quality (Fed-MDBSCAN-G only)
    df_alert = _table_alert_quality(out, scenarios_meta)
    df_alert.to_csv(os.path.join(OUT_DIR, 'table_alert_quality.csv'), index=False)

    # 4) Consolidated summary JSON
    summary_obj = {
        'metric_conventions': {
            'accuracy_final': 'mean across seeds at round = num_rounds (paper main metric)',
            'accuracy_last5': 'mean across last 5 rounds × seeds (stability)',
            'accuracy_round_mean': 'DIAGNOSTIC ONLY — includes warm-up rounds; do not cite in paper',
            'fpr/tpr': 'mean across all rounds × seeds',
            'alert_*': 'cumulative TP/FP/FN/TN over all rounds × seeds',
        },
        'datasets': DATASETS,
        'methods': METHODS,
        'scenarios': scenarios_meta,
        'cells': {
            ds: {sid: out[ds][sid] for sid in out.get(ds, {})}
            for ds in DATASETS
        },
    }
    with open(os.path.join(OUT_DIR, 'summary.json'), 'w') as f:
        json.dump(summary_obj, f, indent=2)

    # 5) Console pretty
    console_text = _print_console(out, scenarios_meta)
    with open(os.path.join(OUT_DIR, 'console.txt'), 'w') as f:
        f.write(console_text)

    print(console_text)
    print(f"\nWrote: {OUT_DIR}/")
    print(f"  table_final_accuracy.csv")
    print(f"  table_last5_accuracy.csv")
    print(f"  table_fpr.csv")
    print(f"  table_tpr.csv")
    print(f"  table_alert_quality.csv")
    print(f"  summary.json")
    print(f"  console.txt")


if __name__ == '__main__':
    main()
