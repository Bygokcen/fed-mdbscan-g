"""
Metrics collection module for federated learning experiments.

Tracks per-round performance metrics including accuracy, false positive rate,
true positive rate (detection rate), and computational overhead.
"""

import time
import pandas as pd


def _validated_decision_ids(decision):
    if not isinstance(decision, dict):
        raise TypeError("decision must be a dictionary")
    if 'accepted_ids' not in decision or 'rejected_ids' not in decision:
        raise ValueError("decision must contain accepted_ids and rejected_ids")
    accepted = decision['accepted_ids']
    rejected = decision['rejected_ids']
    if not isinstance(accepted, (list, tuple)) or not isinstance(rejected, (list, tuple)):
        raise TypeError("decision IDs must be lists or tuples")
    accepted = list(accepted)
    rejected = list(rejected)
    try:
        accepted_set = set(accepted)
        rejected_set = set(rejected)
    except TypeError as exc:
        raise ValueError("decision IDs must be hashable") from exc
    if len(accepted_set) != len(accepted) or len(rejected_set) != len(rejected):
        raise ValueError("decision IDs must be unique")
    if accepted_set & rejected_set:
        raise ValueError("accepted and rejected sets must be disjoint")
    return accepted_set, rejected_set


def evaluate_detection_decision(decision, malicious_ids):
    """Evaluate a frozen defense decision against ground truth.

    This function is deliberately outside ``Server``: malicious identities are
    evaluator labels and cannot influence filtering, fallback, or aggregation.
    """
    accepted, rejected = _validated_decision_ids(decision)
    participants = accepted | rejected
    true_malicious = participants & set(malicious_ids)
    true_benign = participants - true_malicious
    rejected_set = rejected

    tp = len(rejected_set & true_malicious)
    fp = len(rejected_set & true_benign)
    tn = len(true_benign - rejected_set)
    fn = len(true_malicious - rejected_set)
    return {
        'fpr': fp / (fp + tn) if fp + tn else 0.0,
        'tpr': tp / (tp + fn) if tp + fn else 0.0,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn,
    }


def evaluate_attack_alert(decision, malicious_ids, attack_alert):
    """Score an already-frozen round alert without exposing labels to defense code."""
    accepted, rejected = _validated_decision_ids(decision)
    participants = accepted | rejected
    attack_present = bool(participants & set(malicious_ids))
    return {
        'alert_tp': int(bool(attack_alert) and attack_present),
        'alert_fp': int(bool(attack_alert) and not attack_present),
        'alert_fn': int(not bool(attack_alert) and attack_present),
        'alert_tn': int(not bool(attack_alert) and not attack_present),
    }


class MetricsCollector:
    """
    Collects and manages experiment metrics across communication rounds.

    Tracks:
        - Global model accuracy (test set performance)
        - False Positive Rate (FPR): benign updates wrongly flagged as anomalies
        - True Positive Rate (TPR): malicious updates correctly detected
        - Computational Overhead: time taken for the filtering/clustering step
    """

    def __init__(self):
        self.records = []
        self._timer_start = None

    def start_timer(self):
        """Start timing a clustering/filtering operation."""
        self._timer_start = time.time()

    def stop_timer(self):
        """Stop timing and return elapsed time in seconds."""
        if self._timer_start is None:
            return 0.0
        elapsed = time.time() - self._timer_start
        self._timer_start = None
        return elapsed

    def log_round(self, round_num, method, accuracy, fpr=0.0, tpr=0.0,
                  time_elapsed=0.0, extra=None):
        """
        Log metrics for a single communication round.

        Args:
            round_num: round number (0-indexed)
            method: aggregation method name ('fed_mdbscan_g', 'fed_dbscan', etc.)
            accuracy: global model accuracy on test set
            fpr: false positive rate (benign flagged as anomaly)
            tpr: true positive rate (malicious correctly detected)
            time_elapsed: time taken for clustering step (seconds)
            extra: dict of additional metrics to log
        """
        record = {
            'round': round_num,
            'method': method,
            'accuracy': accuracy,
            'fpr': fpr,
            'tpr': tpr,
            'time_elapsed': time_elapsed,
        }
        if extra:
            record.update(extra)
        self.records.append(record)

    def compute_detection_rates(self, predicted_anomalies, true_malicious_ids,
                                total_clients):
        """
        Compute FPR and TPR from predicted anomalies and ground truth.

        Args:
            predicted_anomalies: list of client indices flagged as anomalies
            true_malicious_ids: set/list of actually malicious client IDs
            total_clients: total number of clients

        Returns:
            (fpr, tpr) tuple
        """
        true_malicious = set(true_malicious_ids)
        predicted = set(predicted_anomalies)
        all_clients = set(range(total_clients))
        true_benign = all_clients - true_malicious

        # True Positives: malicious clients correctly flagged
        tp = len(predicted & true_malicious)
        # False Positives: benign clients wrongly flagged
        fp = len(predicted & true_benign)
        # True Negatives: benign clients correctly not flagged
        tn = len(true_benign - predicted)
        # False Negatives: malicious clients missed
        fn = len(true_malicious - predicted)

        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        return fpr, tpr

    def get_summary(self, method=None):
        """
        Get summary statistics for all rounds (or a specific method).

        Args:
            method: if specified, filter to only this method

        Returns:
            dict with mean and std of each metric
        """
        df = pd.DataFrame(self.records)
        if method:
            df = df[df['method'] == method]

        if len(df) == 0:
            return {}

        summary = {}
        for col in ['accuracy', 'fpr', 'tpr', 'time_elapsed']:
            if col in df.columns:
                summary[f'{col}_mean'] = df[col].mean()
                summary[f'{col}_std'] = df[col].std()
                summary[f'{col}_max'] = df[col].max()
                summary[f'{col}_min'] = df[col].min()

        summary['total_rounds'] = len(df)
        summary['method'] = method
        return summary

    def get_dataframe(self, method=None):
        """
        Get all records as a pandas DataFrame.

        Args:
            method: optional method filter

        Returns:
            pandas DataFrame
        """
        df = pd.DataFrame(self.records)
        if method and len(df) > 0:
            df = df[df['method'] == method]
        return df

    def save_csv(self, path, method=None):
        """
        Save metrics to a CSV file.

        Args:
            path: output CSV file path
            method: optional method filter
        """
        df = self.get_dataframe(method)
        df.to_csv(path, index=False)
        print(f"Metrics saved to {path} ({len(df)} records)")

    def save_all_methods_csv(self, output_dir):
        """
        Save a separate CSV for each method.

        Args:
            output_dir: directory to save CSV files
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(self.records)
        methods = df['method'].unique()

        for method in methods:
            method_df = df[df['method'] == method]
            path = os.path.join(output_dir, f'{method}_results.csv')
            method_df.to_csv(path, index=False)
            print(f"  {method}: {len(method_df)} records → {path}")
