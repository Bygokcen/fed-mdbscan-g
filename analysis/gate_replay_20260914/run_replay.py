#!/usr/bin/env python3
"""Frozen-reference gate diagnostic; never trains or feeds back offline branches."""
import argparse, copy, hashlib, inspect, json, os, pathlib, shutil, signal, subprocess, sys, time, traceback

# Match the reference launch environment before importing numerical libraries.
for _thread_var in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_thread_var] = '1'

ROOT = pathlib.Path('/home/gokcen/Fed_MDBSCAN_TIFS')
STUDY = ROOT / 'new_work/results/cutoff_development/study_20260914_v1'
CHECKPOINTS = (0, 9, 29)
REPLACE = 'attack_gate = bool(density_gap_detected and l0_supports_attack)'
TIMES = {'time_elapsed', 'aggregation_time', 'root_training_time', 'server_total_time', 'round_total_time'}

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def plain(x):
    if isinstance(x, dict): return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [plain(v) for v in x]
    if hasattr(x, 'tolist'): return x.tolist()
    if isinstance(x, set): return sorted(x)
    return x

def write(path, value):
    path = pathlib.Path(path)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(plain(value), indent=2, allow_nan=False) + '\n')
    temp.replace(path)

def equality(a, b, label):
    if plain(a) != plain(b): raise RuntimeError('Reference mismatch: ' + label)

def setup(cuda=True):
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    sys.path.insert(0, str(STUDY / 'source/new_work'))
    import torch
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    if cuda and not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable')

def verify():
    validation_path = ROOT / 'analysis/cutoff_development_20260914/validation.json'
    v = json.loads(validation_path.read_text())
    from simulation.run_audit_campaign import load_manifest
    manifest = load_manifest(STUDY)
    equality(manifest['manifest_sha256'], v['manifest_sha256'], 'manifest canonical sha256')
    for rel, digest in manifest['snapshot_files'].items():
        equality(sha(STUDY / 'source' / rel), digest, 'source ' + rel)
    from simulation.run_audit_campaign import _environment_state
    equality(_environment_state(), manifest['environment'], 'environment')
    refs = []
    for rel, digest in v['raw_files_sha256'].items():
        p = pathlib.Path(rel)
        if (p.name.startswith('fed_mdbscan_g_seed') and p.parts[3] in ('scenario_cut_minmax', 'scenario_cut_backdoor')):
            equality(sha(STUDY / rel), digest, 'raw ' + rel)
            refs.append(dict(path=rel, sha256=digest))
    # Validate the previously failing Min-Max reference first; coverage is unchanged.
    refs.sort(key=lambda x: ('scenario_cut_minmax' not in x['path'], x['path']))
    equality(len(refs), 24, 'reference count')
    return refs, dict(manifest_sha256=v['manifest_sha256'], validation_sha256=sha(validation_path), snapshot_files=manifest['snapshot_files'])

def functions():
    import simulation.mdbscan as module
    fn = module.fed_mdbscan_g_filter
    source = inspect.getsource(fn)
    equality(source.count(REPLACE), 1, 'unique gate expression')
    namespace = dict(module.__dict__)
    exec(compile(source, '<baseline-copy>', 'exec'), namespace)
    baseline = namespace[fn.__name__]
    namespace2 = dict(module.__dict__)
    modified = source.replace(REPLACE, 'attack_gate = bool(density_gap_detected)')
    exec(compile(modified, '<density-only-copy>', 'exec'), namespace2)
    return fn, baseline, namespace2[fn.__name__], source, modified

def traced(fn, matrix, kwargs):
    captured = {}
    def trace(frame, event, arg):
        if frame.f_code is fn.__code__ and event == 'return':
            for key in ('low_indices', 'high_indices', 'natural_clusters', 'rejected_snnc_indices', 'l0_benign', 'l0_anomalies', 'rd_values', 't_est'):
                if key in frame.f_locals: captured[key] = plain(frame.f_locals[key])
        return trace
    old = sys.gettrace()
    sys.settrace(trace)
    try: result = fn(matrix.copy(), **copy.deepcopy(kwargs))
    finally: sys.settrace(old)
    captured['partition_executed'] = 'low_indices' in captured
    captured['partition_source'] = 'native_executed' if captured['partition_executed'] else 'unavailable'
    if 'low_indices' not in captured and 'rd_values' in captured and 't_est' in captured:
        captured['partition_source'] = 'derived_threshold_preview'
        captured['low_indices'] = [i for i, v in enumerate(captured['rd_values']) if v < captured['t_est']]
        captured['high_indices'] = [i for i, v in enumerate(captured['rd_values']) if v >= captured['t_est']]
    return result, captured

def self_test():
    setup(False)
    import numpy as np
    original, baseline, forced, source, modified = functions()
    rng = np.random.default_rng(912)
    matrix = np.concatenate([rng.normal(0, .01, (20, 5)), rng.normal(2, .01, (10, 5))])
    count = 0
    for density in (False, True):
        for momentum in (False, True):
            kwargs = dict(t=.5, min_attack_gate_l0_count=100, attack_history=[momentum], momentum_window=3, clean_round_streak=0)
            # Stub only the actual gap estimator in isolated function globals.
            estimator = '_auto_estimate_t'
            if estimator not in baseline.__globals__: raise RuntimeError('unknown gap estimator')
            for fn in (baseline, forced): fn.__globals__[estimator] = lambda *a, **k: (.5, density, 20. if density else 0.)
            kwargs['t'] = 'auto'
            a, _ = traced(baseline, matrix, kwargs)
            b, _ = traced(forced, matrix, kwargs)
            equality(a[2]['attack_gate'], False, 'baseline gate unsupported')
            equality(b[2]['attack_gate'], density, 'density-only gate')
            if not density: equality(a, b, 'closed gate / momentum parity')
            count += 1
    # Fresh unmodified namespaces, actual estimator and synthetic geometry.
    original, baseline, forced, _, _ = functions()
    for history in ([], [True]):
        for cutoff in (True, False):
            kwargs = dict(attack_history=history, enable_snnc_cutoff=cutoff)
            equality(original(matrix.copy(), **copy.deepcopy(kwargs)), baseline(matrix.copy(), **copy.deepcopy(kwargs)), 'compiled baseline')
            count += 1
    print(json.dumps(dict(passed=True, checks=count, source_sha256=hashlib.sha256(source.encode()).hexdigest())))

def worker(out, index):
    setup()
    import numpy as np
    from simulation.server import Server
    import simulation.server as server_module
    from simulation.run_experiment import run_single_experiment
    refs, provenance = verify()
    plan = json.loads((out / 'plan.json').read_text())
    equality(refs, plan['references'], 'frozen reference selection')
    equality(provenance, plan['provenance'], 'frozen provenance')
    equality(sha(__file__), plan['observer_sha256'], 'observer')
    ref = refs[index]
    raw = json.loads((STUDY / ref['path']).read_text())
    dest = out / f'ref_{index:02d}'
    dest.mkdir(exist_ok=False)
    original, baseline, forced, source, modified = functions()
    aggregate = Server.aggregate
    original_filter = server_module.fed_mdbscan_g_filter
    captures, current = {}, {}
    signature = inspect.signature(original_filter)
    def observer_filter(matrix, *args, **kwargs):
        r = current['round']
        if r in CHECKPOINTS:
            if r in captures: raise RuntimeError(f'duplicate checkpoint capture {r}')
            bound = signature.bind(matrix, *args, **kwargs)
            bound.apply_defaults()
            params = dict(bound.arguments)
            params.pop('gradients')
            equality(params['enable_snnc_cutoff'], True, 'reference cutoff enabled')
            captures[r] = dict(matrix=np.asarray(matrix).copy(), params=copy.deepcopy(params), participants=current['participants'], state=current['state'])
        result = original_filter(matrix, *args, **kwargs)
        if r in CHECKPOINTS: captures[r]['filter_result'] = copy.deepcopy(result)
        return result
    def observer_aggregate(self, gradients, *args, **kwargs):
        current.update(round=kwargs.get('round_id'), participants=list(kwargs.get('participating_ids', args[0] if args else [])), state=copy.deepcopy(self.export_defense_state()))
        return aggregate(self, gradients, *args, **kwargs)
    Server.aggregate, server_module.fed_mdbscan_g_filter = observer_aggregate, observer_filter
    try: metrics = run_single_experiment(raw['resolved_config'], 'fed_mdbscan_g', raw['seed'])
    finally: Server.aggregate, server_module.fed_mdbscan_g_filter = aggregate, original_filter
    write(dest / 'replay_unverified.json', dict(records=metrics.records, run_metadata=metrics.run_metadata))
    equality(len(raw['records']), 30, '30 expected rounds')
    equality(len(metrics.records), 30, '30 rounds')
    for i, (observed, expected) in enumerate(zip(metrics.records, raw['records'])):
        equality({k:v for k,v in observed.items() if k not in TIMES}, {k:v for k,v in expected.items() if k not in TIMES}, f'round {i} all non-timing metrics')
    volatile = {'command', 'start_time_unix', 'end_time_unix', 'peak_memory_kib', 'exit_status'}
    equality({k:v for k,v in metrics.run_metadata.items() if k not in volatile}, {k:v for k,v in raw['run_metadata'].items() if k not in volatile}, 'run metadata')
    equality(sorted(captures), list(CHECKPOINTS), 'checkpoints')
    # Only after the complete trajectory and metadata have matched may branches be evaluated.
    branches, artifacts = [], {}
    for r in CHECKPOINTS:
        cap = captures[r]
        matrix = cap.pop('matrix')
        np.save(dest / f'round_{r:02d}_updates.npy', matrix)
        artifacts[f'round_{r:02d}_updates.npy'] = sha(dest / f'round_{r:02d}_updates.npy')
        write(dest / f'round_{r:02d}_state.json', cap)
        artifacts[f'round_{r:02d}_state.json'] = sha(dest / f'round_{r:02d}_state.json')
        participants = cap['participants']
        row = raw['records'][r]
        malicious = set(row['actual_malicious_ids'])
        for mode, fn in (('original', baseline), ('density_only', forced)):
            for cutoff in (True, False):
                kwargs = {**cap['params'], 'enable_snnc_cutoff': cutoff}
                result, local = traced(fn, matrix, kwargs)
                accepted, rejected, info = result
                n = len(participants)
                equality(len(set(accepted)), len(accepted), 'unique accepted indices')
                equality(len(set(rejected)), len(rejected), 'unique rejected indices')
                equality(set(accepted) & set(rejected), set(), 'disjoint indices')
                equality(set(accepted) | set(rejected), set(range(n)), 'indices cover participants')
                ids = [participants[i] for i in accepted]
                if mode == 'original' and cutoff:
                    equality(result, cap['filter_result'], f'round {r} entire filter output')
                    equality(ids, row['accepted_ids'], f'round {r} baseline IDs')
                    equality([participants[i] for i in rejected], row['rejected_ids'], f'round {r} baseline rejected IDs')
                reject_ids = {participants[i] for i in rejected}
                honest = set(participants) - malicious
                attackers = set(participants) & malicious
                branches.append(dict(round=r, gate=mode, effective_gate_reason=('density_gap_only' if mode == 'density_only' and info['attack_gate'] else info['gate_reason']), cutoff=cutoff, accepted_ids=ids, rejected_ids=sorted(reject_ids), info=info, geometry=local, participant_ids=participants, actual_malicious_ids=sorted(attackers), fp=len(reject_ids & honest), tp=len(reject_ids & attackers), honest_count=len(honest), malicious_count=len(attackers)))
    equality(len(branches), 12, 'branch count')
    write(dest / 'branches.json', branches)
    artifacts['branches.json'] = sha(dest / 'branches.json')
    write(dest / 'validation.json', dict(valid=True, reference=ref, matched_rounds=30, matrices=3, branches=12, artifacts=artifacts, observer_sha256=sha(__file__), baseline_function_sha256=hashlib.sha256(source.encode()).hexdigest(), forced_function_sha256=hashlib.sha256(modified.encode()).hexdigest(), provenance=provenance))

def controller(out):
    plan = json.loads((out / 'plan.json').read_text())
    equality(sha(__file__), plan['observer_sha256'], 'controller observer')
    completed = 0
    child = None
    def interrupted(signum, frame):
        raise RuntimeError(f'controller interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for index in range(len(plan['references'])):
            write(out / 'status.json', dict(state='running', completed_references=completed, expected_references=24, expected_matrices=72, expected_branches=288, current=index, updated=time.time(), pid=os.getpid()))
            with (out / f'ref_{index:02d}.log').open('xb') as log:
                child = subprocess.Popen([sys.executable, '-u', __file__, '--worker', str(index), '--out', str(out)], stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
                while child.poll() is None:
                    write(out / 'status.json', dict(state='running', completed_references=completed, expected_references=24, expected_matrices=72, expected_branches=288, current=index, updated=time.time(), pid=os.getpid(), child_pid=child.pid))
                    time.sleep(5)
                code = child.returncode
            if code: raise RuntimeError(f'reference {index} worker exit {code}')
            validation = json.loads((out / f'ref_{index:02d}/validation.json').read_text())
            equality(validation['valid'], True, 'worker validation')
            equality(validation['reference'], plan['references'][index], 'worker reference identity')
            for key, value in [('matched_rounds',30), ('matrices',3), ('branches',12)]:
                equality(validation[key], value, 'worker count ' + key)
            for name, digest in validation['artifacts'].items():
                equality(sha(out / f'ref_{index:02d}' / name), digest, 'worker artifact ' + name)
            completed += 1
        write(out / 'status.json', dict(state='complete', completed_references=completed, matrices=completed*3, branches=completed*12, updated=time.time()))
    except BaseException as exc:
        if child is not None and child.poll() is None:
            child.terminate()
            try: child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        write(out / 'status.json', dict(state='failed', completed_references=completed, error=str(exc), traceback=traceback.format_exc(), updated=time.time()))
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--controller', action='store_true')
    parser.add_argument('--worker', type=int)
    parser.add_argument('--out', type=pathlib.Path)
    args = parser.parse_args()
    if args.self_test: return self_test()
    if args.out is None: parser.error('--out required')
    out = args.out.resolve()
    if args.launch:
        if out.exists(): raise FileExistsError('Refusing existing output: ' + str(out))
        setup()
        refs, provenance = verify()
        out.mkdir(parents=True, exist_ok=False)
        observer = out / 'observer.py'
        shutil.copyfile(__file__, observer)
        observer.chmod(0o444)
        write(out / 'plan.json', dict(references=refs, provenance=provenance, observer_sha256=sha(observer), checkpoints=CHECKPOINTS, expected_references=24, expected_matrices=72, expected_branches=288, created=time.time()))
        with (out / 'controller.log').open('xb') as log:
            process = subprocess.Popen([sys.executable, '-u', str(observer), '--controller', '--out', str(out)], stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        write(out / 'launch.json', dict(pid=process.pid, out=str(out), observer_sha256=sha(observer)))
        print(json.dumps(dict(pid=process.pid, out=str(out))))
    elif args.controller: controller(out)
    elif args.worker is not None: worker(out, args.worker)
    else: parser.error('choose --launch, --worker, --controller or --self-test')

if __name__ == '__main__': main()
