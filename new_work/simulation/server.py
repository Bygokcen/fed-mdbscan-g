"""
Federated learning aggregation server.

The central server that:
    1. Distributes the global model to clients
    2. Collects gradient updates from clients
    3. Filters anomalies using the selected aggregation method
    4. Aggregates clean gradients (FedAvg) to update global model
    5. Evaluates the global model on the test set
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import time

from simulation.models import get_model_weights, set_model_weights
from simulation.mdbscan import fed_mdbscan_g_filter
from simulation.contracts import (
    MDBSCAN_FAMILY_METHODS, aggregate_accepted_updates, validate_update_batch,
)
from simulation.baselines import (
    fed_dbscan, fed_rra, fed_g2l, krum, coord_median, fltrust, flame, flame_hdbscan,
)


class Server:
    """
    Central aggregation server for federated learning.

    Args:
        model: global PyTorch model
        test_loader: DataLoader for test/evaluation data
        device: torch device
        aggregation_method: one of 'fed_mdbscan_g', 'fed_dbscan', 'fed_rra', 'fed_g2l', 'fedavg'
        method_params: dict of parameters for the selected method
    """

    SUPPORTED_METHODS = ['fed_mdbscan_g', 'fed_dbscan', 'fed_rra', 'fed_g2l',
                         'fedavg', 'krum', 'coord_median', 'fltrust', 'flame',
                         # Layer-ablation variants and the matched-radius
                         # FedG2L control; see contracts.MDBSCAN_ABLATION_VARIANTS.
                         *(m for m in MDBSCAN_FAMILY_METHODS
                           if m != 'fed_mdbscan_g'),
                         'fed_g2l_25', 'norm_clip', 'sample_weighted_mean', 'fltrust_normalized', 'flame_hdbscan', 'krum_bound30']

    def __init__(self, model, test_loader, device='cpu',
                 aggregation_method='fed_mdbscan_g', method_params=None,
                 root_loader=None, root_model_fn=None,
                 aggregation_operator='uniform_mean',
                 fallback_policy='accept_all_degraded'):
        if aggregation_method not in self.SUPPORTED_METHODS:
            raise ValueError(f"unsupported aggregation method: {aggregation_method}")
        self.model = model.to(device)
        self.test_loader = test_loader
        self.device = device
        self.aggregation_method = aggregation_method
        self.method_params = method_params or {}
        if aggregation_operator not in {'uniform_mean', 'sample_weighted_mean'}:
            raise ValueError(f"unsupported aggregation operator: {aggregation_operator}")
        if fallback_policy not in {'accept_all_degraded', 'skip_round'}:
            raise ValueError(f"unsupported fallback policy: {fallback_policy}")
        self.aggregation_operator = ("sample_weighted_mean" if aggregation_method == "sample_weighted_mean" else aggregation_operator)
        self.noise_rng = np.random.default_rng(0)
        self.fallback_policy = fallback_policy
        self.criterion = nn.CrossEntropyLoss()

        # FLTrust root dataset (clean held-out subset; only used by 'fltrust')
        self.root_loader = root_loader
        if root_loader is not None and root_model_fn is not None:
            self.root_model = root_model_fn().to(device)
        else:
            self.root_model = None

        # Fed-MDBSCAN-G bookkeeping
        self.detected_attack_history = []          # per-round bool list (gap_detected)
        self.clean_round_streak = 0                # consecutive clean-round counter
        self.attack_alert_log = []                 # per-round True/False alerts
        self.gap_concentration_log = []            # per-round gap_concentration (xAI)
        self.layer_used_log = []                   # per-round pipeline path
        self._seen_update_ids = set()
        self._last_round_id = None

        # Track global weights
        self.global_weights = get_model_weights(self.model)


    def get_global_weights(self):
        """Return current global model weights as numpy array."""
        return self.global_weights.copy()

    def export_defense_state(self):
        """Return a versioned checkpoint of decision-relevant temporal state."""
        return {
            'state_version': 'fed-mdbscan-g-defense-state-v1',
            'detected_attack_history': list(self.detected_attack_history),
            'clean_round_streak': int(self.clean_round_streak),
            'attack_alert_log': list(self.attack_alert_log),
            'gap_concentration_log': list(self.gap_concentration_log),
            'layer_used_log': list(self.layer_used_log),
            'seen_update_ids': sorted(
                self._seen_update_ids,
                key=lambda item: (type(item).__name__, repr(item)),
            ),
            'last_round_id': self._last_round_id,
        }

    def restore_defense_state(self, state):
        """Restore a checkpoint after validating every replay-sensitive field."""
        if not isinstance(state, dict):
            raise TypeError('defense state must be a dictionary')
        if state.get('state_version') != 'fed-mdbscan-g-defense-state-v1':
            raise ValueError('unsupported defense state version')
        bool_lists = ('detected_attack_history', 'attack_alert_log')
        for name in bool_lists:
            value = state.get(name)
            if not isinstance(value, list) or any(not isinstance(item, bool) for item in value):
                raise ValueError(f'{name} must be a list of booleans')
        gaps = state.get('gap_concentration_log')
        if (not isinstance(gaps, list)
                or any(isinstance(item, bool)
                       or not isinstance(item, (int, float, np.number))
                       or not np.isfinite(item) for item in gaps)):
            raise ValueError('gap_concentration_log must contain finite numbers')
        layers = state.get('layer_used_log')
        if not isinstance(layers, list) or any(not isinstance(item, str) for item in layers):
            raise ValueError('layer_used_log must contain strings')
        if len({
            len(state['detected_attack_history']), len(state['attack_alert_log']),
            len(gaps), len(layers),
        }) != 1:
            raise ValueError('defense state logs must have identical lengths')
        streak = state.get('clean_round_streak')
        if isinstance(streak, bool) or not isinstance(streak, int) or streak < 0:
            raise ValueError('clean_round_streak must be a non-negative integer')
        last_round = state.get('last_round_id')
        if (last_round is not None and (
                isinstance(last_round, bool) or not isinstance(last_round, int)
                or last_round < 0)):
            raise ValueError('last_round_id must be null or a non-negative integer')
        seen = state.get('seen_update_ids')
        if not isinstance(seen, list):
            raise ValueError('seen_update_ids must be a list')
        try:
            seen_set = set(seen)
        except TypeError as exc:
            raise ValueError('seen_update_ids must be hashable') from exc
        if len(seen_set) != len(seen):
            raise ValueError('seen_update_ids must be unique')

        self.detected_attack_history = list(state['detected_attack_history'])
        self.clean_round_streak = streak
        self.attack_alert_log = list(state['attack_alert_log'])
        self.gap_concentration_log = [float(item) for item in gaps]
        self.layer_used_log = list(layers)
        self._seen_update_ids = seen_set
        self._last_round_id = last_round

    def _train_root_gradient(self, lr=0.01, epochs=1, momentum=0.9):
        """FLTrust: train the root model one step from current global weights;
        return the resulting weight delta (the 'root gradient'). Returns None
        if no root_model/root_loader is configured."""
        if self.root_model is None or self.root_loader is None:
            return None
        set_model_weights(self.root_model, self.global_weights)
        optimizer = optim.SGD(
            self.root_model.parameters(), lr=lr, momentum=momentum,
        )
        self.root_model.train()
        for _ in range(epochs):
            for batch_data, batch_labels in self.root_loader:
                batch_data = batch_data.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.root_model(batch_data)
                loss = self.criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
        local_weights = get_model_weights(self.root_model)
        return local_weights - self.global_weights

    def aggregate(self, client_gradients, participating_ids, sample_counts=None,
                  update_ids=None, round_id=None):
        """
        Perform one round of aggregation:
            1. Filter gradients using the selected method
            2. Average the clean gradients
            3. Update global model

        Args:
            client_gradients: list of numpy arrays (gradient updates from clients)
            participating_ids: unique server-visible client identifiers
            sample_counts: required only for the sample-weighted ablation
            update_ids: optional unique update identities used for replay checks
            round_id: monotonically increasing round identity used for stale checks

        Returns:
            result: dict with aggregation info
                - 'benign_indices': clients used for aggregation
                - 'anomaly_indices': clients filtered out
                - 'filter_time': time taken for filtering
                - 'decision': immutable accepted/rejected participant IDs for evaluation
        """
        server_start = time.perf_counter()
        root_training_time = 0.0
        if round_id is not None:
            if isinstance(round_id, bool) or not isinstance(round_id, int) or round_id < 0:
                raise ValueError("round_id must be a non-negative integer")
            if self._last_round_id is not None and round_id <= self._last_round_id:
                raise ValueError("stale or replayed round_id")
        if update_ids is None and round_id is not None:
            update_ids = [f"{round_id}:{participant_id}" for participant_id in participating_ids]
        gradients, participating_ids, update_ids = validate_update_batch(
            client_gradients, participating_ids, update_ids=update_ids
        )
        supplied_update_ids = {item for item in update_ids if item is not None}
        if supplied_update_ids & self._seen_update_ids:
            raise ValueError("replayed update_id")
        if self.aggregation_operator == 'sample_weighted_mean':
            if sample_counts is None or len(sample_counts) != len(gradients):
                raise ValueError("sample_weighted_mean requires one sample count per update")
        n_clients = len(gradients)

        # Per-client update magnitude, recorded for every aggregation method so
        # that rejection decisions can be related to update geometry across
        # methods. Purely observational: it is not read by any filter, does not
        # enter aggregation, and leaves every decision unchanged. Updates are
        # already validated as finite, but a finite update can still have a
        # norm too large to represent; such a norm is recorded as null rather
        # than raising or emitting a numerical warning from a diagnostic path.
        with np.errstate(over='ignore', invalid='ignore'):
            update_norms = np.linalg.norm(gradients, axis=1)

        # Measure filtering time
        start_time = time.time()

        pending_temporal = None

        # Apply filtering method
        if self.aggregation_method in ('fedavg', 'sample_weighted_mean', 'norm_clip'):
            benign_indices = list(range(n_clients))
            anomaly_indices = []
            filter_info = {'method': self.aggregation_method}
            if self.aggregation_method == 'norm_clip':
                filter_info.update({'aggregation_op': 'norm_clip',
                    'clip_norm': float(np.median(np.linalg.norm(gradients, axis=1))) * self.method_params.get('threshold_factor', 2.5)})
        elif self.aggregation_method in MDBSCAN_FAMILY_METHODS:
            benign_indices, anomaly_indices, filter_info = fed_mdbscan_g_filter(
                gradients,
                k=self.method_params.get('k', 5),
                t=self.method_params.get('t', 'auto'),
                eps=self.method_params.get('eps', 'auto'),
                min_pts=self.method_params.get('min_pts', 3),
                consensus_threshold=self.method_params.get('consensus_threshold', 2.0),
                trust_region_factor=self.method_params.get('trust_region_factor', 2.5),
                gap_concentration_threshold=self.method_params.get(
                    'gap_concentration_threshold', 10.0),
                min_attack_gate_l0_ratio=self.method_params.get(
                    'min_attack_gate_l0_ratio', 0.05),
                min_attack_gate_l0_count=self.method_params.get(
                    'min_attack_gate_l0_count', 2),
                safety_valve_ratio=self.method_params.get('safety_valve_ratio', 0.5),
                momentum_window=self.method_params.get('momentum_window', 3),
                attack_history=self.detected_attack_history,
                clean_round_streak=self.clean_round_streak,
                enable_snnc_cutoff=self.method_params.get('enable_snnc_cutoff', True),
                enable_l2=self.method_params.get('enable_l2', True),
                enable_momentum=self.method_params.get('enable_momentum', True),
                enable_safety_valve=self.method_params.get(
                    'enable_safety_valve', True),
            )

            attack_gate = bool(filter_info.get('attack_gate', False))
            pending_temporal = {
                'attack_gate': attack_gate,
                'attack_alert': bool(filter_info.get('attack_alert', False)),
                'gap_concentration': float(filter_info.get('gap_concentration', 0.0)),
                'layer_used': filter_info.get('layer_used', 'unknown'),
            }


        elif self.aggregation_method == 'fed_dbscan':
            benign_indices, anomaly_indices, filter_info = fed_dbscan(
                gradients,
                eps=self.method_params.get('eps', 0.5),
                min_pts=self.method_params.get('min_pts', 3),
            )
        elif self.aggregation_method == 'fed_rra':
            benign_indices, anomaly_indices, filter_info = fed_rra(
                gradients,
                eps=self.method_params.get('eps', 0.5),
                min_pts=self.method_params.get('min_pts', 3),
                reputation_threshold=self.method_params.get('reputation_threshold', 0.5),
            )
        elif self.aggregation_method in ('fed_g2l', 'fed_g2l_25'):
            benign_indices, anomaly_indices, filter_info = fed_g2l(
                gradients,
                threshold_factor=self.method_params.get('threshold_factor', 1.5),
            )
        elif self.aggregation_method in ('krum', 'krum_bound30'):
            benign_indices, anomaly_indices, filter_info = krum(
                gradients,
                num_malicious=(int(np.ceil(n_clients * self.method_params.get('max_attack_ratio', 0.3)))
                               if self.aggregation_method == 'krum_bound30' else
                               self.method_params.get('num_malicious', None)),
                multi_krum_m=self.method_params.get('multi_krum_m', None),
            )
        elif self.aggregation_method == 'coord_median':
            benign_indices, anomaly_indices, filter_info = coord_median(gradients)
        elif self.aggregation_method in ('fltrust', 'fltrust_normalized'):
            root_started = time.perf_counter()
            root_grad = self._train_root_gradient(
                lr=self.method_params.get('root_lr', 0.01),
                epochs=self.method_params.get('root_epochs', 1),
                momentum=self.method_params.get('root_momentum', 0.9),
            )
            root_training_time = time.perf_counter() - root_started
            if root_grad is None:
                benign_indices = list(range(n_clients))
                anomaly_indices = []
                filter_info = {
                    'method': 'fltrust',
                    'fallback_applied': True,
                    'fallback_reason': 'fltrust_no_root_model',
                    'degraded': True,
                }
            else:
                benign_indices, anomaly_indices, filter_info = fltrust(
                    gradients, root_grad,
                    clip_to_root_norm=self.method_params.get('clip_to_root_norm', True),
                )
        elif self.aggregation_method == 'flame_hdbscan':
            benign_indices, anomaly_indices, filter_info = flame_hdbscan(
                gradients, self.global_weights,
                noise_std=self.method_params.get('noise_std', 0.001))
        elif self.aggregation_method == 'flame':
            benign_indices, anomaly_indices, filter_info = flame(
                gradients,
                noise_std=self.method_params.get('noise_std', 0.001),
                eps_dbscan=self.method_params.get('eps_dbscan', 'auto'),
            )
        else:
            raise ValueError(f"Unknown method: {self.aggregation_method}")

        filter_time = max(0.0, time.time() - start_time - root_training_time)
        aggregation_started = time.perf_counter()

        def _validated_filter_indices(name, values):
            if not isinstance(values, (list, tuple, np.ndarray)):
                raise ValueError(f'{name} must be an index sequence')
            original = list(values)
            if any(isinstance(item, (bool, np.bool_))
                   or not isinstance(item, (int, np.integer)) for item in original):
                raise ValueError(f'{name} must contain only integer indices')
            converted = [int(item) for item in original]
            if len(set(converted)) != len(converted):
                raise ValueError(f'{name} must not contain duplicate indices')
            if any(item < 0 or item >= n_clients for item in converted):
                raise ValueError(f'{name} contains an out-of-range index')
            return sorted(converted)

        benign_indices = _validated_filter_indices('benign_indices', benign_indices)
        anomaly_indices = _validated_filter_indices('anomaly_indices', anomaly_indices)
        valid_positions = set(range(n_clients))
        if (set(benign_indices) & set(anomaly_indices)
                or set(benign_indices) | set(anomaly_indices) != valid_positions):
            raise ValueError("filter decision must partition every valid update exactly once")
        filter_info = dict(filter_info)
        if filter_info.get('fallback_applied') and self.fallback_policy == 'skip_round':
            benign_indices = []
            anomaly_indices = list(range(n_clients))
            filter_info.update({
                'fallback_applied': True,
                'fallback_reason': filter_info.get('fallback_reason', 'method_fallback'),
                'degraded': True,
                'fallback_policy': self.fallback_policy,
            })
        elif not benign_indices:
            filter_info.update({
                'fallback_applied': True,
                'fallback_reason': 'no_accepted_updates',
                'degraded': True,
                'fallback_policy': self.fallback_policy,
            })
            if self.fallback_policy == 'accept_all_degraded':
                benign_indices = list(range(n_clients))
                anomaly_indices = []
            else:
                anomaly_indices = list(range(n_clients))
        else:
            filter_info.setdefault('fallback_applied', False)
            filter_info.setdefault('fallback_reason', 'none')
            filter_info.setdefault('degraded', False)
            filter_info.setdefault('fallback_policy', self.fallback_policy)

        # Aggregate clean gradients. Default = mean (FedAvg-style); methods that
        # are themselves robust aggregators (e.g. coord_median) signal an
        # alternate op via filter_info['aggregation_op'].
        effective_aggregation_operator = 'none'
        if len(benign_indices) > 0:
            clean_gradients = gradients[benign_indices]
            agg_op = filter_info.get('aggregation_op', 'mean')
            effective_aggregation_operator = (
                agg_op if agg_op != 'mean' else self.aggregation_operator
            )

            if agg_op == 'norm_clip':
                threshold = filter_info['clip_norm']
                norms = np.linalg.norm(clean_gradients, axis=1)
                factors = np.minimum(1.0, threshold / np.maximum(norms, 1e-30))
                avg_gradient = np.mean(clean_gradients * factors[:, None], axis=0)
            elif agg_op == 'median':
                avg_gradient = np.median(clean_gradients, axis=0)
            elif agg_op == 'fltrust':
                # Trust-weighted average with norm clipping to ||root||.
                trust = np.array(filter_info.get('trust_weights', []))
                root_norm = float(filter_info.get('root_norm', 1.0))
                weighted_sum = np.zeros_like(gradients[0], dtype=np.float64)
                total_w = 0.0
                for idx in benign_indices:
                    g = gradients[idx].astype(np.float64)
                    ng = float(np.linalg.norm(g))
                    if ng > 1e-10 and (ng > root_norm or self.aggregation_method == 'fltrust_normalized'):
                        g = g * (root_norm / ng)
                    w = float(trust[idx]) if idx < len(trust) else 0.0
                    weighted_sum += w * g
                    total_w += w
                if total_w > 1e-10:
                    avg_gradient = (weighted_sum / total_w).astype(gradients.dtype)
                else:
                    avg_gradient = np.mean(clean_gradients, axis=0)
            elif agg_op == 'flame':
                # Norm-clip survivors to median norm, mean, then small DP noise.
                median_norm = float(filter_info.get('median_norm', 0.0))
                noise_std = float(filter_info.get('noise_std', 0.0))
                clipped = []
                for idx in benign_indices:
                    g = gradients[idx].astype(np.float64)
                    ng = float(np.linalg.norm(g))
                    if ng > median_norm and ng > 1e-10:
                        g = g * (median_norm / ng)
                    clipped.append(g)
                clipped_arr = np.asarray(clipped)
                avg_gradient = np.mean(clipped_arr, axis=0)
                if noise_std > 0 and median_norm > 0:
                    avg_gradient = avg_gradient + self.noise_rng.normal(
                        0.0, noise_std * median_norm, size=avg_gradient.shape,
                    )
                avg_gradient = avg_gradient.astype(gradients.dtype)
            else:
                avg_gradient = aggregate_accepted_updates(
                    gradients,
                    benign_indices,
                    operator=self.aggregation_operator,
                    sample_counts=sample_counts,
                )

            if not np.all(np.isfinite(avg_gradient)):
                raise ValueError('aggregation produced a non-finite update')
            candidate_weights = self.global_weights + avg_gradient
            if not np.all(np.isfinite(candidate_weights)):
                raise ValueError('global model update produced non-finite weights')
            set_model_weights(self.model, candidate_weights)
            self.global_weights = candidate_weights

        if pending_temporal is not None:
            self.detected_attack_history.append(pending_temporal['attack_gate'])
            self.attack_alert_log.append(pending_temporal['attack_alert'])
            self.gap_concentration_log.append(pending_temporal['gap_concentration'])
            self.layer_used_log.append(pending_temporal['layer_used'])
            if pending_temporal['attack_gate']:
                self.clean_round_streak = 0
            else:
                self.clean_round_streak += 1

        self._seen_update_ids.update(supplied_update_ids)
        if round_id is not None:
            self._last_round_id = round_id

        # Attack-alert signal is part of the defense decision.  Ground-truth
        # alert quality is computed later by the evaluator.
        attack_alert = bool(filter_info.get('attack_alert', False))
        density_gap_detected = bool(filter_info.get('density_gap_detected', False))
        attack_gate = bool(filter_info.get('attack_gate', False))
        gap_concentration = float(filter_info.get('gap_concentration', 0.0))
        layer_used = filter_info.get('layer_used', 'n/a')
        accepted_ids = [participating_ids[i] for i in benign_indices]
        rejected_ids = [participating_ids[i] for i in anomaly_indices]

        # Diagnostic geometry keyed by participant id. `l0_distances` exists
        # only for the MDBSCAN family, which computes it for its own trust
        # region; other methods report update norms alone.
        update_norms_by_id = {
            str(participant_id): (float(norm) if np.isfinite(norm) else None)
            for participant_id, norm in zip(participating_ids, update_norms)
        }
        raw_l0_distances = filter_info.get('l0_distances')
        if raw_l0_distances is not None and len(raw_l0_distances) == len(participating_ids):
            l0_distances_by_id = {
                str(participant_id): float(distance)
                for participant_id, distance in zip(participating_ids, raw_l0_distances)
            }
        else:
            l0_distances_by_id = {}

        result = {
            'benign_indices': benign_indices,
            'anomaly_indices': anomaly_indices,
            'filter_time': filter_time,
            'aggregation_time': time.perf_counter() - aggregation_started,
            'root_training_time': root_training_time,
            'server_total_time': time.perf_counter() - server_start,
            'decision': {
                'accepted_ids': accepted_ids,
                'rejected_ids': rejected_ids,
                'round_id': round_id,
                'update_ids': list(update_ids),
                'aggregation_operator': effective_aggregation_operator,
                'fallback_policy': self.fallback_policy,
            },
            'filter_info': filter_info,
            'n_benign': len(benign_indices),
            'n_anomaly': len(anomaly_indices),
            'update_norms': update_norms_by_id,
            'l0_distances': l0_distances_by_id,
            # xAI attack-alert reporting
            'attack_alert': attack_alert,
            'density_gap_detected': density_gap_detected,
            'attack_gate': attack_gate,
            'gap_concentration': gap_concentration,
            'layer_used': layer_used,
            'gate_reason': filter_info.get('gate_reason', 'n/a'),
            'l0_rejected_count': int(filter_info.get('l0_rejected_count', 0)),
            'l2_rejected_count': int(filter_info.get('l2_rejected_count', 0)),
            'low_density_count': int(filter_info.get('low_density_count', 0)),
            'natural_clusters_count': int(filter_info.get('natural_clusters_count', 0)),
            'rejected_snnc_clusters': int(filter_info.get('rejected_snnc_clusters', 0)),
        }

        return result


    def evaluate(self):
        """
        Evaluate the global model on the test dataset.

        Returns:
            accuracy: float between 0 and 1
        """
        self.model.eval()
        correct = 0
        total = 0
        class_correct = {}
        class_support = {}

        with torch.no_grad():
            for data, labels in self.test_loader:
                data = data.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(data)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                for label in labels.unique().tolist():
                    mask = labels == label
                    key = str(int(label))
                    class_support[key] = class_support.get(key, 0) + int(mask.sum())
                    class_correct[key] = class_correct.get(key, 0) + int(((predicted == labels) & mask).sum())

        accuracy = correct / total if total > 0 else 0.0
        per_class = {key: class_correct[key] / count for key, count in class_support.items()}
        self.last_class_metrics = {'per_class_accuracy': per_class,
                                  'class_support': class_support,
                                  'balanced_accuracy': float(np.mean(list(per_class.values()))) if per_class else 0.0}
        return accuracy
