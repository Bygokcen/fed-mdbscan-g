"""
Paired one-sided Wilcoxon signed-rank tests for the paper's §5 significance
paragraph.

Input : new_work/results/phase2b_report/table_final_accuracy.csv
        (45 measurement points = 3 datasets x 15 scenarios; per-method
        3-seed mean final-round accuracy, produced by report_phase2b.py)
Output: W statistic, one-sided p-value and mean accuracy difference for
        fed_mdbscan_g vs every rival, printed as a table and saved next to
        the input as wilcoxon_significance.csv.

Usage:
    python -m simulation.report_wilcoxon
"""

import os

import pandas as pd
from scipy.stats import wilcoxon

BASE = os.path.join(os.path.dirname(__file__), '..', 'results', 'phase2b_report')
INPUT = os.path.join(BASE, 'table_final_accuracy.csv')
OUTPUT = os.path.join(BASE, 'wilcoxon_significance.csv')

OURS = 'fed_mdbscan_g'
RIVALS = ['fed_dbscan', 'fed_rra', 'fed_g2l', 'fedavg',
          'krum', 'coord_median', 'fltrust', 'flame']


def main():
    df = pd.read_csv(INPUT)
    n = len(df)
    print(f"Loaded {n} measurement points "
          f"({df['dataset'].nunique()} datasets x {df['scenario'].nunique()} scenarios)")
    print(f"{'rival':<14}{'W':>8}{'p (one-sided)':>16}{'mean diff':>12}")

    rows = []
    for rival in RIVALS:
        diffs = df[OURS] - df[rival]
        # one-sided: H1 = fed_mdbscan_g accuracy > rival accuracy
        stat, p = wilcoxon(df[OURS], df[rival], alternative='greater')
        rows.append({'rival': rival, 'n': n, 'W': stat,
                     'p_one_sided': p, 'mean_diff': diffs.mean()})
        print(f"{rival:<14}{stat:>8.0f}{p:>16.3g}{diffs.mean():>+12.4f}")

    pd.DataFrame(rows).to_csv(OUTPUT, index=False)
    print(f"\nSaved -> {OUTPUT}")


if __name__ == '__main__':
    main()
