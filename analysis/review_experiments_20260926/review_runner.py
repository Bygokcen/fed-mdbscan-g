#!/usr/bin/env python3
"""Targeted review experiments of 26 September 2026 (see PROTOCOL.md).

Subcommands
    plan                 freeze the unit list, reference hashes and source hashes
    run --parallel N     execute every pending unit, N worker processes at a time
    worker --unit ID     execute one unit (called by ``run``)

Unit kinds
    capture          E1   re-execute a canonical Fed-MDBSCAN-G run with the frozen
                          canonical source, compare every non-timing round field with
                          the archive, save the server-input matrices of rounds 0, 9
                          and 29 and evaluate two gates x two cutoff settings offline.
    flame_fidelity   E2a  re-execute a canonical FLAME run and, on the identical
                          precomputed distance matrix of every round, also run the
                          reference ``hdbscan`` library (min_samples=1).  The run itself
                          keeps the local selection, so reproduction can be checked.
    flame_nonoise    E2b  canonical FLAME configuration with noise_std = 0.
    random           E3   Multi-Krum or FLAME with the selected indices replaced by a
                          uniformly random subset of the same size.

The canonical archive is read only.  Outputs go to OUT/units/<unit id>/.
"""
import os
for _var in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_var] = '1'

import argparse
import copy
import hashlib
import inspect
import json
import pathlib
import random as pyrandom
import subprocess
import sys
import time
import traceback

ROOT = pathlib.Path('/home/gokcen/Fed_MDBSCAN_TIFS')
CANON = ROOT / 'new_work/results/validated/audit-v2/full_20260910'
SOURCE = CANON / 'source/new_work'
OUT = pathlib.Path(os.environ.get('REVIEW_OUT', str(ROOT / 'new_work/results/review_20260926')))
PYDEPS = ROOT / 'new_work/results/review_20260926/pydeps'
HERE = pathlib.Path(__file__).resolve().parent
PROTOCOL = HERE / 'PROTOCOL.md'
REGISTRATION = HERE / 'protocol_registration.json'

SEEDS = (42, 137, 2024)
CHECKPOINTS = (0, 9, 29)
TIMES = {'time_elapsed', 'aggregation_time', 'root_training_time',
         'server_total_time', 'round_total_time'}
VOLATILE = {'command', 'start_time_unix', 'end_time_unix', 'peak_memory_kib', 'exit_status'}
# Run-metadata fields that must agree with the canonical reference for a paired control.
IDENTITY = ('dataset_identity', 'model_identity', 'partition_sha256', 'schedule_sha256',
            'initial_model_sha256', 'participation_schedule', 'latent_malicious_ids',
            'active_client_ids', 'partition_repair', 'client_metadata')
GATE_EXPR = 'attack_gate = bool(density_gap_detected and l0_supports_attack)'
GATE_FORCED = 'attack_gate = bool(density_gap_detected)'
CUTOFF_EXPR = 'low_data, k, eps=eps_est, original_indices=low_indices'
CUTOFF_OFF = 'low_data, k, eps=None, original_indices=low_indices'
TRACE_KEYS = ('low_indices', 'high_indices', 'natural_clusters', 'rejected_snnc_indices',
              'l0_benign', 'l0_anomalies', 'rd_values', 't_est')


# ----------------------------------------------------------------------------- helpers
def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def require(ok, label):
    if not ok:
        raise RuntimeError(label)


def plain(x):
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, set):
        return sorted(plain(v) for v in x)
    if hasattr(x, 'tolist'):
        return x.tolist()
    return x


def write(path, value):
    path = pathlib.Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(plain(value), indent=1, allow_nan=False) + '\n')
    tmp.replace(path)


def reference_path(dataset, scenario, method, seed):
    return CANON / 'runs/main' / dataset / f'scenario_{scenario}' / 'runs' / f'{method}_seed{seed}.json'


def build_units():
    units = []
    for ds in ('mnist', 'fashion_mnist'):
        for sc in ('7.1', '7.2', '8.1', '8.2', '6.2'):
            for s in SEEDS:
                units.append(dict(id=f'E1_{ds}_{sc}_{s}', kind='capture', dataset=ds,
                                  scenario=sc, seed=s, method='fed_mdbscan_g'))
    for ds in ('mnist', 'fashion_mnist', 'har'):
        for s in SEEDS:
            units.append(dict(id=f'E2b_{ds}_6.2_{s}', kind='flame_nonoise', dataset=ds,
                              scenario='6.2', seed=s, method='flame_hdbscan'))
            units.append(dict(id=f'E3k_{ds}_6.2_{s}', kind='random', variant='krum_random',
                              dataset=ds, scenario='6.2', seed=s, method='krum_bound30'))
            units.append(dict(id=f'E3f_{ds}_6.2_{s}', kind='random', variant='flame_random',
                              dataset=ds, scenario='6.2', seed=s, method='flame_hdbscan'))
    for ds, sc in (('mnist', '1.1'), ('mnist', '6.2'), ('har', '6.2')):
        for s in SEEDS:
            units.append(dict(id=f'E2a_{ds}_{sc}_{s}', kind='flame_fidelity', dataset=ds,
                              scenario=sc, seed=s, method='flame_hdbscan'))
    # Long image runs first, the fast HAR runs last.
    units.sort(key=lambda u: (u['dataset'] == 'har', u['kind'] != 'capture'))
    for u in units:
        p = reference_path(u['dataset'], u['scenario'], u['method'], u['seed'])
        require(p.exists(), 'missing reference ' + str(p))
        u['reference'] = str(p.relative_to(CANON))
        u['reference_sha256'] = sha(p)
    require(len({u['id'] for u in units}) == len(units), 'unique unit ids')
    return units


def source_hashes():
    return {str(p.relative_to(SOURCE)): sha(p)
            for p in sorted((SOURCE / 'simulation').glob('*.py'))}


# ----------------------------------------------------------------------------- plan
def cmd_plan():
    reg = json.loads(REGISTRATION.read_text())
    require(sha(PROTOCOL) == reg['sha256'], 'protocol changed after registration')
    manifest = json.loads((CANON / 'campaign.json').read_text())
    for rel, digest in manifest['snapshot_files'].items():
        require(sha(CANON / 'source' / rel) == digest, 'frozen source drift: ' + rel)
    wheel = sorted((OUT / 'wheels').glob('hdbscan-*.whl'))
    require(len(wheel) == 1, 'hdbscan wheel')
    OUT.mkdir(parents=True, exist_ok=True)
    plan_path = OUT / 'plan.json'
    require(not plan_path.exists(), 'plan already exists')
    plan = dict(created_unix=time.time(), protocol_sha256=reg['sha256'],
                runner_sha256=sha(__file__), canonical_manifest_sha256=manifest['manifest_sha256'],
                canonical_environment=manifest['environment'], source_files=source_hashes(),
                hdbscan_wheel=dict(name=wheel[0].name, sha256=sha(wheel[0])),
                units=build_units())
    write(plan_path, plan)
    print(json.dumps(dict(plan=str(plan_path), units=len(plan['units']))))


def load_plan():
    plan = json.loads((OUT / 'plan.json').read_text())
    require(plan['runner_sha256'] == sha(__file__), 'runner changed after planning')
    require(plan['protocol_sha256'] == sha(PROTOCOL), 'protocol changed after planning')
    return plan


# ----------------------------------------------------------------------------- worker setup
def setup(plan, need_reference_library=False):
    require(source_hashes() == plan['source_files'], 'frozen source changed after planning')
    sys.path.insert(0, str(SOURCE))
    if need_reference_library:
        sys.path.append(str(PYDEPS))
    import torch
    torch.set_num_threads(1)
    require(torch.cuda.is_available(), 'CUDA unavailable')
    import simulation
    require(pathlib.Path(simulation.__file__).resolve().is_relative_to(SOURCE.resolve()),
            'simulation package not imported from the frozen canonical source')


def compare_records(observed, expected):
    mismatches = []
    require(len(observed) == len(expected) == 30, '30 rounds')
    for i, (o, e) in enumerate(zip(observed, expected)):
        o = {k: v for k, v in plain(o).items() if k not in TIMES}
        e = {k: v for k, v in e.items() if k not in TIMES}
        diff = [k for k in sorted(set(o) | set(e)) if o.get(k) != e.get(k)]
        if diff:
            mismatches.append(dict(round=i, fields=diff))
    return mismatches


def compare_metadata(observed, expected, keys=None):
    observed = plain(observed)
    keys = keys or sorted((set(observed) | set(expected)) - VOLATILE)
    return [k for k in keys if observed.get(k) != expected.get(k)]


class RoundTracker:
    """Patch Server.aggregate to expose the round id and participants to hooks."""

    def __init__(self, server_cls):
        self.server_cls = server_cls
        self.original = server_cls.aggregate
        self.current = {}

    def __enter__(self):
        tracker = self

        def aggregate(server, gradients, *args, **kwargs):
            participants = kwargs.get('participating_ids', args[0] if args else [])
            tracker.current = dict(round=kwargs.get('round_id'), participants=list(participants),
                                   state=copy.deepcopy(server.export_defense_state()))
            return tracker.original(server, gradients, *args, **kwargs)
        self.server_cls.aggregate = aggregate
        return self

    def __exit__(self, *exc):
        self.server_cls.aggregate = self.original
        return False


def traced(fn, matrix, kwargs):
    captured = {}

    def trace(frame, event, arg):
        if frame.f_code is fn.__code__ and event == 'return':
            for key in TRACE_KEYS:
                if key in frame.f_locals:
                    captured[key] = plain(frame.f_locals[key])
        return trace
    old = sys.gettrace()
    sys.settrace(trace)
    try:
        result = fn(matrix.copy(), **copy.deepcopy(kwargs))
    finally:
        sys.settrace(old)
    captured['partition_executed'] = 'low_indices' in captured
    return result, captured


def variants(module):
    fn = module.fed_mdbscan_g_filter
    source = inspect.getsource(fn)
    require(source.count(GATE_EXPR) == 1, 'unique gate expression')
    require(source.count(CUTOFF_EXPR) == 1, 'unique cutoff expression')
    out = {}
    for gate in ('original', 'density_only'):
        for cutoff in (True, False):
            text = source
            if gate == 'density_only':
                text = text.replace(GATE_EXPR, GATE_FORCED)
            if not cutoff:
                text = text.replace(CUTOFF_EXPR, CUTOFF_OFF)
            namespace = dict(module.__dict__)
            exec(compile(text, f'<{gate}-cutoff={cutoff}>', 'exec'), namespace)
            out[(gate, cutoff)] = namespace[fn.__name__]
    return out, hashlib.sha256(source.encode()).hexdigest()


def gamma_of(module, matrix, b0, tau):
    import numpy as np
    ordered = sorted(b0)
    require(len(ordered) > 0, 'empty B0')
    trusted = matrix[ordered]
    centre = np.asarray(module._weiszfeld_geometric_median(trusted), dtype=float)
    radii = np.linalg.norm(trusted - centre, axis=1)
    require(np.isfinite(radii).all(), 'non-finite radius')
    median = float(np.median(radii))
    gamma = float(radii.max()) / max(median, 1e-10)
    return dict(b0_size=len(ordered), radius_max=float(radii.max()), radius_median=median,
                gamma=gamma, tau=tau, gamma_le_tau=bool(gamma <= tau))


# ----------------------------------------------------------------------------- E1 capture
def run_capture(unit, raw, dest):
    import numpy as np
    import simulation.mdbscan as mdbscan
    import simulation.server as server_module
    from simulation.server import Server
    from simulation.run_experiment import run_single_experiment
    compiled, source_digest = variants(mdbscan)
    live = server_module.fed_mdbscan_g_filter
    signature = inspect.signature(live)
    captures = {}
    with RoundTracker(Server) as tracker:
        def observer(matrix, *args, **kwargs):
            r = tracker.current['round']
            result = live(matrix, *args, **kwargs)
            if r in CHECKPOINTS:
                require(r not in captures, f'duplicate capture {r}')
                bound = signature.bind(matrix, *args, **kwargs)
                bound.apply_defaults()
                params = dict(bound.arguments)
                params.pop('gradients')
                captures[r] = dict(matrix=np.asarray(matrix).copy(), params=copy.deepcopy(params),
                                   participants=tracker.current['participants'],
                                   state=tracker.current['state'], filter_result=copy.deepcopy(result))
            return result
        server_module.fed_mdbscan_g_filter = observer
        try:
            metrics = run_single_experiment(raw['resolved_config'], unit['method'], unit['seed'])
        finally:
            server_module.fed_mdbscan_g_filter = live
    records = plain(metrics.records)
    record_mismatch = compare_records(records, raw['records'])
    metadata_mismatch = compare_metadata(metrics.run_metadata, raw['run_metadata'])
    require(sorted(captures) == list(CHECKPOINTS), 'checkpoint coverage')
    branches, artifacts, matrices = [], {}, []
    for r in CHECKPOINTS:
        cap = captures[r]
        matrix = cap.pop('matrix')
        path = dest / f'round_{r:02d}_updates.npy'
        np.save(path, matrix)
        artifacts[path.name] = sha(path)
        participants = cap['participants']
        row = records[r]
        malicious = set(row['actual_malicious_ids'])
        tau = float(cap['params'].get('consensus_threshold', 2.0))
        b0_sets = set()
        for (gate, cutoff), fn in compiled.items():
            result, local = traced(fn, matrix, cap['params'] | {'enable_safety_valve': cap['params'].get('enable_safety_valve', True)})
            accepted, rejected, info = result
            n = len(participants)
            require(len(set(accepted)) == len(accepted) and set(accepted).isdisjoint(rejected)
                    and set(accepted) | set(rejected) == set(range(n)), 'index partition')
            if gate == 'original' and cutoff:
                require(plain(result) == plain(cap['filter_result']), f'round {r} compiled baseline')
                require([participants[i] for i in accepted] == row['accepted_ids'], f'round {r} accepted ids')
            b0 = set(local['l0_benign'])
            b0_sets.add(tuple(sorted(b0)))
            groups = local.get('natural_clusters', [])
            reject_ids = {participants[i] for i in rejected}
            removed = b0 - set(accepted)
            branches.append(dict(
                round=r, gate=gate, cutoff=cutoff, partition_executed=local['partition_executed'],
                attack_gate=bool(info.get('attack_gate', False)), layer_used=info.get('layer_used'),
                n=n, b0_size=len(b0), n_groups=len(groups),
                groups_outside_b0=sum(1 for g in groups if not set(g) <= b0),
                rejected_group_members=len(set(local.get('rejected_snnc_indices', []))),
                removed_from_b0=len(removed),
                removed_from_b0_honest=len({participants[i] for i in removed} - malicious),
                removed_from_b0_attackers=len({participants[i] for i in removed} & malicious),
                tp=len(reject_ids & malicious), fp=len(reject_ids - malicious),
                honest_count=len(set(participants) - malicious),
                malicious_count=len(set(participants) & malicious),
                accepted_ids=[participants[i] for i in accepted]))
        require(len(b0_sets) == 1, 'B0 identical across gate and cutoff variants')
        b0 = set(b0_sets.pop())
        matrices.append(dict(round=r, malicious_count=len(malicious & set(participants)),
                             **gamma_of(mdbscan, matrix, b0, tau)))
        write(dest / f'round_{r:02d}_state.json', cap)
        artifacts[f'round_{r:02d}_state.json'] = sha(dest / f'round_{r:02d}_state.json')
    write(dest / 'branches.json', branches)
    write(dest / 'matrices.json', matrices)
    write(dest / 'records.json', dict(records=records, run_metadata=plain(metrics.run_metadata)))
    return dict(exact_reproduction=not record_mismatch and not metadata_mismatch,
                record_mismatches=record_mismatch[:5], mismatched_rounds=len(record_mismatch),
                metadata_mismatches=metadata_mismatch, artifacts=artifacts,
                filter_source_sha256=source_digest)


# ----------------------------------------------------------------------------- E2a fidelity
def run_flame_fidelity(unit, raw, dest):
    import numpy as np
    import sklearn.cluster as skc
    import hdbscan as reference_library
    require(pathlib.Path(reference_library.__file__).resolve().is_relative_to(PYDEPS.resolve()),
            'reference hdbscan imported from the review folder')
    from simulation.server import Server
    from simulation.run_experiment import run_single_experiment
    base = skc.HDBSCAN
    rows = []
    tracker_box = {}

    class Recording(base):
        def fit_predict(self, X, y=None):
            labels = super().fit_predict(X, y)
            state, py_state = np.random.get_state(), pyrandom.getstate()
            try:
                ref = reference_library.HDBSCAN(
                    min_cluster_size=self.min_cluster_size, min_samples=1,
                    allow_single_cluster=self.allow_single_cluster,
                    metric='precomputed').fit_predict(np.array(X, dtype=np.float64, copy=True))
            finally:
                np.random.set_state(state)
                pyrandom.setstate(py_state)
            local = set(np.flatnonzero(labels >= 0).tolist())
            refset = set(np.flatnonzero(ref >= 0).tolist())
            rows.append(dict(round=tracker_box['t'].current.get('round'), n=int(len(labels)),
                             min_cluster_size=int(self.min_cluster_size),
                             local_size=len(local), reference_size=len(refset),
                             equal=local == refset, symmetric_difference=len(local ^ refset),
                             local_clusters=int(labels.max() + 1),
                             reference_clusters=int(ref.max() + 1),
                             local_accepted=sorted(local), reference_accepted=sorted(refset)))
            return labels
    with RoundTracker(Server) as tracker:
        tracker_box['t'] = tracker
        skc.HDBSCAN = Recording
        try:
            metrics = run_single_experiment(raw['resolved_config'], unit['method'], unit['seed'])
        finally:
            skc.HDBSCAN = base
    records = plain(metrics.records)
    record_mismatch = compare_records(records, raw['records'])
    metadata_mismatch = compare_metadata(metrics.run_metadata, raw['run_metadata'])
    write(dest / 'fidelity_rounds.json', rows)
    write(dest / 'records.json', dict(records=records, run_metadata=plain(metrics.run_metadata)))
    return dict(exact_reproduction=not record_mismatch and not metadata_mismatch,
                mismatched_rounds=len(record_mismatch), record_mismatches=record_mismatch[:5],
                metadata_mismatches=metadata_mismatch, clustered_rounds=len(rows),
                equal_rounds=sum(r['equal'] for r in rows))


# ----------------------------------------------------------------------------- E2b / E3
def run_control(unit, raw, dest):
    import numpy as np
    import simulation.server as server_module
    from simulation.server import Server
    from simulation.contracts import derive_seed
    from simulation.run_experiment import run_single_experiment
    config = copy.deepcopy(raw['resolved_config'])
    audit = []
    patched = None
    if unit['kind'] == 'flame_nonoise':
        require(config['method_params']['flame_hdbscan']['noise_std'] == 0.001, 'canonical noise')
        config['method_params']['flame_hdbscan']['noise_std'] = 0.0
    tracker = RoundTracker(Server)
    if unit['kind'] == 'random':
        name = {'krum_random': 'krum', 'flame_random': 'flame_hdbscan'}[unit['variant']]
        original = getattr(server_module, name)

        def randomised(gradients, *args, **kwargs):
            accepted, rejected, info = original(gradients, *args, **kwargs)
            n = len(gradients)
            r = tracker.current['round']
            rng = np.random.default_rng(derive_seed(unit['seed'], 'review_random_selection', r))
            chosen = sorted(int(i) for i in rng.choice(n, size=len(accepted), replace=False))
            audit.append(dict(round=r, n=n, size=len(accepted),
                              overlap_with_rule=len(set(chosen) & set(accepted))))
            info = dict(info, review_variant=unit['variant'])
            return chosen, [i for i in range(n) if i not in set(chosen)], info
        patched = (name, original)
        setattr(server_module, name, randomised)
    try:
        with tracker:
            metrics = run_single_experiment(config, unit['method'], unit['seed'])
    finally:
        if patched:
            setattr(server_module, patched[0], patched[1])
    records = plain(metrics.records)
    identity_mismatch = compare_metadata(metrics.run_metadata, raw['run_metadata'], IDENTITY)
    require(not identity_mismatch, 'pairing identity differs: ' + ','.join(identity_mismatch))
    if unit['kind'] == 'random':
        require(len(audit) == 30, 'one random selection per round')
    write(dest / 'records.json', dict(records=records, run_metadata=plain(metrics.run_metadata),
                                      selection_audit=audit, config=config))
    return dict(final_accuracy=records[-1]['accuracy'],
                canonical_final_accuracy=raw['records'][-1]['accuracy'],
                identity_checked=list(IDENTITY))


# ----------------------------------------------------------------------------- worker / controller
def cmd_worker(unit_id):
    plan = load_plan()
    unit = next(u for u in plan['units'] if u['id'] == unit_id)
    dest = OUT / 'units' / unit_id
    dest.mkdir(parents=True, exist_ok=False)
    started = time.time()
    try:
        setup(plan, need_reference_library=unit['kind'] == 'flame_fidelity')
        ref = CANON / unit['reference']
        require(sha(ref) == unit['reference_sha256'], 'reference hash')
        raw = json.loads(ref.read_text())
        require(raw['method'] == unit['method'] and raw['seed'] == unit['seed'], 'reference identity')
        runner = {'capture': run_capture, 'flame_fidelity': run_flame_fidelity,
                  'flame_nonoise': run_control, 'random': run_control}[unit['kind']]
        summary = runner(unit, raw, dest)
        write(dest / 'done.json', dict(unit=unit, seconds=time.time() - started,
                                       runner_sha256=plan['runner_sha256'], **summary))
    except Exception:
        write(dest / 'failed.json', dict(unit=unit, seconds=time.time() - started,
                                         traceback=traceback.format_exc()))
        raise


def cmd_smoke(spec):
    """Run one unit spec into REVIEW_OUT without a frozen plan (pre-launch test only)."""
    require('REVIEW_OUT' in os.environ, 'smoke runs need a separate REVIEW_OUT')
    unit = json.loads(spec)
    p = reference_path(unit['dataset'], unit['scenario'], unit['method'], unit['seed'])
    unit.update(id='smoke_' + unit['kind'] + '_' + unit.get('variant', ''), reference=str(p.relative_to(CANON)),
                reference_sha256=sha(p))
    plan = dict(source_files=source_hashes(), runner_sha256=sha(__file__), units=[unit])
    dest = OUT / 'units' / unit['id']
    dest.mkdir(parents=True, exist_ok=False)
    setup(plan, need_reference_library=unit['kind'] == 'flame_fidelity')
    raw = json.loads(p.read_text())
    runner = {'capture': run_capture, 'flame_fidelity': run_flame_fidelity,
              'flame_nonoise': run_control, 'random': run_control}[unit['kind']]
    started = time.time()
    summary = runner(unit, raw, dest)
    write(dest / 'done.json', dict(unit=unit, seconds=time.time() - started, **summary))
    print(json.dumps(dict(unit=unit['id'], seconds=round(time.time() - started, 1),
                          **{k: v for k, v in summary.items() if k != 'artifacts'})))


def cmd_run(parallel):
    plan = load_plan()
    (OUT / 'logs').mkdir(exist_ok=True)
    pending = [u['id'] for u in plan['units'] if not (OUT / 'units' / u['id']).exists()]
    status = dict(started_unix=time.time(), total=len(plan['units']), launched={}, finished={})
    running = {}
    env = {**os.environ, 'PYTHONUNBUFFERED': '1'}
    while pending or running:
        while pending and len(running) < parallel:
            uid = pending.pop(0)
            log = open(OUT / 'logs' / f'{uid}.log', 'w')
            proc = subprocess.Popen([sys.executable, __file__, 'worker', '--unit', uid],
                                    stdout=log, stderr=subprocess.STDOUT, env=env)
            running[uid] = (proc, log, time.time())
            status['launched'][uid] = time.time()
        for uid, (proc, log, t0) in list(running.items()):
            code = proc.poll()
            if code is not None:
                log.close()
                status['finished'][uid] = dict(returncode=code, seconds=time.time() - t0)
                del running[uid]
        status.update(updated_unix=time.time(), running=sorted(running), pending=len(pending),
                      done=sum(1 for v in status['finished'].values() if v['returncode'] == 0),
                      failed=sorted(k for k, v in status['finished'].items() if v['returncode'] != 0))
        write(OUT / 'status.json', status)
        time.sleep(5)
    print(json.dumps(dict(done=status['done'], failed=status['failed'])))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('plan')
    r = sub.add_parser('run')
    r.add_argument('--parallel', type=int, default=6)
    w = sub.add_parser('worker')
    w.add_argument('--unit', required=True)
    s = sub.add_parser('smoke')
    s.add_argument('--spec', required=True)
    args = ap.parse_args()
    if args.cmd == 'smoke':
        cmd_smoke(args.spec)
    elif args.cmd == 'plan':
        cmd_plan()
    elif args.cmd == 'run':
        cmd_run(args.parallel)
    else:
        cmd_worker(args.unit)


if __name__ == '__main__':
    main()
