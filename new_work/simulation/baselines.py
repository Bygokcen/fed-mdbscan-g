"""
Baseline aggregation methods for comparison with Fed-MDBSCAN.

Implements:
    - Fed-DBSCAN: Standard DBSCAN-based gradient filtering
    - FedRRA: Reputation-Aware Robust Federated Learning (simplified)
    - FedG2L: Gradient-to-Local privacy-preserving scheme (simplified)

These represent the current state-of-the-art approaches that use
density-based clustering for anomaly detection in federated learning.
"""

import numpy as np
from sklearn.cluster import DBSCAN as SklearnDBSCAN
from sklearn.neighbors import NearestNeighbors


def _auto_eps(data, k=5):
    """Auto-estimate DBSCAN eps from k-nearest neighbor distances."""
    n = data.shape[0]
    ek = min(k, n - 1)
    if ek <= 0:
        return 1.0
    nn = NearestNeighbors(n_neighbors=ek + 1, metric='euclidean')
    nn.fit(data)
    distances, _ = nn.kneighbors(data)
    k_dists = np.sort(distances[:, -1])
    return max(np.percentile(k_dists, 75), 1e-10)


def fed_dbscan(gradients, eps='auto', min_pts=3):
    """
    Standard Federated DBSCAN: Apply DBSCAN directly to gradient vectors.

    The largest cluster is considered benign; all other points (noise + smaller
    clusters) are treated as potential anomalies.

    Limitation: Uses a single global eps threshold, which fails when benign
    updates have varying densities (the core problem Fed-MDBSCAN solves).

    Args:
        gradients: numpy array of shape (n_clients, n_features)
        eps: DBSCAN distance threshold
        min_pts: minimum points for dense region

    Returns:
        benign_indices: list of indices classified as benign
        anomaly_indices: list of indices classified as anomalies
        info: dict with method details
    """
    n_clients = gradients.shape[0]

    if n_clients <= 2:
        return list(range(n_clients)), [], {'method': 'fed_dbscan', 'n_clusters': 1}

    if eps == 'auto':
        eps = _auto_eps(gradients, k=min_pts)

    dbscan = SklearnDBSCAN(eps=eps, min_samples=min_pts, metric='euclidean')
    labels = dbscan.fit_predict(gradients)

    # Find the largest cluster (assumed benign majority)
    unique_labels = set(labels)
    unique_labels.discard(-1)  # Remove noise label

    if len(unique_labels) == 0:
        # No clusters found — all are noise, treat all as benign (fallback)
        return list(range(n_clients)), [], {
            'method': 'fed_dbscan', 'n_clusters': 0, 'fallback': True
        }

    # Find largest cluster
    largest_cluster = max(unique_labels, key=lambda l: np.sum(labels == l))

    benign_indices = np.where(labels == largest_cluster)[0].tolist()
    anomaly_indices = [i for i in range(n_clients) if i not in benign_indices]

    info = {
        'method': 'fed_dbscan',
        'n_clusters': len(unique_labels),
        'largest_cluster_size': len(benign_indices),
        'anomalies_detected': len(anomaly_indices),
        'labels': labels.tolist(),
    }

    return benign_indices, anomaly_indices, info


def fed_rra(gradients, eps='auto', min_pts=3, reputation_threshold=0.5):
    """
    FedRRA: Reputation-Aware Robust Federated Learning.

    Simplified implementation of the two-step detection process:
        Step 1: Parameter-based pre-filtering using cosine similarity
                to the median gradient.
        Step 2: DBSCAN clustering on remaining gradients.

    Reference: FedRRA (2023) — IEEE Xplore

    Args:
        gradients: numpy array of shape (n_clients, n_features)
        eps: DBSCAN epsilon
        min_pts: DBSCAN min_samples
        reputation_threshold: cosine similarity threshold for pre-filtering

    Returns:
        benign_indices, anomaly_indices, info
    """
    n_clients = gradients.shape[0]

    if n_clients <= 2:
        return list(range(n_clients)), [], {'method': 'fed_rra', 'n_clusters': 1}

    # Step 1: Compute median gradient as reference
    median_gradient = np.median(gradients, axis=0)

    # Compute cosine similarity of each client to median
    similarities = np.array([
        _cosine_similarity(gradients[i], median_gradient)
        for i in range(n_clients)
    ])

    # Pre-filter: remove clients with low similarity
    pre_filtered_mask = similarities >= reputation_threshold
    pre_filtered_indices = np.where(pre_filtered_mask)[0]
    pre_anomaly_indices = np.where(~pre_filtered_mask)[0].tolist()

    if len(pre_filtered_indices) <= min_pts:
        # Too aggressive filtering — use all clients
        pre_filtered_indices = np.arange(n_clients)
        pre_anomaly_indices = []

    # Step 2: DBSCAN on remaining gradients
    filtered_gradients = gradients[pre_filtered_indices]
    if eps == 'auto':
        eps = _auto_eps(filtered_gradients, k=min_pts)
    dbscan = SklearnDBSCAN(eps=eps, min_samples=min_pts, metric='euclidean')
    labels = dbscan.fit_predict(filtered_gradients)

    # Find largest cluster
    unique_labels = set(labels)
    unique_labels.discard(-1)

    if len(unique_labels) == 0:
        benign_indices = pre_filtered_indices.tolist()
    else:
        largest_cluster = max(unique_labels, key=lambda l: np.sum(labels == l))
        benign_local = np.where(labels == largest_cluster)[0]
        benign_indices = [pre_filtered_indices[i] for i in benign_local]

    anomaly_indices = sorted(set(range(n_clients)) - set(benign_indices))

    info = {
        'method': 'fed_rra',
        'pre_filtered_count': len(pre_anomaly_indices),
        'similarities': similarities.tolist(),
        'n_clusters': len(unique_labels),
        'anomalies_detected': len(anomaly_indices),
    }

    return sorted(benign_indices), anomaly_indices, info


def fed_g2l(gradients, threshold_factor=1.5):
    """
    FedG2L: Gradient-to-Local privacy-preserving scheme.

    Simplified implementation of dynamic security clustering:
        - Compute distance of each gradient to the geometric median
        - Weight gradients inversely by their distance
        - Flag gradients beyond threshold_factor * median_distance as anomalies

    Reference: FedG2L (2023) — Taylor & Francis

    Args:
        gradients: numpy array of shape (n_clients, n_features)
        threshold_factor: factor to multiply median distance for threshold

    Returns:
        benign_indices, anomaly_indices, info
    """
    n_clients = gradients.shape[0]

    if n_clients <= 2:
        return list(range(n_clients)), [], {'method': 'fed_g2l'}

    # Compute geometric median using Weiszfeld's algorithm
    geo_median = _geometric_median(gradients)

    # Compute L2 distance of each gradient to geometric median
    distances = np.linalg.norm(gradients - geo_median, axis=1)

    # Dynamic threshold: median distance * factor
    median_dist = np.median(distances)
    threshold = median_dist * threshold_factor

    # Classify
    benign_mask = distances <= threshold
    benign_indices = np.where(benign_mask)[0].tolist()
    anomaly_indices = np.where(~benign_mask)[0].tolist()

    info = {
        'method': 'fed_g2l',
        'distances': distances.tolist(),
        'threshold': float(threshold),
        'median_distance': float(median_dist),
        'anomalies_detected': len(anomaly_indices),
    }

    return benign_indices, anomaly_indices, info


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _geometric_median(data, max_iter=100, tol=1e-5):
    """
    Compute the geometric median using Weiszfeld's algorithm.
    More robust to outliers than arithmetic mean.
    """
    median = np.mean(data, axis=0)

    for _ in range(max_iter):
        distances = np.linalg.norm(data - median, axis=1)
        distances = np.maximum(distances, 1e-10)  # Avoid division by zero
        weights = 1.0 / distances
        new_median = np.average(data, axis=0, weights=weights)

        if np.linalg.norm(new_median - median) < tol:
            break
        median = new_median

    return median


def krum(gradients, num_malicious=None, multi_krum_m=None):
    """
    Multi-Krum (Blanchard et al., NeurIPS 2017).

    For each gradient i, compute its score = sum of squared distances to its
    (n - f - 2) closest neighbors. Select the m gradients with smallest scores.
    Default m = n - f - 2 (Multi-Krum); if multi_krum_m=1, equivalent to vanilla Krum.

    Args:
        gradients: numpy array (n_clients, n_features)
        num_malicious: estimate of f (default n // 4)
        multi_krum_m: number of gradients to select (default n - f - 2)

    Returns:
        benign_indices, anomaly_indices, info
    """
    n = gradients.shape[0]
    if n <= 2:
        return list(range(n)), [], {'method': 'krum'}

    if num_malicious is None:
        num_malicious = max(0, n // 4)
    f = min(num_malicious, max(0, n - 3))
    closest_count = max(1, n - f - 2)

    # Avoid the N x N x d temporary for CNN updates.
    from scipy.spatial.distance import cdist
    dist_sq = cdist(gradients, gradients, metric='sqeuclidean')
    np.fill_diagonal(dist_sq, np.inf)
    sorted_dists = np.sort(dist_sq, axis=1)
    scores = sorted_dists[:, :closest_count].sum(axis=1)

    if multi_krum_m is None:
        multi_krum_m = closest_count
    multi_krum_m = max(1, min(multi_krum_m, n))

    selected = np.argsort(scores)[:multi_krum_m].tolist()
    benign_indices = sorted(int(i) for i in selected)
    anomaly_indices = [i for i in range(n) if i not in benign_indices]

    return benign_indices, anomaly_indices, {
        'method': 'krum',
        'm': multi_krum_m,
        'f_assumed': f,
        'selected_count': len(benign_indices),
    }


def coord_median(gradients):
    """
    Coordinate-wise Median (Yin et al., ICML 2018).

    Aggregation method, not a filter — robustness comes from the median
    operation itself, which tolerates up to 50% adversarial corruption per
    coordinate. All clients are reported as "benign" for FPR/TPR bookkeeping;
    the server is responsible for switching the aggregation op to median.

    Returns:
        benign_indices = all, anomaly_indices = [], info marker
    """
    n = gradients.shape[0]
    return list(range(n)), [], {'method': 'coord_median', 'aggregation_op': 'median'}


def fltrust(gradients, root_gradient, clip_to_root_norm=True):
    """
    FLTrust (Cao et al., NDSS 2021).

    Server holds a small clean "root" dataset and trains it for one local step
    per round to obtain g_root. Each client gradient g_i is scored by:
        trust_i = max(0, cosine(g_i, g_root))
    Gradients with non-positive cosine are dropped; the rest are clipped to
    have ||g_i|| ≤ ||g_root|| (norm clipping) and weighted by trust_i.

    The server-side weighted aggregation is signaled via filter_info; this
    function only computes the trust scores, the kept-set and the per-client
    weights so that server.aggregate can apply them.

    Args:
        gradients: (n, d) numpy array
        root_gradient: (d,) numpy array — server's clean root gradient
        clip_to_root_norm: if True, clip each kept gradient to ||g_root||

    Returns:
        benign_indices: clients with positive cosine
        anomaly_indices: clients with non-positive cosine (dropped)
        info: dict with 'trust_weights', 'cos_sims', 'aggregation_op'='fltrust'
    """
    n = gradients.shape[0]
    if n == 0:
        return [], [], {'method': 'fltrust'}

    root_norm = float(np.linalg.norm(root_gradient))
    if root_norm < 1e-10:
        # Degenerate root → fall back to mean
        return list(range(n)), [], {
            'method': 'fltrust', 'aggregation_op': 'mean', 'fallback': True
        }

    cos_sims = np.zeros(n)
    norms = np.zeros(n)
    for i in range(n):
        g = gradients[i]
        ng = float(np.linalg.norm(g))
        norms[i] = ng
        cos_sims[i] = (np.dot(g, root_gradient) / (ng * root_norm)) if ng > 1e-10 else 0.0

    trust = np.maximum(cos_sims, 0.0)
    benign_indices = [int(i) for i in range(n) if trust[i] > 0]
    anomaly_indices = [int(i) for i in range(n) if trust[i] <= 0]

    return benign_indices, anomaly_indices, {
        'method': 'fltrust',
        'cos_sims': cos_sims.tolist(),
        'trust_weights': trust.tolist(),
        'norms': norms.tolist(),
        'root_norm': root_norm,
        'clip_to_root_norm': clip_to_root_norm,
        'aggregation_op': 'fltrust',
    }


def flame(gradients, noise_std=0.001, eps_dbscan='auto'):
    """
    FLAME (Nguyen et al., USENIX Security 2022).

    Three-step pipeline:
        1) Cosine-distance DBSCAN clustering — keep only the largest cluster
           (assumed benign majority).
        2) Norm clipping to the median norm S = median(||g_i||) of survivors.
        3) Add small Gaussian noise σ × S as a lightweight DP layer.

    Returns the cluster-survivor index list and signals the server to apply
    norm clipping + Gaussian noise via filter_info.

    Args:
        gradients: (n, d) array
        noise_std: σ multiplier for DP noise (default 0.001 — very small)
        eps_dbscan: cosine-distance eps for DBSCAN; 'auto' = median pairwise

    Returns:
        benign_indices, anomaly_indices, info (with aggregation_op='flame')
    """
    n = gradients.shape[0]
    if n <= 2:
        return list(range(n)), [], {'method': 'flame'}

    # 1) Cosine distance pairwise
    norms = np.linalg.norm(gradients, axis=1)
    norms = np.maximum(norms, 1e-10)
    normed = gradients / norms[:, None]
    cos_sim = normed @ normed.T
    cos_dist = 1.0 - cos_sim

    if eps_dbscan == 'auto':
        # Median upper-triangle pairwise distance — full magnitude. Smaller
        # multipliers (e.g. 0.5) cluster only a tiny core and reject the rest
        # as outliers, which inflates FPR catastrophically.
        iu = np.triu_indices(n, k=1)
        eps_dbscan = max(0.05, float(np.median(cos_dist[iu])))

    dbs = SklearnDBSCAN(eps=eps_dbscan, min_samples=2, metric='precomputed')
    labels = dbs.fit_predict(np.maximum(cos_dist, 0.0))

    unique_labels = set(labels)
    unique_labels.discard(-1)
    if len(unique_labels) == 0:
        # No clusters — accept all (fallback)
        survivors = list(range(n))
    else:
        largest = max(unique_labels, key=lambda l: int(np.sum(labels == l)))
        survivors = [int(i) for i in np.where(labels == largest)[0].tolist()]

    survivor_norms = norms[survivors]
    median_norm = float(np.median(survivor_norms)) if len(survivor_norms) else 0.0

    benign_indices = sorted(survivors)
    anomaly_indices = [i for i in range(n) if i not in survivors]

    return benign_indices, anomaly_indices, {
        'method': 'flame',
        'eps_dbscan': eps_dbscan,
        'median_norm': median_norm,
        'noise_std': noise_std,
        'aggregation_op': 'flame',
        'cluster_count': len(unique_labels),
    }


def flame_hdbscan(gradients, global_weights, noise_std=0.001):
    """Paper-based FLAME: local-model cosine HDBSCAN, all-update median clip.

    Nguyen et al., USENIX Security 2022, Algorithm 1 and Appendix E.
    sklearn includes self in min_samples: 2 corresponds to contrib's 1.
    Noise factor is explicit; this implementation asserts no DP budget.
    """
    from sklearn.cluster import HDBSCAN
    from sklearn.metrics.pairwise import cosine_distances
    n = len(gradients)
    models = gradients.astype(np.float64) + global_weights.astype(np.float64)
    distances = np.maximum(cosine_distances(models), 0.0)
    distances = (distances + distances.T) / 2
    np.fill_diagonal(distances, 0.0)
    labels = None
    if n <= 2 or np.all(distances == 0):
        accepted = list(range(n))
        clustering_skip_reason = 'small_cohort' if n <= 2 else 'zero_distances'
    else:
        labels = HDBSCAN(min_cluster_size=n // 2 + 1, min_samples=2,
                         metric='precomputed', allow_single_cluster=True,
                         copy=True).fit_predict(distances)
        accepted = np.flatnonzero(labels >= 0).tolist()
        clustering_skip_reason = 'none'
    # Preserve the HDBSCAN output before the server may replace an empty
    # selection with accept-all. A skipped fit has unknown, not zero, clusters.
    cluster_sizes = None if labels is None else {
        str(int(label)): int(np.count_nonzero(labels == label))
        for label in np.unique(labels) if label >= 0
    }
    return accepted, sorted(set(range(n)) - set(accepted)), {
        'method': 'flame_hdbscan', 'aggregation_op': 'flame',
        'median_norm': float(np.median(np.linalg.norm(gradients.astype(np.float64), axis=1))),
        'noise_std': float(noise_std), 'min_cluster_size': n // 2 + 1,
        'sklearn_min_samples': 2, 'geometry': 'local_model_cosine',
        'fallback_applied': not bool(accepted),
        'fallback_reason': 'no_majority_cluster' if not accepted else 'none',
        'flame_clustering': {
            'executed': labels is not None,
            'skip_reason': clustering_skip_reason,
            'min_cluster_size': n // 2 + 1,
            'cluster_sizes': cluster_sizes,
            'noise_count': None if labels is None else int(np.count_nonzero(labels == -1)),
            'selected_count_before_fallback': len(accepted),
        },
    }
