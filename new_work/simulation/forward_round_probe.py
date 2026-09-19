"""Forward-round branch probe: A/B/C arms replayed from shared reference checkpoints.

The single-round pilot (``batch_control_probe``) compares batching regimes at the
initial model only. At that point every client is at the same, untrained state, so
a null result there does not say whether the regime matters once the model has
started to learn. This probe answers the forward-round version of the question.

Two modes:

``reference``
    Run one ordinary trajectory for ``--rounds`` rounds with the standard data
    loader -- this is arm A -- and capture, at each requested checkpoint round and
    before that round is aggregated: the global weights the round starts from, the
    defense's temporal state, and the participating client ids.

``branch``
    Run exactly one round from a captured checkpoint under arm A, B or C. Every
    arm at a given checkpoint starts from the same weights, the same participants
    and the same defense memory, so a difference between arms is attributable to
    the batching regime rather than to the learning stage.

Branch results are never fed back: the reference trajectory is finished and
written before any branch starts, and branches only ever read its checkpoints.

Seed handling. A branch runs as round 0 of a one-round experiment, but the four
round-dependent seed purposes are remapped to the checkpoint's round index, so
arm A of a branch reproduces the corresponding reference round exactly. That
equality is checked by the supervisor and is the probe's main integrity control.

Replay counters (``last_round_id``, ``seen_update_ids``) are cleared when the
defense state is restored, because a branch is a fresh single-round process. The
decision-relevant memory -- gate history, alert log and the clean-round streak --
is preserved.

This is an exploratory mechanism diagnostic. It produces no canonical unit, no
security claim and no independent validation result.
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import time

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')

import numpy as np

# Same sampling and hashing the single-round pilot used, imported rather than
# restated so the two experiments cannot drift apart.
from simulation.batch_control_probe import selected_batches, digest

ROUND_SEED_PURPOSES = ('attack', 'client_training', 'server_noise', 'root_training')
STATE_VERSION = 'fed-mdbscan-g-forward-round-v1'


def _configure_backend():
    import torch
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    return dict(deterministic=True, cudnn_deterministic=True, cudnn_benchmark=False,
                cublas=os.environ['CUBLAS_WORKSPACE_CONFIG'])


def _probe_identity():
    return {
        'forward_probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'state_version': STATE_VERSION,
    }


# ----------------------------------------------------------------------
# reference mode
# ----------------------------------------------------------------------
def run_reference(config, checkpoint_rounds, out_dir):
    """Run the reference trajectory and capture the requested round states."""
    from simulation.server import Server
    from simulation.run_experiment import run_single_experiment

    wanted = sorted(set(checkpoint_rounds))
    if any(r < 0 or r >= config['num_rounds'] for r in wanted):
        raise ValueError('checkpoint rounds must lie inside the reference horizon')

    captured = {}
    original_aggregate = Server.aggregate

    def aggregate(self, gradients, *args, **kwargs):
        round_id = kwargs.get('round_id')
        if round_id in wanted:
            if round_id in captured:
                raise RuntimeError(f'round {round_id} captured twice')
            participants = list(kwargs.get('participating_ids', args[0] if args else []))
            # Taken before the call, so this is the state the round starts from.
            captured[round_id] = dict(
                round=round_id,
                participants=participants,
                weights=self.global_weights.copy(),
                defense_state=self.export_defense_state(),
            )
        return original_aggregate(self, gradients, *args, **kwargs)

    Server.aggregate = aggregate
    try:
        metrics = run_single_experiment(config, 'fed_mdbscan_g', config['seed'])
    finally:
        Server.aggregate = original_aggregate

    missing = [r for r in wanted if r not in captured]
    if missing:
        raise RuntimeError(f'reference finished without capturing rounds {missing}')

    ckpt_dir = out_dir / 'checkpoints'
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for round_id in wanted:
        item = captured[round_id]
        weights = np.ascontiguousarray(item['weights'])
        weights_path = ckpt_dir / f'round_{round_id:03d}_weights.npy'
        np.save(weights_path, weights)
        state = dict(item['defense_state'])
        # A branch is a fresh process: anti-replay bookkeeping does not carry
        # over, while the filter's decision memory does.
        state['last_round_id'] = None
        state['seen_update_ids'] = []
        record = dict(
            round=round_id,
            participants=item['participants'],
            weights_file=weights_path.name,
            weights_sha256=digest(weights),
            defense_state=state,
            reference_defense_state=item['defense_state'],
            **_probe_identity(),
        )
        path = ckpt_dir / f'round_{round_id:03d}.json'
        path.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
        index.append(dict(round=round_id, checkpoint=path.name,
                          weights_sha256=record['weights_sha256'],
                          participants=len(item['participants'])))

    return metrics, index


# ----------------------------------------------------------------------
# branch mode
# ----------------------------------------------------------------------
def run_branch(config, checkpoint, arm, weights):
    """Run one round from ``checkpoint`` under ``arm`` and return the trace."""
    import torch
    import simulation.run_experiment as run_experiment_module
    from simulation.client import Client
    from simulation.server import Server
    from simulation.models import get_model_weights, set_model_weights
    from simulation.contracts import derive_seed
    from simulation.mdbscan import _weiszfeld_geometric_median, fed_mdbscan_g_filter
    from simulation.run_experiment import run_single_experiment

    steps = config['max_local_steps']
    checkpoint_round = checkpoint['round']
    participants = list(checkpoint['participants'])
    defense_state = checkpoint['defense_state']

    trace, vectors, ctx, shadow = {}, {}, {}, {}
    depth = 0

    original_train = Client.train
    original_step = torch.optim.SGD.step
    original_aggregate = Server.aggregate
    original_server_init = Server.__init__
    original_get_model = run_experiment_module.get_model
    original_schedule = run_experiment_module.build_participation_schedule
    original_derive = run_experiment_module.derive_seed

    class RecordingSampler:
        """Yields the arm's batches while recording exactly what was used."""

        def __init__(self, base, indices, cid):
            self.base, self.indices, self.cid = base, indices, cid

        def __len__(self):
            return len(self.base)

        def __iter__(self):
            for batch in self.base:
                ids = [int(self.indices[i]) for i in batch]
                item = dict(batch_size=len(ids), example_ids=ids,
                            batch_sha256=digest(np.array(ids, dtype=np.int64)))
                trace[self.cid].append(item)
                ctx['batch'] = item
                yield batch

    def get_model(*args, **kwargs):
        model = original_get_model(*args, **kwargs)
        set_model_weights(model, weights)
        return model

    def schedule(cfg, active_client_ids):
        latent, _ = original_schedule(cfg, active_client_ids)
        unknown = set(participants) - set(active_client_ids)
        if unknown:
            raise RuntimeError(f'checkpoint participants missing from cohort: {sorted(unknown)}')
        return latent, [list(participants)]

    def derive(seed, *parts):
        # Reproduce the reference round's streams: the branch runs as round 0.
        if len(parts) >= 2 and parts[0] in ROUND_SEED_PURPOSES and parts[1] == 0:
            parts = (parts[0], checkpoint_round) + tuple(parts[2:])
        return original_derive(seed, *parts)

    def server_init(self, *args, **kwargs):
        original_server_init(self, *args, **kwargs)
        self.restore_defense_state(defense_state)

    def train(self, global_weights, *args, **kwargs):
        nonlocal depth
        if depth:
            return original_train(self, global_weights, *args, **kwargs)
        cid = str(self.client_id)
        trace[cid], vectors[cid] = [], []
        ctx.update(client=self, weights=global_weights, cid=cid)
        loader = self.data_loader
        old_sampler = loader.batch_sampler
        indices = list(loader.dataset.indices)
        base = old_sampler if arm == 'A' else selected_batches(
            len(indices), derive_seed(config['seed'], 'batch_probe', self.client_id),
            arm, steps=steps)
        object.__setattr__(loader, 'batch_sampler', RecordingSampler(base, indices, cid))
        hook = self.criterion.register_forward_hook(
            lambda module, inputs, output: ctx['batch'].update(
                batch_loss=float(output.detach().item())))
        depth += 1
        try:
            return original_train(self, global_weights, *args, **kwargs)
        finally:
            depth -= 1
            hook.remove()
            object.__setattr__(loader, 'batch_sampler', old_sampler)

    def step(self, *args, **kwargs):
        result = original_step(self, *args, **kwargs)
        cid = ctx['cid']
        delta = get_model_weights(ctx['client'].model) - ctx['weights']
        if not np.isfinite(delta).all():
            raise RuntimeError(f'client {cid} produced a non-finite intermediate update')
        vectors[cid].append(delta.copy())
        ctx['batch']['delta_norm'] = float(np.linalg.norm(delta.astype(np.float64)))
        ctx['batch']['delta_sha256'] = digest(delta)
        ctx['batch']['unique_examples_so_far'] = len(
            {i for b in trace[cid] for i in b['example_ids']})
        return result

    def aggregate(self, gradients, *args, **kwargs):
        ids = list(kwargs.get('participating_ids', args[0] if args else []))
        if len(ids) != len(gradients):
            raise RuntimeError('participant and update counts disagree')
        params = dict(config['method_params']['fed_mdbscan_g'])
        params['enable_l2'] = False
        accepted, _, _ = fed_mdbscan_g_filter(np.asarray(gradients), **params)
        shadow['l0_accepted_ids'] = [ids[i] for i in accepted]
        shadow['uniform_accepted_ids'] = ids
        shadow['input_sha256'] = digest(np.asarray(gradients))
        result = original_aggregate(self, gradients, *args, **kwargs)
        shadow['full_accepted_ids'] = result['decision']['accepted_ids']
        return result

    Client.train = train
    torch.optim.SGD.step = step
    Server.aggregate = aggregate
    Server.__init__ = server_init
    run_experiment_module.get_model = get_model
    run_experiment_module.build_participation_schedule = schedule
    run_experiment_module.derive_seed = derive
    try:
        metrics = run_single_experiment(config, 'fed_mdbscan_g', config['seed'])
    finally:
        Client.train = original_train
        torch.optim.SGD.step = original_step
        Server.aggregate = original_aggregate
        Server.__init__ = original_server_init
        run_experiment_module.get_model = original_get_model
        run_experiment_module.build_participation_schedule = original_schedule
        run_experiment_module.derive_seed = original_derive

    if len(metrics.records) != 1:
        raise RuntimeError('a branch must produce exactly one round')
    ids = list(metrics.records[0]['server_input_ids'])
    if ids != participants:
        raise RuntimeError('branch cohort does not match the checkpoint')
    for cid in ids:
        if len(trace[str(cid)]) != steps or len(vectors[str(cid)]) != steps:
            raise RuntimeError(f'client {cid} did not take exactly {steps} steps')

    # Distance to the cohort's geometric median after each intermediate step.
    # The server is only really updated once, at the end of the round.
    for k in range(steps):
        matrix = np.stack([vectors[str(cid)][k] for cid in ids])
        center = _weiszfeld_geometric_median(matrix)
        for cid, distance in zip(ids, np.linalg.norm(matrix - center, axis=1)):
            trace[str(cid)][k]['cohort_geometric_median_distance'] = float(distance)

    return metrics, trace, shadow


# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['reference', 'branch'], required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--rounds', type=int, help='reference mode: trajectory length')
    parser.add_argument('--checkpoint-rounds', help='reference mode: comma separated')
    parser.add_argument('--checkpoint', help='branch mode: checkpoint json')
    parser.add_argument('--arm', choices=['A', 'B', 'C'], help='branch mode')
    args = parser.parse_args()

    out = Path(args.output)
    if out.exists():
        raise SystemExit(f'refusing to overwrite {out}')
    backend = _configure_backend()
    config = json.loads(Path(args.config).read_text())
    if config['malicious_ratio'] != 0:
        raise SystemExit('this probe only studies the attack-free mechanism')
    if config['max_local_steps'] is None:
        raise SystemExit('a fixed local step budget is required')

    result = dict(mode=args.mode, started=time.time(), backend=backend,
                  config=config, **_probe_identity())
    try:
        if args.mode == 'reference':
            config = dict(config, num_rounds=int(args.rounds))
            result['config'] = config
            rounds = [int(r) for r in args.checkpoint_rounds.split(',') if r != '']
            metrics, index = run_reference(config, rounds, out.parent)
            result.update(outcome='completed', arm='A', checkpoint_rounds=rounds,
                          checkpoint_index=index, records=metrics.records,
                          metadata=metrics.run_metadata)
        else:
            if config['num_rounds'] != 1:
                raise SystemExit('a branch config must declare exactly one round')
            checkpoint = json.loads(Path(args.checkpoint).read_text())
            weights = np.load(Path(args.checkpoint).parent / checkpoint['weights_file'])
            if digest(weights) != checkpoint['weights_sha256']:
                raise SystemExit('checkpoint weights do not match their recorded hash')
            metrics, trace, shadow = run_branch(config, checkpoint, args.arm, weights)
            result.update(outcome='completed', arm=args.arm,
                          checkpoint_round=checkpoint['round'],
                          checkpoint_weights_sha256=checkpoint['weights_sha256'],
                          records=metrics.records, metadata=metrics.run_metadata,
                          clients=trace, shadow=shadow)
    except BaseException as exc:
        result.update(outcome='failed', error=repr(exc))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, default=str) + '\n')
        raise
    result['ended'] = time.time()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
