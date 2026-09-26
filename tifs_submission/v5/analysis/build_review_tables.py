#!/usr/bin/env python3
"""Supplement tables for the targeted review experiments of 26 September 2026.

Reads analysis/evidence/review_20260926/{e0_summary.json, review_summary.json}
and writes manuscript/generated/review_*.tex with the same table helper as
build_tables.py.  No training, network or raw archive is needed.

    python analysis/build_review_tables.py --root .
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_tables import tex_table  # noqa: E402

FAMILY_LABEL = [('clean', 'Adversary-free'), ('constrained', 'Constrained probes'),
                ('patch', 'Patch backdoor'), ('loud_gaussian', 'Loud Gaussian'),
                ('label_flip', 'Label flipping'), ('bounded', 'Bounded perturbation')]


def alpha_label(a):
    return f"{a:g}"


def e0_table(e0):
    pooled = {(r['family'], r['alpha']): r for r in e0['pooled']}
    rows = []
    for fam, label in FAMILY_LABEL:
        alphas = sorted({a for f, a in pooled if f == fam}, reverse=True)
        for i, a in enumerate(alphas):
            r = pooled[(fam, a)]
            rows.append([label if i == 0 else '', alpha_label(a), str(r['rounds']), str(r['gate_open']),
                         str(r['rounds_with_removal']), str(r['removed_updates'])])
        rows.append(None)
    rows = rows[:-1]
    return tex_table(
        caption=r"Cluster-Stage Activity in the Canonical Fed-MDBSCAN-G Runs",
        label="tab:review_e0",
        header=["Attack family", r"$\alpha$", "Rounds", "Gate open", "Rounds removing", "Removed"],
        units=["", "", "", "", r"from $B_0$", "updates"],
        rows=rows, colspec="llrrrr",
        notes=(r"Counts over every dataset and seed of the canonical main block, read from the "
               r"recorded round fields; no run was repeated. The gate is open when the recorded layer "
               r"is not Stage~1 alone. A removed update is a Stage-1-accepted update that the cluster "
               r"stage excludes from the final set, $|B_0|-|B|$; in adversary-free rounds all of them "
               r"are honest."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    ev = os.path.join(root, 'analysis', 'evidence', 'review_20260926')
    gen = os.path.join(root, 'manuscript', 'generated')
    e0 = json.load(open(os.path.join(ev, 'e0_summary.json')))
    open(os.path.join(gen, 'review_e0.tex'), 'w', encoding='utf-8').write(e0_table(e0))
    summary_path = os.path.join(ev, 'review_summary.json')
    if os.path.exists(summary_path):
        summary = json.load(open(summary_path))
        for name, fn in (('review_e1.tex', e1_table), ('review_e2.tex', e2_table), ('review_e3.tex', e3_table),
                         ('review_e4.tex', e4_table)):
            open(os.path.join(gen, name), 'w', encoding='utf-8').write(fn(summary))
        open(os.path.join(gen, 'review_main.tex'), 'w', encoding='utf-8').write(main_table(summary))
        gen_tr = os.path.join(root, 'manuscript', 'generated_tr')
        open(os.path.join(gen_tr, 'review_main.tex'), 'w', encoding='utf-8').write(main_table(summary, turkish=True))
    print('review tables written')


E1_ORDER = [('7.1', r'Min-Max, $\alpha=0.1$'), ('7.2', r'Min-Sum, $\alpha=0.01$'),
            ('8.1', r'Patch, $\alpha=0.1$'), ('8.2', r'Patch, $\alpha=0.01$'),
            ('6.2', r'Adversary-free, $\alpha=0.01$')]


def e1_table(summary):
    rows = []
    by = {r['scenario']: r for r in summary['e1']}
    for sc, label in E1_ORDER:
        r = by[sc]
        attackers = (f"{r['attackers_outside_b0']}/{r['attackers_total']}" if r['attackers_total'] else '--')
        with_groups = r['x_forced_matrices_with_groups']
        in_b0 = str(r['x_forced_matrices_groups_nonempty_in_b0']) if with_groups else '--'
        rows.append([label, f"{r['exact_runs']}/{r['runs']}", str(r['matrices']),
                     f"{r['gamma_median']:.2f}", f"{r['gamma_le_tau']}", str(with_groups), in_b0,
                     str(r['sufficient_condition']), str(r['deployed_gate_ran']),
                     str(r['deployed_matrices_with_removal']),
                     f"{r['deployed_removed_honest']}/{r['deployed_removed_attackers']}", attackers])
    return tex_table(
        caption=r"Decision-Path Measurements on Canonical Checkpoint Matrices",
        label="tab:review_e1", star=True,
        header=["Condition", "Exact", "Matrices", "Median", r"$\Gamma\leq\tau$", "With", r"Groups",
                "Sufficient", "Deployed", "Matrices", "Removed", "Attackers"],
        units=["", "runs", "", r"$\Gamma$", "", "groups", r"in $B_0$", "condition", "gate ran",
               "with removal", "honest/att.", r"outside $B_0$"],
        rows=rows, colspec="lrrrrrrrrrrr",
        notes=(r"Canonical Fed-MDBSCAN-G runs on MNIST and Fashion-MNIST, three seeds each, re-executed "
               r"with the frozen canonical source; ``Exact'' counts runs whose 30 recorded rounds matched "
               r"the archive in every non-timing field. Matrices are the server inputs of rounds 0, 9, "
               r"and 29. ``With groups'' counts matrices on which the cluster stage, forced to run by the "
               r"density-only gate, recovers at least one candidate group; ``Groups in $B_0$'' counts those "
               r"on which every recovered group lies in $B_0$. ``Sufficient condition'' counts matrices "
               r"with $\Gamma\leq\tau=2$ on which every recovered group, if any, lies in $B_0$. Removal "
               r"columns refer to the deployed gate. Attackers outside $B_0$ were excluded by Stage~1."))


def e2_table(summary):
    rows = []
    label = {('mnist', '1.1'): r'MNIST, $\alpha=0.5$', ('mnist', '6.2'): r'MNIST, $\alpha=0.01$',
             ('har', '6.2'): r'HAR, $\alpha=0.01$'}
    for r in summary['e2a']:
        rows.append([label[(r['dataset'], r['scenario'])], f"{r['exact_runs']}/{r['runs']}",
                     str(r['clustered_rounds']), str(r['equal_rounds']), str(r['max_symmetric_difference'])])
    return tex_table(
        caption=r"FLAME Clustering: Local Selector Versus Reference HDBSCAN",
        label="tab:review_e2", header=["Clean cell", "Exact", "Clustered", "Identical", "Max. sym."],
        units=["", "runs", "rounds", "selections", "difference"], rows=rows, colspec="lrrrr",
        notes=(r"Canonical FLAME runs were re-executed; in every round the precomputed cosine-distance "
               r"matrix of the local selector was also passed to the reference \texttt{hdbscan} library "
               r"(0.8.44) with $\texttt{min\_cluster\_size}=\lfloor n/2\rfloor+1$, "
               r"$\texttt{min\_samples}=1$, and a single cluster allowed. The runs kept the local "
               r"selection, so reproduction of the archive could be checked."))


def signed(v):
    return (r"$-$" if v < 0 else "+") + f"{abs(v):.2f}"


def span(d):
    return f"{signed(d['mean'])} [{signed(d['min'])}, {signed(d['max'])}]"


NAME = {'mnist': 'MNIST', 'fashion_mnist': 'Fashion-MNIST', 'har': 'UCI HAR'}


def e3_table(summary):
    rows = [[NAME[r['dataset']], f"{r['fedavg']:.2f}", f"{r['flame']:.2f}", f"{r['flame_nonoise']:.2f}",
             f"{r['flame_random']:.2f}", f"{r['flame_matched_random']:.2f}", f"{r['multikrum']:.2f}",
             f"{r['multikrum_random']:.2f}"]
            for r in summary['e23']]
    return tex_table(
        caption=r"Adversary-Free Final Accuracy at $\alpha=0.01$ With Noise and Selection Controls",
        label="tab:review_e3", star=True,
        header=["Dataset", "FedAvg", "FLAME", "FLAME", "FLAME random", "FLAME random", "Multi-Krum", "Multi-Krum"],
        units=["", "", "", "no noise", "rule-sized", "matched", "", "random"],
        rows=rows, colspec="lrrrrrrr",
        notes=(r"Mean final accuracy (\%) over seeds 42, 137, and 2024. FedAvg, FLAME, and Multi-Krum are "
               r"the canonical runs. ``No noise'' sets the FLAME noise factor to zero. The random controls "
               r"replace the selected updates in every round with a uniformly random subset; the clipping "
               r"and noise rules are kept. For Multi-Krum the subset has 61 members in both arms. ``Rule-sized'' "
               r"uses the size that FLAME selects on the control's own updates, so admitted counts can "
               r"drift from the canonical run. ``Matched'' uses the admitted count that the canonical FLAME "
               r"run recorded in each round, so admitted counts and BER equal those of canonical FLAME. All "
               r"controls share each seed's data partition, participation schedule, and initial model with "
               r"the canonical runs."))


def e4_table(summary):
    rows = [[NAME[r['dataset']], span(r['noise_effect']), span(r['flame_minus_random']),
             span(r['flame_minus_matched_random']), span(r['multikrum_minus_random']),
             span(r['fedavg_minus_multikrum_random'])]
            for r in summary['e23']]
    return tex_table(
        caption=r"Paired Final-Accuracy Differences for the Controls of Table~\ref{tab:review_e3}",
        label="tab:review_e4", star=True,
        header=["Dataset", "No noise", "FLAME", "FLAME", "Multi-Krum", "FedAvg"],
        units=["", r"$-$ FLAME", r"$-$ rule-sized", r"$-$ matched", r"$-$ random", r"$-$ Multi-Krum random"],
        rows=rows, colspec="lrrrrr",
        notes=(r"Percentage points, mean [minimum, maximum] over the three seed pairs. A negative entry "
               r"in a FLAME or Multi-Krum column means that the rule's own selection yields lower "
               r"accuracy than a random subset."))


def main_table(summary, turkish=False):
    rows = [[NAME[r['dataset']], f"{r['fedavg']:.2f}", f"{r['multikrum']:.2f}", f"{r['multikrum_random']:.2f}",
             f"{r['flame']:.2f}", f"{r['flame_matched_random']:.2f}"] for r in summary['e23']]
    if turkish:
        return tex_table(
            caption=r"$\alpha=0.01$'de Saldırgansız Son Doğruluk (\%): Kurallar ve Aynı Büyüklükte Rastgele Altkümeler",
            label="tab:random", header=["Veri kümesi", "FedAvg", "Multi-Krum", "Multi-Krum", "FLAME", "FLAME"],
            units=["", "", "kural", "rastgele", "kural", "rastgele"], rows=rows, colspec="lrrrrr",
            notes=(r"Üç tohum üzerinden ortalamalar. Rastgele altkümeler her turda kuralın seçtiği "
                   r"güncellemelerin yerini alır ve kabul sayısını korur: Multi-Krum için 61, FLAME için "
                   r"kanonik FLAME koşumunun o turda kaydettiği sayı. Kırpma ve gürültü kuralları korunur; "
                   r"eşleştirilmiş farklar ek belgededir."))
    return tex_table(
        caption=r"Adversary-Free Final Accuracy (\%) at $\alpha=0.01$: Rules Versus Random Subsets of the Same Size",
        label="tab:random", header=["Dataset", "FedAvg", "Multi-Krum", "Multi-Krum", "FLAME", "FLAME"],
        units=["", "", "rule", "random", "rule", "random"], rows=rows, colspec="lrrrrr",
        notes=(r"Means over three seeds. Random subsets replace a rule's selected updates in every round "
               r"and keep its admitted count: 61 for Multi-Krum and, for FLAME, the count that the "
               r"canonical FLAME run recorded in that round. The clipping and noise rules are kept; paired "
               r"differences are in the supplement."))


if __name__ == '__main__':
    main()
