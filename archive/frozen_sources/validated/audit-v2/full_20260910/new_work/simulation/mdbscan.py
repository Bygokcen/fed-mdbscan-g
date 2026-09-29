"""
Fed-MDBSCAN-G: Hybrid Multi-Density DBSCAN with Geometric Median Consensus
===========================================================================

An **explainable** density-based Byzantine-robust federated learning defense
that provides three simultaneous guarantees:

    (1) FILTERING     — Remove poisoning gradients before aggregation
    (2) DETECTION     — Report whether the current round is under attack
    (3) INTERPRETABILITY — Expose the bimodal rd gap as a forensic signal

Architecture
------------
    Layer 0: Geometric Trust-Region Pre-filter (FedG2L-style conservative filter)
    Layer 1: Bimodal Relative-Density Decomposition (→ attack_alert)
    Layer 2: MDBSCAN + SNNC + Geometric-Median Consensus Validation
    Layer 3: FPR Safety Valve (reject-to-Layer-0 if benign_ratio < 0.5)

Original MDBSCAN reference
--------------------------
    Qian, J., Zhou, Y., Han, X., & Wang, Y. (2024).
    MDBSCAN: A multi-density DBSCAN based on relative density.
    Neurocomputing, 576, 127329.

Our federated adaptation adds:
    * Bimodal Relative-Density Decomposition (auto-gap threshold)
    * Contamination-free eps estimation
    * Weiszfeld Geometric-Median Consensus (replaces coordinate-wise median)
    * Temporal Gap Momentum with clean-round decay
    * Hybrid Trust-Region fallback
    * Explicit attack-alert output for xAI integration
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN as SklearnDBSCAN


# =====================================================================
#  0. GEOMETRIC MEDIAN UTILITIES
# =====================================================================

def _weiszfeld_geometric_median(data, max_iter=100, tol=1e-5):
    """
    Compute the geometric median of a set of vectors using Weiszfeld's
    iterative algorithm.

    The geometric median minimizes the sum of Euclidean distances
    to the input points and is highly robust to outliers in
    high-dimensional gradient spaces (breakdown point 0.5).

    References:
        Weiszfeld, E. (1937). Sur le point pour lequel la somme des
        distances de n points donnés est minimum.
    """
    if data.shape[0] == 0:
        return np.zeros(data.shape[1]) if data.ndim > 1 else np.array([])
    if data.shape[0] == 1:
        return data[0].copy()

    median = np.mean(data, axis=0)
    for _ in range(max_iter):
        distances = np.linalg.norm(data - median, axis=1)
        distances = np.maximum(distances, 1e-10)
        weights = 1.0 / distances
        new_median = np.average(data, axis=0, weights=weights)
        if np.linalg.norm(new_median - median) < tol:
            break
        median = new_median
    return median


# =====================================================================
#  1. RELATIVE DENSITY (Qian et al. 2024, Eq. 1)
# =====================================================================

def compute_relative_density(data, k):
    """
    rd(i) = k / Σ_{j ∈ kNN(i)} dist(p_i, p_j)

    Reference: Equation (1) in Qian et al. (2024).
    """
    n_samples = data.shape[0]
    effective_k = min(k, n_samples - 1)
    if effective_k <= 0:
        return np.ones(n_samples)

    nn = NearestNeighbors(n_neighbors=effective_k + 1, metric='euclidean')
    nn.fit(data)
    distances, _ = nn.kneighbors(data)
    knn_distances = distances[:, 1:]
    distance_sums = np.sum(knn_distances, axis=1)

    rd_values = np.where(
        distance_sums > 0,
        effective_k / np.maximum(distance_sums, 1e-15),
        1.0
    )
    return rd_values


def extract_low_density(data, rd_values, t):
    """L = {p_i | rd(i) < t}.  Equation (2) in Qian et al. (2024)."""
    low_mask = rd_values < t
    high_mask = ~low_mask
    low_density_indices = np.where(low_mask)[0]
    high_density_indices = np.where(high_mask)[0]
    return (data[low_density_indices], low_density_indices,
            data[high_density_indices], high_density_indices)


# =====================================================================
#  2. SNNC (Qian et al. 2024, Algorithm 1)
# =====================================================================

def snnc(data, k, eps=None, original_indices=None):
    """Share Nearest Neighbors-based Clustering (Algorithm 1 in Qian et al.)."""
    n_points = data.shape[0]
    if original_indices is None:
        original_indices = np.arange(n_points)
    if n_points <= 1:
        return [], original_indices.tolist() if hasattr(original_indices, 'tolist') else list(original_indices)

    effective_k = min(k, n_points - 1)
    if effective_k <= 0:
        return [], list(original_indices)

    nn = NearestNeighbors(n_neighbors=effective_k + 1, metric='euclidean')
    nn.fit(data)
    distances, knn_indices = nn.kneighbors(data)

    knn_sets = []
    for i in range(n_points):
        valid_neighbors = set()
        for j_idx, dist in zip(knn_indices[i, 1:], distances[i, 1:]):
            if eps is None or dist <= eps * 3.0:
                valid_neighbors.add(int(j_idx))
        knn_sets.append(valid_neighbors)

    sn = {i: {i} for i in range(n_points)}
    for i in range(n_points):
        for j in range(i + 1, n_points):
            if len(knn_sets[i] & knn_sets[j]) >= 1:
                sn[i].add(j)

    for _ in range(100):
        merged = False
        keys = list(sn.keys())
        for i_idx in range(len(keys)):
            i = keys[i_idx]
            if i not in sn or len(sn[i]) == 0:
                continue
            for j_idx in range(i_idx + 1, len(keys)):
                j = keys[j_idx]
                if j not in sn or len(sn[j]) == 0:
                    continue
                if len(sn[i] & sn[j]) >= 1:
                    sn[i] = sn[i] | sn[j]
                    sn[j] = set()
                    merged = True
        if not merged:
            break

    non_empty_sn = {k: v for k, v in sn.items() if len(v) > 0}
    if len(non_empty_sn) == 0:
        return [], list(original_indices)

    set_sizes = [len(v) for v in non_empty_sn.values()]
    mean_size = np.mean(set_sizes)
    required_size = max(mean_size, 2)

    natural_clusters = []
    natural_cluster_point_indices = set()
    for _, point_set in non_empty_sn.items():
        if len(point_set) >= required_size:
            cluster_original_indices = [int(original_indices[p]) for p in point_set]
            natural_clusters.append(cluster_original_indices)
            natural_cluster_point_indices.update(point_set)

    remaining_local_indices = [
        i for i in range(n_points) if i not in natural_cluster_point_indices
    ]
    remaining_indices = [int(original_indices[i]) for i in remaining_local_indices]
    return natural_clusters, remaining_indices


# =====================================================================
#  3. ADAPTIVE PARAMETER ESTIMATORS (Fed-MDBSCAN-G contributions)
# =====================================================================

def _auto_estimate_eps(data, k, exclude_indices=None):
    """
    Contamination-free eps estimate.

    If attacker indices are known (exclude_indices), the 75th-percentile
    of the k-NN distance distribution is computed on benign-only data.
    """
    if exclude_indices is not None and len(exclude_indices) > 0:
        mask = np.ones(data.shape[0], dtype=bool)
        for idx in exclude_indices:
            mask[idx] = False
        estimation_data = data[mask]
    else:
        estimation_data = data

    n_samples = estimation_data.shape[0]
    effective_k = min(k, n_samples - 1)
    if effective_k <= 0:
        return 1.0

    nn = NearestNeighbors(n_neighbors=effective_k + 1, metric='euclidean')
    nn.fit(estimation_data)
    distances, _ = nn.kneighbors(estimation_data)
    k_distances = distances[:, -1]
    eps = np.percentile(k_distances, 75)
    return max(eps, 1e-10)


def _auto_estimate_t(rd_values, gap_concentration_threshold=10.0):
    """
    Bimodal Relative-Density Decomposition.

    Finds the natural gap between benign and malicious populations
    in the sorted rd distribution using a Jenks-style maximum-gap test.

    Returns:
        t               : threshold placed at the gap midpoint
        gap_detected    : bool, True if the gap is statistically significant
        gap_concentration : float (max_gap / median_gap) — xAI signal
    """
    sorted_rd = np.sort(rd_values)
    n = len(sorted_rd)
    if n < 3:
        return np.percentile(rd_values, 25), False, 0.0

    gaps = np.diff(sorted_rd)
    max_gap_idx = int(np.argmax(gaps))
    max_gap = gaps[max_gap_idx]
    median_gap = np.median(gaps)
    gap_concentration = float(max_gap / median_gap) if median_gap > 1e-15 else 0.0

    gap_is_significant = gap_concentration > gap_concentration_threshold

    if gap_is_significant:
        t = (sorted_rd[max_gap_idx] + sorted_rd[max_gap_idx + 1]) / 2.0
        return float(t), True, gap_concentration
    else:
        t = float(np.percentile(rd_values, 10))
        return t, False, gap_concentration


# =====================================================================
#  4. GEOMETRIC MEDIAN CONSENSUS (replaces coordinate-wise median)
# =====================================================================

def _geometric_consensus_validation(gradients, cluster_indices,
                                    benign_indices, threshold_factor=2.0):
    """
    Validate an SNNC natural cluster against the **geometric-median**
    consensus of the currently-trusted benign majority.

    Why geometric median?
        In high-dimensional gradient space, coordinate-wise median is a
        Cartesian-axis-biased estimator (it minimises the L1-marginal loss
        per dimension) and can drift when benign gradients have structured
        correlation across coordinates. The geometric (L1-Euclidean) median
        has the optimal breakdown point (0.5) and is rotation-invariant,
        which matches the geometry of gradient descent updates.

    Returns True if the SNNC cluster centroid lies within
    `threshold_factor × median_benign_distance` of the geometric median.
    """
    if len(benign_indices) == 0 or len(cluster_indices) == 0:
        return True

    benign_gradients = gradients[benign_indices]
    consensus = _weiszfeld_geometric_median(benign_gradients)

    benign_distances = np.linalg.norm(benign_gradients - consensus, axis=1)
    median_benign_dist = float(np.median(benign_distances))
    if median_benign_dist < 1e-10:
        median_benign_dist = 1e-10

    cluster_centroid = np.mean(gradients[cluster_indices], axis=0)
    cluster_distance = float(np.linalg.norm(cluster_centroid - consensus))
    return cluster_distance <= median_benign_dist * threshold_factor


# =====================================================================
#  5. LAYER 0: GEOMETRIC TRUST-REGION PRE-FILTER
# =====================================================================

def _geometric_trust_region_filter(gradients, threshold_factor=2.5):
    """
    Layer 0 — an FedG2L-inspired pre-filter that removes gross outliers
    before the MDBSCAN pipeline.

    Rationale:
        Even when the bimodal rd gap is not visible (extreme non-IID),
        a conservative geometric-median trust region safely excludes
        extreme poisoning vectors without hurting the benign minority.
        The threshold factor is deliberately loose (2.5×) so that
        legitimate sparse clients are retained.

    Returns:
        trusted_indices : list[int] — clients inside the trust region
        distances       : np.ndarray — L2 distance of each client to
                          the geometric median (useful for diagnostics)
    """
    n_clients = gradients.shape[0]
    if n_clients <= 2:
        return list(range(n_clients)), np.zeros(n_clients)

    geo_median = _weiszfeld_geometric_median(gradients)
    distances = np.linalg.norm(gradients - geo_median, axis=1)
    median_dist = float(np.median(distances))
    threshold = median_dist * threshold_factor

    # Safeguard: if thresholding would remove too many clients (> 50%),
    # keep everyone — the geometry is too noisy for this heuristic.
    trusted_mask = distances <= threshold
    if trusted_mask.sum() < n_clients * 0.5:
        trusted_mask = np.ones(n_clients, dtype=bool)

    trusted_indices = np.where(trusted_mask)[0].tolist()
    return trusted_indices, distances


# =====================================================================
#  6. MAIN ENTRY POINT — HYBRID Fed-MDBSCAN-G FILTER
# =====================================================================

def fed_mdbscan_g_filter(gradients,
                       k=5,
                       t='auto',
                       eps='auto',
                       min_pts=3,
                       consensus_threshold=2.0,
                       trust_region_factor=1.5,
                       gap_concentration_threshold=20.0,
                       min_attack_gate_l0_ratio=0.05,
                       min_attack_gate_l0_count=2,
                       attack_history=None,
                       clean_round_streak=0,
                       momentum_window=3,
                       safety_valve_ratio=0.5,
                       enable_l2=True,
                       enable_momentum=True,
                       enable_safety_valve=True):

    """
    Fed-MDBSCAN-G: Hybrid explainable density-based robust aggregator.

    Pipeline
    --------
        L0 — Geometric Trust-Region Pre-filter        (always active)
        L1 — Bimodal Relative-Density Decomposition   → density-gap diagnostic
        L2 — MDBSCAN + SNNC + Geometric Consensus     (only if attack gate opens)
        L3 — FPR Safety Valve                         (reject L2 if too aggressive)

    Parameters
    ----------
    gradients : np.ndarray, shape (n_clients, n_features)
    k : int
        Nearest-neighbour count for rd and SNNC.
    t, eps : 'auto' or float
        'auto' triggers Bimodal / contamination-free estimation.
    min_pts : int
        DBSCAN MinPts for Layer 2.
    consensus_threshold : float
        λ in the geometric consensus distance check.
    trust_region_factor : float
        Layer 0 distance multiplier (default 1.5).
    gap_concentration_threshold : float
        C in the Bimodal Gap Concentration test (default 20.0).
    min_attack_gate_l0_ratio, min_attack_gate_l0_count : float, int
        A density gap opens the attack gate only when Layer 0 also sees at
        least this much outlier evidence. This prevents natural non-IID
        density gaps from triggering L2 in clean heterogeneous rounds.
    attack_history : list[bool] or None
        Temporal Gap Momentum memory (last `momentum_window` rounds).
    clean_round_streak : int
        Number of **consecutive** recent clean rounds. Suppresses momentum
        after `momentum_window` clean rounds to prevent FPR inflation.
    momentum_window : int
        τ, the Temporal Gap Momentum window (default 3).
    safety_valve_ratio : float
        If the Layer-2 benign ratio drops below this fraction, fall back
        to Layer-0 output to avoid over-filtering (default 0.5).
    enable_l2, enable_momentum, enable_safety_valve : bool
        Layer-ablation switches. All default to True, which reproduces the
        published architecture exactly; they exist so that the contribution
        of each layer can be measured instead of argued.
        - enable_l2=False    : accept set is always B0 (Layer-0 only). The
          attack gate and alert are still computed and logged, so alert
          quality stays measurable independently of filtering.
        - enable_momentum=False : the gate must fire freshly each round;
          no temporal carry-over.
        - enable_safety_valve=False : the |B| < ratio*N fallback to B0 is
          not applied, exposing Layer-2's unguarded rejection behaviour.

    Returns
    -------
    benign_indices  : sorted list[int]
    anomaly_indices : sorted list[int]
    info : dict
        Includes `attack_alert` (bool), `gap_concentration` (float),
        and all intermediate layer outputs for reporting / xAI.
    """
    n_clients = gradients.shape[0]
    if n_clients <= 2:
        return (list(range(n_clients)), [],
                {'attack_alert': False,
                 'gap_concentration': 0.0,
                 'layer_used': 'trivial',
                 'fallback_applied': True,
                 'fallback_reason': 'cohort_below_minimum',
                 'degraded': True,
                 'n_clusters': 1})

    # -----------------------------------------------------------------
    # LAYER 0 — Geometric Trust-Region Pre-filter
    # -----------------------------------------------------------------
    l0_benign, l0_distances = _geometric_trust_region_filter(
        gradients, threshold_factor=trust_region_factor
    )
    l0_anomalies = sorted(set(range(n_clients)) - set(l0_benign))

    # -----------------------------------------------------------------
    # LAYER 1 — Bimodal Relative-Density Decomposition
    # -----------------------------------------------------------------
    rd_values = compute_relative_density(gradients, k)

    if t == 'auto':
        t_est, gap_detected, gap_conc = _auto_estimate_t(
            rd_values, gap_concentration_threshold
        )
    else:
        t_est, gap_detected, gap_conc = float(t), True, 0.0

    density_gap_detected = bool(gap_detected)

    # A raw rd gap is a distribution-shift diagnostic, not by itself an
    # attack claim. Require independent Layer-0 outlier support before the
    # attack gate can activate L2/SNNC.
    min_gate_count = max(
        int(min_attack_gate_l0_count),
        int(np.ceil(n_clients * float(min_attack_gate_l0_ratio))),
    )
    l0_supports_attack = len(l0_anomalies) >= min_gate_count
    attack_gate = bool(density_gap_detected and l0_supports_attack)
    if attack_gate:
        gate_reason = 'density_gap+l0_outlier_support'
    elif density_gap_detected:
        gate_reason = 'density_gap_without_l0_support'
    else:
        gate_reason = 'no_density_gap'

    if density_gap_detected:
        low_density_preview_count = int(np.sum(rd_values < t_est))
    else:
        low_density_preview_count = 0
    high_density_preview_count = n_clients - low_density_preview_count

    # Temporal Gap Momentum with clean-round decay. History stores attack
    # gates, not raw density gaps, so clean non-IID bimodality does not keep
    # the defense in attack mode indefinitely.
    #   - a recent gap in the history keeps us in "under attack" mode,
    #     but ONLY if we have not accumulated ≥ momentum_window
    #     consecutive clean rounds (clean_round_streak).
    momentum_active = False
    if enable_momentum and attack_history:
        recent = attack_history[-momentum_window:]
        momentum_active = any(recent)
    if clean_round_streak >= momentum_window:
        momentum_active = False  # decay — trust the signal again

    attack_alert = attack_gate or momentum_active
    if momentum_active and not attack_gate:
        gate_reason = 'temporal_momentum'

    # -----------------------------------------------------------------
    # If NO attack is detected → trust Layer 0 output only
    # -----------------------------------------------------------------
    if (not attack_alert) or (not enable_l2):
        info = {
            'attack_alert': bool(attack_alert),
            'density_gap_detected': density_gap_detected,
            'gap_detected': density_gap_detected,
            'attack_gate': bool(attack_gate),
            'gate_reason': gate_reason,
            'gap_concentration': gap_conc,
            'momentum_active': momentum_active,
            'attack_gate_min_count': int(min_gate_count),
            'attack_gate_l0_count': int(len(l0_anomalies)),
            'layer_used': 'L0_only',
            'fallback_applied': False,
            'fallback_reason': 'none',
            'degraded': False,
            'l0_rejected_count': len(l0_anomalies),
            'rd_values': rd_values.tolist(),
            'auto_t': float(t_est),
            'auto_eps': 0.0,
            'n_clusters': 1,
            'low_density_count': low_density_preview_count,
            'high_density_count': high_density_preview_count,
            'natural_clusters_count': 0,
            'rejected_snnc_clusters': 0,
            'l2_rejected_count': 0,
            'anomalies_detected': len(l0_anomalies),
        }
        return sorted(l0_benign), l0_anomalies, info

    # -----------------------------------------------------------------
    # LAYER 2 — MDBSCAN + SNNC + Geometric Consensus
    # (additive to Layer 0 — Layer 0 is ALWAYS the baseline filter)
    # -----------------------------------------------------------------
    low_data, low_indices, high_data, high_indices = extract_low_density(
        gradients, rd_values, t_est
    )

    # Contamination-free eps (estimated on the high-density side only
    # when the gap is significant — prevents attacker-scale contamination)
    if eps == 'auto':
        exclude = set(low_indices.tolist()) if gap_detected else None
        eps_est = _auto_estimate_eps(gradients, k, exclude_indices=exclude)
    else:
        eps_est = float(eps)

    # SNNC natural-cluster recovery in the low-density region.
    # In a poisoning context, these "natural clusters" are almost always
    # **attacker coalitions** that share a structured direction distinct
    # from the benign consensus.  We therefore validate each cluster
    # against the geometric median of the trusted (Layer-0-approved)
    # benign majority.  A cluster that fails the consensus check is
    # reported as an attacker-coalition rejection.
    natural_clusters = []
    if len(low_data) > 1:
        natural_clusters, _ = snnc(
            low_data, k, eps=eps_est, original_indices=low_indices
        )

    # The "trusted pool" for consensus validation is the Layer-0
    # accepted set (robust geometric-median trust region).
    rejected_snnc_indices = []
    rejected_snnc_cluster_count = 0
    for cluster in natural_clusters:
        is_legit = _geometric_consensus_validation(
            gradients, cluster, l0_benign,
            threshold_factor=consensus_threshold
        )
        if not is_legit:
            rejected_snnc_cluster_count += 1
            rejected_snnc_indices.extend(cluster)

    # -----------------------------------------------------------------
    # Combine:
    #   final_benign = Layer-0 benign
    #                  ∖ (additional SNNC attacker-coalition clients)
    # -----------------------------------------------------------------
    snnc_reject_set = set(rejected_snnc_indices)
    combined_benign = sorted(set(l0_benign) - snnc_reject_set)
    combined_anomalies = sorted(set(range(n_clients)) - set(combined_benign))
    layer_used = 'L0+L2_SNNC'
    l2_benign = combined_benign  # (for reporting compatibility)
    l2_anomalies = combined_anomalies

    # -----------------------------------------------------------------
    # LAYER 3 — FPR Safety Valve
    #   If the combined filter would keep fewer than `safety_valve_ratio`
    #   of the clients, revert to Layer 0 only (conservative fallback).
    # -----------------------------------------------------------------
    if enable_safety_valve and len(combined_benign) < n_clients * safety_valve_ratio:
        final_benign = sorted(l0_benign)
        layer_used = 'L3_safety_fallback_L0'
        fallback_applied = True
        fallback_reason = 'l2_below_safety_valve'
    else:
        final_benign = combined_benign
        fallback_applied = False
        fallback_reason = 'none'


    final_anomalies = sorted(set(range(n_clients)) - set(final_benign))

    info = {
        'attack_alert': True,
        'density_gap_detected': density_gap_detected,
        'gap_detected': density_gap_detected,
        'attack_gate': bool(attack_gate),
        'gate_reason': gate_reason,
        'gap_concentration': gap_conc,
        'momentum_active': momentum_active,
        'attack_gate_min_count': int(min_gate_count),
        'attack_gate_l0_count': int(len(l0_anomalies)),
        'layer_used': layer_used,
        'fallback_applied': fallback_applied,
        'fallback_reason': fallback_reason,
        'degraded': fallback_applied,
        'l0_rejected_count': len(l0_anomalies),
        'l2_rejected_count': len(l2_anomalies),
        'rd_values': rd_values.tolist(),
        'low_density_count': int(len(low_data)),
        'high_density_count': int(len(high_data)),
        'natural_clusters_count': len(natural_clusters),
        'rejected_snnc_clusters': int(rejected_snnc_cluster_count),
        'auto_t': float(t_est),
        'auto_eps': float(eps_est),
        'n_clusters': 1 + len(natural_clusters),
        'anomalies_detected': len(final_anomalies),
    }
    return final_benign, final_anomalies, info


# =====================================================================
#  7. STANDALONE MDBSCAN (for unit tests / original algorithm)
# =====================================================================

def mdbscan(data, k=5, t=0.7, eps=0.5, min_pts=3):
    """Standalone MDBSCAN (Qian et al. 2024, Algorithm 2)."""
    n_samples = data.shape[0]
    labels = np.full(n_samples, -1)

    rd_values = compute_relative_density(data, k)
    low_data, low_indices, high_data, high_indices = extract_low_density(data, rd_values, t)

    natural_clusters = []
    remaining_low_indices = low_indices.tolist()
    if len(low_data) > 1:
        natural_clusters, remaining_low_indices = snnc(
            low_data, k, original_indices=low_indices
        )

    cluster_id = 0
    for cluster in natural_clusters:
        for idx in cluster:
            labels[idx] = cluster_id
        cluster_id += 1

    remaining_indices = np.concatenate([
        high_indices,
        np.array(remaining_low_indices, dtype=int)
    ]).astype(int)

    if len(remaining_indices) > 0:
        remaining_data = data[remaining_indices]
        if len(remaining_data) >= min_pts:
            dbscan = SklearnDBSCAN(eps=eps, min_samples=min_pts, metric='euclidean')
            dbscan_labels = dbscan.fit_predict(remaining_data)
            for i, orig_idx in enumerate(remaining_indices):
                if dbscan_labels[i] == -1:
                    labels[orig_idx] = -1
                else:
                    labels[orig_idx] = dbscan_labels[i] + cluster_id
            if np.any(dbscan_labels >= 0):
                cluster_id += dbscan_labels.max() + 1
        else:
            for idx in remaining_indices:
                labels[idx] = -1

    noise_indices = np.where(labels == -1)[0]
    clustered_indices = np.where(labels >= 0)[0]
    if len(noise_indices) > 0 and len(clustered_indices) > 0:
        clustered_data = data[clustered_indices]
        nn = NearestNeighbors(n_neighbors=1, metric='euclidean')
        nn.fit(clustered_data)
        for noise_idx in noise_indices:
            _, nearest = nn.kneighbors(data[noise_idx:noise_idx + 1])
            nearest_clustered_idx = clustered_indices[nearest[0, 0]]
            labels[noise_idx] = labels[nearest_clustered_idx]

    info = {
        'rd_values': rd_values,
        'low_density_indices': low_indices.tolist(),
        'high_density_indices': high_indices.tolist(),
        'natural_clusters': natural_clusters,
        'n_clusters': len(set(labels[labels >= 0])),
    }
    return labels, info
