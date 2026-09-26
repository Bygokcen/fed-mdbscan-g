#!/usr/bin/env python3
"""
build_tables.py -- regenerate the experimental tables, figures and derived
summary statistics in V4 from audit-v2 and checkpoint evidence files.

Inputs  (analysis/evidence/):
    cells.csv                    per method-condition cell aggregates (3 seeds)
    units.csv                    per method-condition-seed run records
    outcomes.csv                 planned/valid/failed accounting
    scenario_manifest.json       condition definitions (alpha, attack, ratio)
    unclustered_policy_summary.csv   fixed-matrix consensus-coverage replay
    mechanism_clusters.csv       recovered clusters at the selected checkpoint

Outputs (manuscript/generated/*.tex, manuscript/figures/*, analysis/derived_values.json)

Standard library + matplotlib only.  No network, no raw training archive.
Run:  python3 analysis/build_tables.py --root .
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics as st
from collections import defaultdict

# --------------------------------------------------------------------------
# condition metadata (mirrors scenario_manifest.json; asserted against it)
# --------------------------------------------------------------------------
ALPHA = {
    "1.1": 0.5, "1.2": 0.5, "1.3": 0.5,
    "2.1": 0.1, "2.2": 0.1, "2.3": 0.1,
    "3.1": 0.01, "3.2": 0.01, "3.3": 0.01,
    "4.1": 0.1, "4.2": 0.01, "4.3": 0.01,
    "5.1": 0.1, "5.2": 0.01, "5.3": 0.01,
    "6.1": 0.1, "6.2": 0.01,
    "7.1": 0.1, "7.2": 0.01,
    "8.1": 0.1, "8.2": 0.01,
}
# adversary-free conditions (malicious_ratio == 0.0)
BENIGN = {"1.1": 0.5, "6.1": 0.1, "6.2": 0.01}

# Attack families in a fixed display order; displacement is NOT measured here.
FAMILY = {
    "1.2": "loud", "2.1": "loud", "2.3": "loud", "3.1": "loud", "3.2": "loud",
    "1.3": "flip", "2.2": "flip", "3.3": "flip",
    "8.1": "patch", "8.2": "patch",
    "4.1": "bounded", "4.2": "bounded", "4.3": "bounded",
    "5.1": "bounded", "5.2": "bounded", "5.3": "bounded",
    "7.1": "constrained", "7.2": "constrained",
}
FAMILY_LABEL = {
    "loud": r"Loud Gaussian ($\sigma=5$)",
    "flip": "Label flipping",
    "patch": "Patch backdoor",
    "bounded": "Bounded random direction",
    "constrained": "Constrained omniscient",
}
FAMILY_ORDER = ["loud", "flip", "patch", "bounded", "constrained"]

# Rules with logged client-level exclusions; FLTrust logs zero trust weight.
REJECTORS = ["krum_bound30", "fltrust_normalized", "flame_hdbscan", "fed_mdbscan_g"]
# rules with no per-client rejection decision (harm channel is distortion, not exclusion)
NONREJECTORS = ["norm_clip", "coord_median"]
UNDEFENDED = ["fedavg", "sample_weighted_mean"]

METHOD_LABEL = {
    "fedavg": "Uniform mean (undefended)",
    "sample_weighted_mean": "Sample-weighted mean (undefended)",
    "norm_clip": "Norm clipping",
    "coord_median": "Coordinate-wise median",
    "krum_bound30": "Multi-Krum",
    "fltrust_normalized": "FLTrust (normalized)",
    "flame_hdbscan": "FLAME (HDBSCAN)",
    "fed_mdbscan_g": "Fed-MDBSCAN-G (full)",
    "mdbg_l0_only": "Fed-MDBSCAN-G, stage 1 only",
    "mdbg_no_valve": "Fed-MDBSCAN-G, no valve",
    "mdbg_no_momentum": "Fed-MDBSCAN-G, no activation memory",
    "fed_g2l_25": "Geometric-median distance control",
    "mdbg_rtr15": "Trust-region multiplier 1.5",
    "mdbg_rtr20": "Trust-region multiplier 2.0",
    "mdbg_rtr30": "Trust-region multiplier 3.0",
}
DS_LABEL = {"mnist": "MNIST", "fashion_mnist": "Fashion", "har": "HAR", "cifar10": "CIFAR-10"}
DS_ORDER = ["mnist", "fashion_mnist", "har", "cifar10"]

# design constants of the evaluated configuration (see manuscript Sec. V)
N_PARTICIPANTS = 90          # clients contributing per round in the main block
MULTIKRUM_F = 27             # ceil(0.3 * 90)
MULTIKRUM_M = N_PARTICIPANTS - MULTIKRUM_F - 2   # 61 selected
FLAME_MIN_CLUSTER = N_PARTICIPANTS // 2 + 1      # 46


def pf(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct(x, nd=2):
    return "--" if x is None else f"{100 * x:.{nd}f}"


def load(root):
    ev = os.path.join(root, "analysis", "evidence")
    rd = lambda n: list(csv.DictReader(open(os.path.join(ev, n), encoding="utf-8")))
    data = {
        "cells": rd("cells.csv"),
        "units": rd("units.csv"),
        "outcomes": rd("outcomes.csv"),
        "policy": rd("unclustered_policy_summary.csv"),
        "clusters": rd("mechanism_clusters.csv"),
    }
    with open(os.path.join(ev, "scenario_manifest.json"), encoding="utf-8") as fh:
        data["manifest"] = json.load(fh)
    with open(os.path.join(ev, "provenance.json"), encoding="utf-8") as fh:
        data["provenance"] = json.load(fh)
    return data


def check_manifest(manifest):
    """Assert our ALPHA / BENIGN metadata against the shipped scenario manifest."""
    seen = {}
    for job in manifest:
        spec = job.get("scenario")
        if isinstance(spec, dict) and "id" in spec:
            seen[spec["id"]] = (spec.get("alpha"), spec.get("malicious_ratio"))
    problems = []
    if not seen:
        problems.append("scenario metadata could not be read from the manifest")
    missing = sorted(set(ALPHA) - set(seen))
    if missing:
        problems.append(f"conditions absent from manifest: {missing}")
    for sid, alpha in ALPHA.items():
        if sid in seen and seen[sid][0] is not None and abs(seen[sid][0] - alpha) > 1e-12:
            problems.append(f"alpha mismatch for {sid}: manifest {seen[sid][0]} vs table {alpha}")
    for sid in BENIGN:
        if sid in seen and seen[sid][1] not in (0, 0.0):
            problems.append(f"{sid} marked adversary-free but manifest ratio {seen[sid][1]}")
    for sid, fam in FAMILY.items():
        if sid in seen and seen[sid][1] in (0, 0.0):
            problems.append(f"{sid} in an attack family but manifest ratio is 0")
    return seen, problems


# --------------------------------------------------------------------------
def _signfix(cell):
    """Typographic minus sign; values that round to zero are printed unsigned."""
    m = re.fullmatch(r"([+-])(\d+(?:\.\d+)?)", cell)
    if not m:
        return cell
    if float(m.group(2)) == 0:
        return m.group(2)
    return ("$+$" if m.group(1) == "+" else "$-$") + m.group(2)


def tex_table(caption, label, header, rows, colspec, notes=None, star=False, fit=True,
              units=None, pre_header=None, tabcolsep="4pt"):
    """Emit an IEEE-style booktabs table at a uniform 8-pt size (\\footnotesize).

    The caption is a short title; explanations go in the notes below the table.
    fit=True only *shrinks* a tabular wider than the column/text width (adjustbox
    max width); narrower tables keep their natural 8-pt size instead of being
    enlarged.  `units` adds a second header row; a str row is emitted verbatim.
    """
    env = "table*" if star else "table"
    width = r"\textwidth" if star else r"\columnwidth"
    placement = "!tp" if star else "!t"
    out = [f"\\begin{{{env}}}[{placement}]", "\\centering\\footnotesize",
           f"\\setlength{{\\tabcolsep}}{{{tabcolsep}}}",
           f"\\caption{{{caption}}}\\label{{{label}}}"]
    if fit:
        out.append(f"\\begin{{adjustbox}}{{max width={width}}}")
    out += [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule"]
    if pre_header:
        out.append(pre_header)
    out.append(" & ".join(header) + r" \\")
    if units:
        out.append(" & ".join(units) + r" \\")
    out.append("\\midrule")
    for r in rows:
        if r is None:
            out.append("\\midrule")
        elif isinstance(r, str):
            out.append(r)
        else:
            out.append(" & ".join(_signfix(c) for c in r) + r" \\")
    out += ["\\bottomrule", "\\end{tabular}"]
    if fit:
        out.append("\\end{adjustbox}")
    if notes:
        out.append(f"\n\\par\\vspace{{3pt}}\\parbox{{\\linewidth}}{{\\footnotesize {notes}}}")
    out.append(f"\\end{{{env}}}")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    gen = os.path.join(root, "manuscript", "generated")
    figs = os.path.join(root, "manuscript", "figures")
    os.makedirs(gen, exist_ok=True)
    os.makedirs(figs, exist_ok=True)

    D = load(root)
    cells, units, outcomes = D["cells"], D["units"], D["outcomes"]
    seen, problems = check_manifest(D["manifest"])
    if problems:
        raise RuntimeError('Invalid condition metadata: ' + '; '.join(problems))
    idx = {(r["phase"], r["scenario"], r["dataset"], r["method"]): r for r in cells}
    derived = {"manifest_checks": problems, "scenarios_in_manifest": len(seen)}

    # ---------------- coverage / failure accounting ----------------
    oc = defaultdict(int)
    for r in outcomes:
        oc[r["outcome"]] += 1
    derived["planned_units"] = len(outcomes)
    derived["valid_units"] = oc.get("valid", 0)
    derived["failed_units"] = sum(v for k, v in oc.items() if k != "valid")
    derived["outcome_counts"] = dict(oc)

    # ================= T1: benign specificity benchmark =================
    t1_rows = []
    order = UNDEFENDED + NONREJECTORS + REJECTORS
    for m in order:
        row = [METHOD_LABEL[m]]
        for sid in ["1.1", "6.1", "6.2"]:
            for d in DS_ORDER:
                if d == "cifar10" and sid == "1.1":
                    continue
                r = idx.get(("main", sid, d, m))
                row.append("--" if r is None else pct(pf(r["fpr_mean"]), 1))
        t1_rows.append(row)
    hdr = ["Rule"] + [f"{DS_LABEL[d]}" for d in DS_ORDER[:3]] \
                   + [f"{DS_LABEL[d]}" for d in DS_ORDER] \
                   + [f"{DS_LABEL[d]}" for d in DS_ORDER]
    sub = (r"& \multicolumn{3}{c}{$\alpha=0.5$} & \multicolumn{4}{c}{$\alpha=0.1$}"
           r" & \multicolumn{4}{c}{$\alpha=0.01$} \\")
    t1 = tex_table(
        caption=r"Benign Exclusion Rate (BER, \%) Without Adversaries",
        label="tab:ber", header=hdr, rows=t1_rows,
        colspec="l" + "r" * 11,
        notes=(r"Honest client--round submissions rejected with no adversary present; three "
               r"seeds, 30 rounds and 90 participants per round (8{,}100 honest client--rounds "
               r"per cell). Fashion denotes Fashion-MNIST. CIFAR-10 has no $\alpha=0.5$ block; "
               r"dashes mark conditions outside the planned coverage. "
               r"Multi-Krum's BER is $1-m/n=29/90=32.22\%$ in every cell, independent of dataset "
               r"and of $\alpha$ (Corollary~\ref{cor:cardinality}). FLAME's clean upper bound is "
               r"$1-(\lfloor n/2\rfloor+1)/n=44/90=48.89\%$ (Corollary~\ref{cor:majority}). "
               r"FLTrust counts zero-weight submissions, not a separate rejection stage. "
               r"Norm clipping and the coordinate-wise median emit no per-client rejection, so "
               r"BER${}=0$ for them by construction and their benign cost appears in "
               r"Table~\ref{tab:buc} instead."),
        star=True)
    t1 = t1.replace("\\toprule\n" + " & ".join(hdr) + r" \\",
                    "\\toprule\n" + sub + "\n\\cmidrule(lr){2-4}\\cmidrule(lr){5-8}\\cmidrule(lr){9-12}\n"
                    + " & ".join(hdr) + r" \\")
    open(os.path.join(gen, "ber.tex"), "w", encoding="utf-8").write(t1)

    # structural prediction checks
    mk = [pf(idx[k]["fpr_mean"]) for k in idx
          if k[0] == "main" and k[3] == "krum_bound30" and k[1] in BENIGN]
    derived["multikrum_predicted_ber"] = (N_PARTICIPANTS - MULTIKRUM_M) / N_PARTICIPANTS
    derived["multikrum_observed_ber"] = {"min": min(mk), "max": max(mk), "n_cells": len(mk)}
    fl = {k[1] + "/" + k[2]: pf(idx[k]["fpr_mean"]) for k in idx
          if k[0] == "main" and k[3] == "flame_hdbscan" and k[1] in BENIGN}
    derived["flame_ceiling_ber"] = (N_PARTICIPANTS - FLAME_MIN_CLUSTER) / N_PARTICIPANTS
    derived["flame_observed_ber"] = fl
    derived["flame_implied_cluster_size"] = {
        k: round(N_PARTICIPANTS * (1 - v), 3) for k, v in fl.items()}

    # ================= T2: benign utility cost =================
    t2_rows = []
    for m in NONREJECTORS + REJECTORS:
        row = [METHOD_LABEL[m]]
        for sid in ["1.1", "6.1", "6.2"]:
            for d in DS_ORDER:
                if d == "cifar10" and sid == "1.1":
                    continue
                b = idx.get(("main", sid, d, "fedavg"))
                r = idx.get(("main", sid, d, m))
                if b is None or r is None or pf(b["accuracy_mean"]) is None or pf(r["accuracy_mean"]) is None:
                    row.append("--")
                else:
                    row.append(f"{100 * (pf(b['accuracy_mean']) - pf(r['accuracy_mean'])):+.1f}")
        t2_rows.append(row)
    t2 = tex_table(
        caption=r"Benign Utility Cost (BUC, Percentage Points) Without Adversaries",
        label="tab:buc", header=hdr, rows=t2_rows, colspec="l" + "r" * 11,
        notes=(r"Final-round accuracy of the undefended uniform mean minus that of the defense, "
               r"in the same adversary-free runs as Table~\ref{tab:ber}; positive values denote "
               r"lower final accuracy than the uniform mean, and entries that round to zero are "
               r"printed without sign. "
               r"Descriptive means over three seeds. Per-seed paired differences are supplied in "
               r"the artifact; summary ranges appear in the supplement. No significance claim "
               r"is attached to any single entry."),
        star=True)
    t2 = t2.replace("\\toprule\n" + " & ".join(hdr) + r" \\",
                    "\\toprule\n" + sub + "\n\\cmidrule(lr){2-4}\\cmidrule(lr){5-8}\\cmidrule(lr){9-12}\n"
                    + " & ".join(hdr) + r" \\")
    open(os.path.join(gen, "buc.tex"), "w", encoding="utf-8").write(t2)

    buc = {}
    for sid in BENIGN:
        vals = []
        for d in DS_ORDER:
            for m in NONREJECTORS + REJECTORS:
                b, r = idx.get(("main", sid, d, "fedavg")), idx.get(("main", sid, d, m))
                if b and r and pf(b["accuracy_mean"]) is not None and pf(r["accuracy_mean"]) is not None:
                    vals.append(100 * (pf(b["accuracy_mean"]) - pf(r["accuracy_mean"])))
        buc[str(BENIGN[sid])] = {"mean": round(st.mean(vals), 2),
                                 "max": round(max(vals), 2), "n": len(vals)}
    derived["benign_utility_cost_by_alpha"] = buc

    # ================= T3: descriptive attack-family comparison =================
    fam_stats = defaultdict(list)
    fam_meth = defaultdict(list)
    for r in cells:
        if r["phase"] != "main":
            continue
        fam = FAMILY.get(r["scenario"])
        if fam is None or r["method"] not in REJECTORS:
            continue
        tpr, fpr = pf(r["tpr_mean"]), pf(r["fpr_mean"])
        if tpr is None or fpr is None:
            continue
        b = idx.get(("main", r["scenario"], r["dataset"], "fedavg"))
        ben = None
        if b and pf(b["accuracy_mean"]) is not None and pf(r["accuracy_mean"]) is not None:
            ben = 100 * (pf(r["accuracy_mean"]) - pf(b["accuracy_mean"]))
        fam_stats[fam].append((100 * tpr, 100 * fpr, 100 * (tpr - fpr), ben))
        fam_meth[(fam, r["method"])].append((100 * tpr, 100 * fpr, 100 * (tpr - fpr), ben))

    t3_rows = []
    for fam in FAMILY_ORDER:
        v = fam_stats[fam]
        if not v:
            continue
        bs = [x[3] for x in v if x[3] is not None]
        t3_rows.append([FAMILY_LABEL[fam], str(len(v)),
                        f"{st.mean(x[0] for x in v):.1f}",
                        f"{st.mean(x[1] for x in v):.1f}",
                        f"{st.mean(x[2] for x in v):+.1f}",
                        f"{st.mean(bs):+.1f}"])
    t3 = tex_table(
        caption=r"Client-Level Discrimination by Attack Family",
        label="tab:discrimination",
        header=["Attacker family", "Cells", "TPR", "FPR", r"$J$", "Benefit"],
        units=["", "", r"(\%)", r"(\%)", "(pp)", "(pp)"],
        rows=t3_rows, colspec="lrrrrr",
        notes=(r"$J=\mathrm{TPR}-\mathrm{FPR}$ is Youden's index: $J>0$ lies above the chance "
               r"diagonal, and $J<0$ means honest clients are rejected in preference to "
               r"attackers. Benefit is defense accuracy minus undefended accuracy in the same "
               r"condition. Each row pools rule~$\times$~dataset~$\times$~condition cells of "
               r"the four rejecting rules; cells are not independent replicates. "
               r"Family coverage differs in dataset, concentration and adversary ratio. Radial "
               r"displacement is not measured by this summary. FLTrust uses zero-weight decisions. "
               r"These are descriptive averages, not a controlled displacement experiment."))
    open(os.path.join(gen, "discrimination.tex"), "w", encoding="utf-8").write(t3)

    # per-method breakdown
    t4_rows = []
    for fam in FAMILY_ORDER:
        if t4_rows:
            t4_rows.append("\\addlinespace[3pt]")
        t4_rows.append(f"\\multicolumn{{6}}{{l}}{{\\emph{{{FAMILY_LABEL[fam]}}}}} \\\\")
        for m in REJECTORS:
            v = fam_meth.get((fam, m))
            if not v:
                continue
            bs = [x[3] for x in v if x[3] is not None]
            t4_rows.append([r"\quad " + METHOD_LABEL[m], str(len(v)),
                            f"{st.mean(x[0] for x in v):.1f}",
                            f"{st.mean(x[1] for x in v):.1f}",
                            f"{st.mean(x[2] for x in v):+.1f}",
                            f"{st.mean(bs):+.1f}" if bs else "--"])
    t4 = tex_table(
        caption=r"Discrimination by Rule and Attack Family",
        label="tab:discrimination_method",
        header=["Attack family / rule", "Cells", "TPR", "FPR", r"$J$", "Benefit"],
        units=["", "", r"(\%)", r"(\%)", "(pp)", "(pp)"],
        rows=t4_rows, colspec="lrrrrr",
        notes=(r"Means over available cells; columns as in Table~\ref{tab:discrimination}. "
               r"FLTrust has a positive mean $J$ for the constrained family in this panel; its "
               r"counts concern zero weights. This does not establish a general distinction "
               r"between defense classes."))
    open(os.path.join(gen, "discrimination_method.tex"), "w", encoding="utf-8").write(t4)

    derived["family_summary"] = {
        fam: {"cells": len(v),
              "tpr": round(st.mean(x[0] for x in v), 2),
              "fpr": round(st.mean(x[1] for x in v), 2),
              "J": round(st.mean(x[2] for x in v), 2),
              "benefit_pp": round(st.mean([x[3] for x in v if x[3] is not None]), 2)}
        for fam, v in fam_stats.items()}
    derived["family_method_J"] = {
        f"{fam}|{m}": round(st.mean(x[2] for x in v), 2) for (fam, m), v in fam_meth.items()}

    # ========= T4b: constrained-adversary operating points vs prediction =========
    n_adv = int(round(0.3 * N_PARTICIPANTS))          # 27 configured attackers
    n_hon = N_PARTICIPANTS - n_adv                    # 63 honest participants
    pred_krum = (N_PARTICIPANTS - MULTIKRUM_M) / n_hon
    pred_flame = (N_PARTICIPANTS - FLAME_MIN_CLUSTER) / n_hon
    cons_rows, exact = [], 0
    # Restrict to the two rules whose admission arithmetic yields a numerical
    # prediction; FLTrust and the composite appear in Table~\ref{tab:discrimination_method}.
    PREDICTED = ["krum_bound30", "flame_hdbscan"]
    for sid in ["7.1", "7.2"]:
        if cons_rows:
            cons_rows.append("\\addlinespace[3pt]")
        cons_rows.append(f"\\multicolumn{{6}}{{l}}{{\\emph{{$\\alpha={ALPHA[sid]}$}}}} \\\\")
        for d in DS_ORDER:
            for m in PREDICTED:
                r = idx.get(("main", sid, d, m))
                if r is None:
                    continue
                tpr, fpr = pf(r["tpr_mean"]), pf(r["fpr_mean"])
                if tpr is None or fpr is None:
                    continue
                pred = {"krum_bound30": f"{100*pred_krum:.2f}",
                        "flame_hdbscan": f"$\\leq{100*pred_flame:.2f}$"}.get(m, "--")
                if m == "krum_bound30" and abs(fpr - pred_krum) < 5e-4 and tpr == 0:
                    exact += 1
                cons_rows.append([r"\quad " + DS_LABEL[d], METHOD_LABEL[m],
                                  f"{100*tpr:.2f}", f"{100*fpr:.2f}",
                                  f"{100*(tpr-fpr):+.2f}", pred])
    t4b = tex_table(
        caption=r"Operating Points Under the Constrained Omniscient Adversary",
        label="tab:constrained",
        header=["Dataset", "Rule", "TPR", "FPR", r"$J$", "Predicted"],
        units=["", "", r"(\%)", r"(\%)", "(pp)", r"FPR (\%)"],
        rows=cons_rows, colspec="llrrrr",
        notes=(r"Thirty percent adversaries: 63 honest and 27 adversarial participants per "
               r"round. Only the two rules whose admission arithmetic yields a numerical "
               r"prediction are listed; FLTrust and Fed-MDBSCAN-G appear in "
               r"Table~\ref{tab:discrimination_method}. Predicted FPR is the value at zero "
               r"attacker recall ($\mathrm{TPR}=0$): the cardinality identity for Multi-Krum "
               r"and an upper bound for FLAME (Corollaries~\ref{cor:cardinality}--\ref{cor:majority}). "
               rf"Multi-Krum discards $n-m=29$ of 90 submissions every round. In {exact} of the "
               rf"six cells it records $\mathrm{{TPR}}=0$ with exactly $2{{,}}610=29\times90$ "
               rf"honest rejections, i.e. $\mathrm{{FPR}}=29/63={100*pred_krum:.2f}\%$: every "
               r"discarded submission is honest. Each cell has 90 recorded rounds except "
               r"CIFAR-10/FLAME/$\alpha=0.1$, which has 60 from two completed seeds and one "
               r"retained failure. The conditional identity does not apply to the positive-TPR rows."))
    open(os.path.join(gen, "constrained.tex"), "w", encoding="utf-8").write(t4b)
    derived["constrained_prediction"] = {
        "multikrum_predicted_fpr": round(100 * pred_krum, 3),
        "multikrum_exact_cells": exact,
        "flame_predicted_fpr_ceiling": round(100 * pred_flame, 3)}

    # ================= T5: benign alarm rate =================
    alarm_rows = []
    for sid in ["1.1", "6.1", "6.2"]:
        for d in DS_ORDER:
            us = [u for u in units if u["phase"] == "main" and u["scenario"] == sid
                  and u["dataset"] == d and u["method"] == "fed_mdbscan_g"]
            if not us:
                continue
            fp = sum(int(u["alert_fp"] or 0) for u in us)
            tn = sum(int(u["alert_tn"] or 0) for u in us)
            if fp + tn == 0:
                continue
            acc = idx.get(("main", sid, d, "fed_mdbscan_g"))
            alarm_rows.append([f"{BENIGN[sid]}", DS_LABEL[d], f"{fp}/{fp+tn}",
                               f"{100*fp/(fp+tn):.1f}",
                               pct(pf(acc["fpr_mean"]), 2) if acc else "--"])
    t5 = tex_table(
        caption=r"Benign Round-Level Alarm Rate of Fed-MDBSCAN-G",
        label="tab:alarm",
        header=[r"$\alpha$", "Dataset", "Alarming rounds", r"Rate (\%)", r"BER (\%)"],
        rows=alarm_rows, colspec="llrrr",
        notes=(r"Fed-MDBSCAN-G is the only evaluated rule that exposes a round-level alarm. "
               r"The denominator is adversary-free rounds; at $\alpha=0.01$ every round on "
               r"every dataset raises an alarm. These counts measure false alarms in clean "
               r"controls, not predictive value at a deployment prevalence. "
               r"The other rules expose no alarm channel; a rate of zero is therefore not "
               r"reported for them, because absence of an alarm mechanism is not alarm "
               r"specificity."))
    open(os.path.join(gen, "alarm.tex"), "w", encoding="utf-8").write(t5)
    derived["benign_alarm"] = {f"{r[0]}|{r[1]}": r[2] for r in alarm_rows}

    # ================= T6: consensus-coverage replay =================
    pol = D["policy"]
    want = [("original", "cutoff_attacked", "scenario_cut_minmax"),
            ("original", "cutoff_attacked", "scenario_cut_backdoor"),
            ("density_only", "cutoff_attacked", "scenario_cut_minmax"),
            ("density_only", "cutoff_attacked", "scenario_cut_backdoor"),
            ("original", "cutoff_clean", "scenario_cut_minmax"),
            ("density_only", "cutoff_clean", "scenario_cut_minmax"),
            ("original", "cutoff_clean", "scenario_cut_backdoor"),
            ("density_only", "cutoff_clean", "scenario_cut_backdoor")]
    GATE = {"original": "As deployed", "density_only": "Density-only"}
    COND = {"cutoff_attacked": "attacked", "cutoff_clean": "attack-disabled control"}
    SCEN = {"scenario_cut_minmax": "Min-Max", "scenario_cut_backdoor": "Patch"}
    prow = {(r["gate"], r["condition"], r["scenario"], r["policy"]): r
            for r in pol if r["scope"] == "gate_v2"}
    t6_rows = []
    GROUP = {"cutoff_attacked": "Attacked matrices", "cutoff_clean": "Attack-disabled controls"}
    last = None
    for g, c, s in want:
        if c != last:
            if last is not None:
                t6_rows.append("\\addlinespace[3pt]")
            t6_rows.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{GROUP[c]}}}}} \\\\")
            last = c
        cellrow = [r"\quad " + GATE[g], SCEN[s]]
        for p in ["P0", "P1", "P2"]:
            r = prow.get((g, c, s, p))
            cellrow.append("--" if r is None else f"{r['final_fp']}/{r['final_tp']}")
        t6_rows.append(cellrow)
    # all four 18-matrix blocks are shown under both gates (72 distinct matrices)
    assert sum(int(prow[(g, c, s, "P0")]["cells"]) for g, c, s in want if g == "original") == 72
    valve = prow[("density_only", "cutoff_attacked", "scenario_cut_minmax", "P2")]
    assert (int(valve["valves"]), int(valve["pre_fp"]), int(valve["final_fp"])) == (18, 1296, 0)
    t6 = tex_table(
        caption=r"Consensus-Test Coverage Replay on 72 Recorded Update Matrices",
        label="tab:coverage_replay",
        header=["Gate", "Attack", "P0", "P1", "P2"],
        rows=t6_rows, colspec="llrrr",
        notes=(r"Cluster structure, geometry and activation memory are held fixed. Entries are "
               r"honest/attacker rejections as client--checkpoint counts. P0 is the deployed "
               r"policy (clusters only); P1 also submits unclustered low-density updates to the "
               r"same test as singletons; P2 excludes them outright. Widening coverage adds "
               r"honest rejections and, except in one block, no attacker rejections. "
               r"Each attacked block contains 1{,}296 honest and 324 attacker observations; each "
               r"attack-disabled block contains 1{,}620 honest observations. The one block that "
               r"does yield attacker rejections (P2, density-only gate, patch) reaches "
               r"$\mathrm{TPR}=46/324=14.20\%$ at $\mathrm{FPR}=142/1296=10.96\%$, i.e. "
               r"$J=+3.2$~pp; its attack-disabled control records 82 honest rejections under the "
               r"same policy. Counts are after the safety valve: under the density-only gate, P2 "
               r"would exclude all 1{,}296 honest Min-Max observations, and the valve restores "
               r"$B_0$ in all 18 of those matrices. These are fixed-matrix decision counts; no "
               r"accuracy or attack success rate is re-measured."))
    open(os.path.join(gen, "coverage_replay.tex"), "w", encoding="utf-8").write(t6)

    r = prow.get(("density_only", "cutoff_attacked", "scenario_cut_backdoor", "P2"))
    if r:
        tp, fp = int(r["final_tp"]), int(r["final_fp"])
        hc, mc = int(r["honest_count"]), int(r["malicious_count"])
        derived["p2_patch_density_only"] = {
            "TPR_pct": round(100 * tp / mc, 2), "FPR_pct": round(100 * fp / hc, 2),
            "J_pp": round(100 * (tp / mc - fp / hc), 2)}

    # ================= T7: recovered-cluster radial ratios =================
    cl = D["clusters"]
    t7_rows = []
    for row in cl:
        # threshold is tau*R0 as recorded by the replay; the test rejects when ratio > 1.
        dist, thr, ratio = float(row["distance"]), float(row["threshold"]), float(row["ratio"])
        assert abs(ratio - dist / thr) < 1e-9 * max(1.0, ratio)
        assert (row["accepted"].lower() == "true") == (dist <= thr)
        t7_rows.append([row["arm"], row["cluster"], row["size"], row["l0_size"],
                        f"{float(row['ratio']):.2f}",
                        "accept" if row["accepted"].lower() == "true" else "reject"])
    t7 = tex_table(
        caption=r"Recovered Clusters at an Adversary-Free MNIST Checkpoint",
        label="tab:cluster_ratios",
        header=["Arm", "Cluster", "Size", r"In $B_0$", "Ratio", "Decision"],
        rows=t7_rows, colspec="llrrrl",
        notes=(r"Seed 2024, round 9. Mini-batch regimes: A, standard loader with batch size 32; "
               r"B, a fresh 20-example subset at each local step; C, the first 20-example batch "
               r"repeated five times. Ratio is "
               r"$\lVert c_S-m_{B_0}\rVert/(\tau R_0)$ with $\tau=2$ and $R_0$ from "
               r"\eqref{eq:consensus}, so a group is rejected when the ratio exceeds 1; the "
               r"decision column is the implementation's own output. Every client is honest. "
               r"The majority cluster lies at $0.12$--$0.13$ of the rejection radius and every "
               r"honest minority cluster at $1.70$--$2.63$ times it. The rejection radius "
               r"therefore separates honest groups from one another."))
    open(os.path.join(gen, "cluster_ratios.tex"), "w", encoding="utf-8").write(t7)
    ratios = [float(x["ratio"]) for x in cl]
    derived["cluster_ratio_range"] = {"min": min(ratios), "max": max(ratios),
                                      "majority_max": max(float(x["ratio"]) for x in cl
                                                          if x["accepted"].lower() == "true")}

    # ================= T8: backdoor block =================
    bd_rows = []
    for sid in ["8.1", "8.2"]:
        for d in ["mnist", "fashion_mnist", "cifar10"]:
            a = idx.get(("main", sid, d, "fed_mdbscan_g"))
            c = idx.get(("clean", sid, d, "fed_mdbscan_g"))
            if a is None:
                continue
            bd_rows.append([f"{ALPHA[sid]}", DS_LABEL[d],
                            pct(pf(a["accuracy_mean"]), 2),
                            pct(pf(a["backdoor_asr_mean"]), 2),
                            pct(pf(c["accuracy_mean"]), 2) if c else "--",
                            pct(pf(c["backdoor_asr_mean"]), 2) if c else "--"])
    t8 = tex_table(
        caption=r"Patch-Backdoor Results of Fed-MDBSCAN-G With Matched Controls",
        label="tab:backdoor",
        pre_header=(r"& & \multicolumn{2}{c}{Attacked} & \multicolumn{2}{c}{Attack disabled} \\"
                    "\n" r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}"),
        header=[r"$\alpha$", "Dataset", r"Acc. (\%)", r"ASR (\%)", r"Acc. (\%)", r"ASR (\%)"],
        rows=bd_rows, colspec="llrrrr",
        notes=(r"ASR is the triggered non-target attack success rate. Accuracy and ASR are "
               r"reported together; the low-accuracy $\alpha=0.01$ block should not be read as "
               r"effective protection."))
    open(os.path.join(gen, "backdoor.tex"), "w", encoding="utf-8").write(t8)

    # ================= T9: ablation (upper layers) =================
    abl_order = ["mdbg_l0_only", "fed_g2l_25", "mdbg_no_momentum", "mdbg_no_valve",
                 "mdbg_rtr15", "mdbg_rtr20", "mdbg_rtr30"]
    diffs = defaultdict(list)
    for r in cells:
        if r["phase"] != "ablation" or r["method"] not in abl_order:
            continue
        # the full-method reference for these conditions lives in the main block
        full = idx.get(("main", r["scenario"], r["dataset"], "fed_mdbscan_g"))
        if full is None or pf(full["accuracy_mean"]) is None or pf(r["accuracy_mean"]) is None:
            continue
        diffs[r["method"]].append(100 * (pf(r["accuracy_mean"]) - pf(full["accuracy_mean"])))
    abl_rows = []
    for m in abl_order:
        v = diffs.get(m)
        if not v:
            continue
        abl_rows.append([METHOD_LABEL[m], str(len(v)), f"{st.mean(v):+.3f}",
                         f"{min(v):+.2f}", f"{max(v):+.2f}"])
    t9 = tex_table(
        caption=r"Endpoint Ablations: Variant Minus Full Final Accuracy (Percentage Points)",
        label="tab:ablation",
        header=["Variant", "Cells", "Mean", "Min.", "Max."], rows=abl_rows, colspec="lrrrr",
        notes=(r"Matched ablation block. Ranges describe heterogeneity across conditions, not "
               r"confidence intervals. Removing every layer above the stage-1 acceptance region "
               r"changes the mean by less than a tenth of a percentage point. "
               r"Cells are dataset~$\times$~condition means over three seeds; the manuscript makes "
               r"no equivalence claim from a small mean difference."))
    open(os.path.join(gen, "ablation.tex"), "w", encoding="utf-8").write(t9)
    derived["ablation_mean_diff"] = {m: round(st.mean(v), 4) for m, v in diffs.items()}

    # ================= coverage table =================
    ph = defaultdict(int)
    for r in outcomes:
        ph[r["phase"]] += 1
    PHASE_LABEL = {
        "main": "Main matrix (attacked and adversary-free)",
        "clean": "Matched attack-disabled controls",
        "oracle": "Oracle diagnostics",
        "ablation": "Ablation variants",
        "temporal": "Onset/offset timing",
        "preserve_empty": "Alternative partition policy",
        "fixed_steps": "Fixed local-step control",
    }
    cov_rows = [[PHASE_LABEL.get(p, p.replace("_", r"\_")), str(n)]
                for p, n in sorted(ph.items(), key=lambda kv: -kv[1])]
    cov_rows.append(["Total planned", str(len(outcomes))])
    t10 = tex_table(
        caption=r"Planned Evaluation Coverage by Block",
        label="tab:coverage", header=["Block", "Units"], rows=cov_rows, colspec="lr",
        notes=(r"A unit is one rule--condition--seed run. "
               f"Of {len(outcomes)} planned units, {oc.get('valid',0)} completed and "
               f"{sum(v for k,v in oc.items() if k!='valid')} are retained as failures rather "
               r"than imputed or re-seeded. The blocks are not a balanced full factorial."))
    open(os.path.join(gen, "coverage.tex"), "w", encoding="utf-8").write(t10)

    # ================= figure: J by categorical attack family =================
    try:
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(3.4, 2.5))
        marks = {"krum_bound30": "o", "fltrust_normalized": "s",
                 "flame_hdbscan": "^", "fed_mdbscan_g": "D"}
        xs = range(len(FAMILY_ORDER))
        for m in REJECTORS:
            ys, xx = [], []
            for i, fam in enumerate(FAMILY_ORDER):
                v = fam_meth.get((fam, m))
                if not v:
                    continue
                xx.append(i)
                ys.append(st.mean(x[2] for x in v))
            ax.plot(xx, ys, marker=marks[m], ms=4, linestyle='none',
                    label=METHOD_LABEL[m].replace(" (full)", ""))
        ax.axhline(0, color="0.3", lw=0.8, ls="--")
        ax.set_xticks(list(xs))
        ax.set_xticklabels(["loud", "flip", "patch", "bounded", "constr."], fontsize=7)
        ax.set_xlabel("configured attack family (uneven coverage)", fontsize=7)
        ax.set_ylabel(r"$J=\mathrm{TPR}-\mathrm{FPR}$ (pp)", fontsize=7)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=5.6, frameon=False, loc="lower left")
        ax.grid(alpha=0.25, lw=0.5)
        fig.tight_layout(pad=0.3)
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(figs, f"discrimination.{ext}"), dpi=300)
        plt.close(fig)

        # BER vs alpha
        fig, ax = plt.subplots(figsize=(3.4, 2.5))
        alphas = [0.5, 0.1, 0.01]
        sids = ["1.1", "6.1", "6.2"]
        for m in REJECTORS:
            ys, xx = [], []
            for a, sid in zip(alphas, sids):
                vals = [pf(idx[("main", sid, d, m)]["fpr_mean"]) for d in DS_ORDER
                        if ("main", sid, d, m) in idx
                        and pf(idx[("main", sid, d, m)]["fpr_mean"]) is not None]
                if not vals:
                    continue
                xx.append(a)
                ys.append(100 * st.mean(vals))
            ax.plot(xx, ys, marker=marks[m], ms=4, lw=1.1,
                    label=METHOD_LABEL[m].replace(" (full)", ""))
        ax.set_xscale("log")
        ax.invert_xaxis()
        ax.set_xlabel(r"Dirichlet $\alpha$ (adversary-free)", fontsize=7)
        ax.set_ylabel("benign exclusion rate (%)", fontsize=7)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=5.6, frameon=False, loc="lower right")
        ax.grid(alpha=0.25, lw=0.5)
        fig.tight_layout(pad=0.3)
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(figs, f"ber_vs_alpha.{ext}"), dpi=300)
        plt.close(fig)
        derived["figures"] = ["discrimination", "ber_vs_alpha"]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError('Figure generation failed') from exc

    from build_checks import build
    build(root, tex_table, derived)
    with open(os.path.join(root, "analysis", "derived_values.json"), "w", encoding="utf-8") as fh:
        json.dump(derived, fh, indent=2, sort_keys=True)

    print(json.dumps(derived, indent=2, sort_keys=True))
    if problems:
        print("\nMANIFEST CHECK PROBLEMS:")
        for p in problems:
            print("  -", p)
    else:
        print("\nManifest check: condition alpha and adversary-ratio metadata agree.")


if __name__ == "__main__":
    main()
