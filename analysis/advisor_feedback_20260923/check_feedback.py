"""Read-only advisor follow-up: exact duplicate density and FLAME round counts.

Historical cluster sizes are justified from saved accepted IDs plus the frozen
selection path; historical HDBSCAN labels were NOT logged or reconstructed.
"""
from __future__ import annotations
import os
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
import ast
import collections
import csv
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

import numpy as np


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def write_csv(path, values):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    inputs = {}

    def record(path, expected=None):
        digest = sha(path)
        require(expected is None or digest == expected, 'hash mismatch: '+str(path))
        inputs[str(path.relative_to(root))] = digest

    archive = root/'new_work/results/validated/audit-v2/full_20260910'
    previous_path = root/'analysis/flame_fidelity_20260920/provenance.json'
    record(previous_path)
    previous = json.loads(previous_path.read_text())
    # Confirm the archived selector/aggregator are the previously audited ones.
    for path, digest in previous['source_hashes'].items():
        if path.startswith('new_work/results/'):
            record(root/path, digest)
    sources = [root/'new_work/simulation/mdbscan.py',
               archive/'source/new_work/simulation/mdbscan.py',
               root/'new_work/results/cutoff_development/study_20260914_v1/source/new_work/simulation/mdbscan.py']
    rd_results, function_ast = [], []
    for number, source in enumerate(sources):
        record(source)
        tree = ast.parse(source.read_text())
        fun = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='compute_relative_density')
        function_ast.append(ast.dump(fun, include_attributes=False))
        module = load_module(source, 'rd_check_%d'%number)
        cases = [
            ('two_duplicates_k1', [[0.], [0.], [.1], [.2]], 1),
            ('six_duplicates_k5', [[0.]]*6+[[.1],[.2]], 5),
            ('all_duplicates_k5', [[0.]]*6, 5),
            ('two_duplicates_not_enough_k5', [[0.],[0.],[.1],[.2],[.3],[.4]], 5),
        ]
        for name, values, k in cases:
            data = np.array(values, dtype=float)
            result = module.compute_relative_density(data, k)
            require(np.isfinite(result).all(), name)
            # Pairwise distances independently establish whether all k neighbours
            # are identical. kNN tie ordering cannot affect this zero sum check.
            pairwise = np.linalg.norm(data[:,None]-data[None,:],axis=2)
            np.fill_diagonal(pairwise, np.inf)
            zero_sums = np.sort(pairwise,axis=1)[:,:k].sum(axis=1)==0
            require(np.array_equal(result[zero_sums], np.ones(zero_sums.sum())), name)
            if name=='two_duplicates_k1':
                require(np.allclose(result,[1,1,10,10]), name)
            if name=='two_duplicates_not_enough_k5':
                require(not zero_sums.any() and not np.any(result==1), name)
            rd_results.append(dict(source=str(source.relative_to(root)), case=name, k=k,
                                   input=values, zero_sum_rows=np.flatnonzero(zero_sums).tolist(),
                                   density=result.tolist()))
    require(len(set(function_ast))==1, 'RD source functions differ')

    # Count saved identities first; rates are only used for cross-checking.
    old_paths = sorted(previous['inputs'])
    actual_paths = sorted(str(p.relative_to(root)) for p in (archive/'runs').rglob('flame_hdbscan_seed*.json'))
    require(actual_paths==old_paths, 'canonical FLAME file inventory changed')
    rounds, groups, failures = [], collections.defaultdict(list), []
    counters = collections.Counter()
    for name in actual_paths:
        path = root/name
        record(path, previous['inputs'][name])
        payload = json.loads(path.read_text())
        parts = path.relative_to(archive).parts
        phase, dataset, scenario = parts[1], parts[2], parts[3].removeprefix('scenario_')
        seed = int(path.stem.split('seed')[1])
        records = payload.get('records', [])
        if parts[4]=='failures':
            require(not records, 'unexpected partial failed record')
            failures.append(dict(phase=phase,dataset=dataset,scenario=scenario,seed=seed,path=name))
            continue
        require(len(records)==30 and [r['round'] for r in records]==list(range(30)), 'round coverage')
        counters['valid_runs'] += 1
        for r in records:
            participants, accepted, rejected = r['participant_ids'],r['accepted_ids'],r['rejected_ids']
            p,a,b = set(participants),set(accepted),set(rejected)
            require(len(p)==len(participants) and len(a)==len(accepted) and len(b)==len(rejected), 'duplicate IDs')
            require(not a&b and a|b==p, 'partition mismatch')
            require(len(p)==r['n_participants']==90, 'cohort mismatch')
            require(len(a)==r['n_benign'] and len(b)==r['n_anomaly'], 'direct count mismatch')
            require(r['fallback_applied']==0 and r['fallback_reason']=='none' and r['degraded']==0, 'nonstandard path')
            require(len(a)<len(p) and len(p)>2, 'skip path cannot be excluded')
            minimum=len(p)//2+1
            require(len(a)>=minimum, 'selection below majority minimum')
            evil=set(r['actual_malicious_ids'])&p
            truth=dict(tp=len(b&evil), fp=len(b-evil), tn=len(a-evil), fn=len(a&evil))
            require(all(truth[k]==r[k] for k in truth), 'identity confusion mismatch')
            row=dict(phase=phase,dataset=dataset,scenario=scenario,seed=seed,round=r['round'],
                     participants=len(p), accepted_set_size=len(a), min_cluster_size=minimum,
                     at_minimum=int(len(a)==minimum), attack_active=int(bool(evil)),
                     tp=truth['tp'],fp=truth['fp'],tn=truth['tn'],fn=truth['fn'])
            rounds.append(row)
            groups[(phase,dataset,scenario)].append(row)
            counters['old_rounds_with_flame_clustering_field'] += 'flame_clustering' in r

    require(counters['valid_runs']==200 and len(rounds)==6000 and len(failures)==1, 'canonical coverage')
    outcome_path = archive/'report/outcomes.csv'
    record(outcome_path)
    outcomes=[r for r in csv.DictReader(outcome_path.open()) if r['method']=='flame_hdbscan']
    require(collections.Counter(r['outcome'] for r in outcomes)=={'valid':200,'failed':1}, 'outcome accounting')
    valid_keys={(r['phase'],r['dataset'],r['scenario'],r['seed']) for r in outcomes if r['outcome']=='valid'}
    require(valid_keys=={(r['phase'],r['dataset'],r['scenario'],str(r['seed'])) for r in rounds}, 'valid unit identity')
    cells_path=archive/'report/cells.csv'
    record(cells_path)
    cells={(r['phase'],r['dataset'],r['scenario']):r for r in csv.DictReader(cells_path.open()) if r['method']=='flame_hdbscan'}
    summary=[]
    for key, rs in sorted(groups.items()):
        sizes=[r['accepted_set_size'] for r in rs]
        totals={col:sum(r[col] for r in rs) for col in ['tp','fp','tn','fn']}
        require(key in cells and all(totals[col]==int(cells[key][col]) for col in totals), 'cell confusion mismatch')
        summary.append(dict(phase=key[0],dataset=key[1],scenario=key[2],
                            runs=len({r['seed'] for r in rs}),rounds=len(rs),
                            min_size=min(sizes),median_size=statistics.median(sizes),
                            mean_size=statistics.mean(sizes),max_size=max(sizes),
                            rounds_at_minimum=sum(r['at_minimum'] for r in rs),
                            fraction_at_minimum=sum(r['at_minimum'] for r in rs)/len(rs),
                            all_attack_free=int(not any(r['attack_active'] for r in rs)),
                            size_histogram=json.dumps(dict(sorted(collections.Counter(sizes).items()))),
                            **totals))
    clean=[r for r in summary if r['phase']=='main' and r['scenario'] in {'1.1','6.1','6.2'}]
    require(len(clean)==11 and all(r['all_attack_free'] and r['rounds']==90 for r in clean), 'clean coverage')
    for path,digest in inputs.items():
        require(sha(root/path)==digest, 'input changed during check')
    write_json(out/'rd_checks.json', dict(function_ast_equal=True,cases=rd_results))
    write_csv(out/'flame_round_counts.csv',rounds)
    write_csv(out/'flame_cell_sizes.csv',summary)
    write_csv(out/'flame_clean_sizes.csv',clean)
    write_json(out/'verification.json',dict(valid_runs=200,failed_runs=failures,recorded_rounds=len(rounds),
              historical_hdbscan_labels_available=False,
              historical_count_source='len(accepted_ids), checked against n_benign and the frozen non-fallback selection path; not recovered from BER',
              old_rounds_with_flame_clustering_field=counters['old_rounds_with_flame_clustering_field'],
              cell_count=len(summary),clean_cells=len(clean),clean_rounds=sum(r['rounds'] for r in clean),
              canonical_fallback_rounds=0,canonical_skip_or_all_accepted_rounds=0,
              clean_rounds_at_minimum=sum(r['rounds_at_minimum'] for r in clean)))
    write_json(out/'provenance.json',dict(script_sha256=sha(Path(__file__)),inputs_sha256=inputs,
               outputs_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},
               note='Read-only canonical archive audit. Hashes establish content, not preregistration.'))
    print(json.dumps(dict(rd_checks=len(rd_results),flame_runs=200,failed_runs=1,rounds=len(rounds),clean_cells=clean),indent=2))


if __name__=='__main__':
    main()
