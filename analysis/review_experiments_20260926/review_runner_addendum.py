#!/usr/bin/env python3
"""E3m of PROTOCOL_ADDENDUM.md: FLAME with random subsets matched to the canonical admitted count.

In every round the frozen FLAME selector runs as usual, so its clipping norm and noise
scale are unchanged, and its selected indices are replaced by a uniformly random subset
whose size equals the admitted count that the canonical FLAME run recorded in the same
round.  The helpers of review_runner.py are imported unchanged, so the frozen source,
the canonical launch environment and the pairing checks are the same as in E3.

    plan | run --parallel N | worker --unit ID | smoke --unit ID (needs ADDENDUM_OUT)
"""
import os
for _var in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_var] = '1'

import argparse
import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('review_runner', HERE / 'review_runner.py')
rr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rr)

OUT = pathlib.Path(os.environ.get('ADDENDUM_OUT', str(rr.ROOT / 'new_work/results/review_20260926_addendum')))
ADDENDUM = HERE / 'PROTOCOL_ADDENDUM.md'
REGISTRATION = HERE / 'protocol_addendum_registration.json'


def build_units():
    units = []
    for ds in ('mnist', 'fashion_mnist', 'har'):
        for s in rr.SEEDS:
            p = rr.reference_path(ds, '6.2', 'flame_hdbscan', s)
            units.append(dict(id=f'E3m_{ds}_6.2_{s}', kind='matched_random', dataset=ds, scenario='6.2',
                              seed=s, method='flame_hdbscan', reference=str(p.relative_to(rr.CANON)),
                              reference_sha256=rr.sha(p)))
    return units


def cmd_plan():
    reg = json.loads(REGISTRATION.read_text())
    rr.require(rr.sha(ADDENDUM) == reg['sha256'], 'addendum changed after registration')
    manifest = json.loads((rr.CANON / 'campaign.json').read_text())
    for rel, digest in manifest['snapshot_files'].items():
        rr.require(rr.sha(rr.CANON / 'source' / rel) == digest, 'frozen source drift: ' + rel)
    OUT.mkdir(parents=True, exist_ok=True)
    rr.require(not (OUT / 'plan.json').exists(), 'plan already exists')
    plan = dict(created_unix=time.time(), addendum_sha256=reg['sha256'], runner_sha256=rr.sha(__file__),
                helper_sha256=rr.sha(HERE / 'review_runner.py'), source_files=rr.source_hashes(),
                units=build_units())
    rr.write(OUT / 'plan.json', plan)
    print(json.dumps(dict(plan=str(OUT / 'plan.json'), units=len(plan['units']))))


def load_plan():
    plan = json.loads((OUT / 'plan.json').read_text())
    rr.require(plan['runner_sha256'] == rr.sha(__file__), 'runner changed after planning')
    rr.require(plan['helper_sha256'] == rr.sha(HERE / 'review_runner.py'), 'helper changed after planning')
    rr.require(plan['addendum_sha256'] == rr.sha(ADDENDUM), 'addendum changed after planning')
    return plan


def run_matched(unit, raw, dest):
    import numpy as np
    import simulation.server as server_module
    from simulation.server import Server
    from simulation.contracts import derive_seed
    from simulation.run_experiment import run_single_experiment
    sizes = [len(r['accepted_ids']) for r in raw['records']]
    rr.require(len(sizes) == 30, 'thirty canonical rounds')
    config = copy.deepcopy(raw['resolved_config'])
    audit = []
    tracker = rr.RoundTracker(Server)
    original = server_module.flame_hdbscan

    def matched(gradients, *args, **kwargs):
        accepted, rejected, info = original(gradients, *args, **kwargs)
        n = len(gradients)
        r = tracker.current['round']
        size = sizes[r]
        rr.require(0 < size < n, f'round {r} canonical size')
        rng = np.random.default_rng(derive_seed(unit['seed'], 'review_matched_random_selection', r))
        chosen = sorted(int(i) for i in rng.choice(n, size=size, replace=False))
        audit.append(dict(round=r, n=n, size=size, rule_size=len(accepted),
                          overlap_with_rule=len(set(chosen) & set(accepted))))
        return chosen, [i for i in range(n) if i not in set(chosen)], dict(info, review_variant='flame_matched_random')

    server_module.flame_hdbscan = matched
    try:
        with tracker:
            metrics = run_single_experiment(config, unit['method'], unit['seed'])
    finally:
        server_module.flame_hdbscan = original
    records = rr.plain(metrics.records)
    identity_mismatch = rr.compare_metadata(metrics.run_metadata, raw['run_metadata'], rr.IDENTITY)
    rr.require(not identity_mismatch, 'pairing identity differs: ' + ','.join(identity_mismatch))
    rr.require(len(audit) == 30 and len(records) == 30, 'one matched selection per round')
    for r, (o, e) in enumerate(zip(records, raw['records'])):
        rr.require(len(o['accepted_ids']) == len(e['accepted_ids']), f'round {r} admitted count')
        rr.require((o['fp'], o['tn'], o['tp'], o['fn']) == (e['fp'], e['tn'], e['tp'], e['fn']), f'round {r} confusion counts')
    rr.write(dest / 'records.json', dict(records=records, run_metadata=rr.plain(metrics.run_metadata),
                                         selection_audit=audit, config=config))
    return dict(final_accuracy=records[-1]['accuracy'], canonical_final_accuracy=raw['records'][-1]['accuracy'],
                identity_checked=list(rr.IDENTITY), admitted_counts_matched=True)


def execute(unit, plan, dest):
    rr.setup(plan)
    ref = rr.CANON / unit['reference']
    rr.require(rr.sha(ref) == unit['reference_sha256'], 'reference hash')
    raw = json.loads(ref.read_text())
    rr.require(raw['method'] == unit['method'] and raw['seed'] == unit['seed'], 'reference identity')
    started = time.time()
    summary = run_matched(unit, raw, dest)
    rr.write(dest / 'done.json', dict(unit=unit, seconds=time.time() - started,
                                      runner_sha256=plan['runner_sha256'], **summary))
    return summary


def cmd_worker(unit_id, smoke=False):
    if smoke:
        rr.require('ADDENDUM_OUT' in os.environ, 'smoke runs need a separate ADDENDUM_OUT')
        plan = dict(source_files=rr.source_hashes(), runner_sha256=rr.sha(__file__), units=build_units())
    else:
        plan = load_plan()
    unit = next(u for u in plan['units'] if u['id'] == unit_id)
    dest = OUT / 'units' / unit_id
    dest.mkdir(parents=True, exist_ok=False)
    try:
        summary = execute(unit, plan, dest)
        print(json.dumps(dict(unit=unit_id, **summary)))
    except Exception:
        rr.write(dest / 'failed.json', dict(unit=unit, traceback=traceback.format_exc()))
        raise


def cmd_run(parallel):
    plan = load_plan()
    (OUT / 'logs').mkdir(exist_ok=True)
    pending = [u['id'] for u in plan['units'] if not (OUT / 'units' / u['id']).exists()]
    status = dict(started_unix=time.time(), total=len(plan['units']), finished={})
    running = {}
    env = {**os.environ, 'PYTHONUNBUFFERED': '1'}
    while pending or running:
        while pending and len(running) < parallel:
            uid = pending.pop(0)
            log = open(OUT / 'logs' / f'{uid}.log', 'w')
            running[uid] = (subprocess.Popen([sys.executable, __file__, 'worker', '--unit', uid],
                                             stdout=log, stderr=subprocess.STDOUT, env=env), log, time.time())
        for uid, (proc, log, t0) in list(running.items()):
            if proc.poll() is not None:
                log.close()
                status['finished'][uid] = dict(returncode=proc.returncode, seconds=time.time() - t0)
                del running[uid]
        status.update(updated_unix=time.time(), running=sorted(running), pending=len(pending),
                      done=sum(v['returncode'] == 0 for v in status['finished'].values()),
                      failed=sorted(k for k, v in status['finished'].items() if v['returncode'] != 0))
        rr.write(OUT / 'status.json', status)
        time.sleep(5)
    print(json.dumps(dict(done=status['done'], failed=status['failed'])))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('plan')
    r = sub.add_parser('run')
    r.add_argument('--parallel', type=int, default=9)
    for name in ('worker', 'smoke'):
        w = sub.add_parser(name)
        w.add_argument('--unit', required=True)
    args = ap.parse_args()
    if args.cmd == 'plan':
        cmd_plan()
    elif args.cmd == 'run':
        cmd_run(args.parallel)
    else:
        cmd_worker(args.unit, smoke=args.cmd == 'smoke')


if __name__ == '__main__':
    main()
