"""Adim kontrolu kampanyasinin degerlendirilmesi — onceden sabitlenen olcutlere gore.

Karsilastirma:
    kanonik 3 epoch  (new_work/results/validated/audit-v2/full_20260910)
    yeni 5 sabit adim (new_work/results/step_control/steps5_20260913)

Salt okunur. Her iki arsivi de degistirmez.

Calistirma:
    cd /home/gokcen/Fed_MDBSCAN_TIFS && .venv/bin/python claude/analiz/adim_kontrolu.py

NOT — 3 seed ve bagimsiz olmayan turlar nedeniyle Spearman katsayilari BETIMSEL
etki buyuklugudur; hipotez testi degildir.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / "new_work/results/step_control/steps5_20260913"
OLD = ROOT / "new_work/results/validated/audit-v2/full_20260910"
OUT = Path(__file__).resolve().parent / "ciktilar"
OUT.mkdir(parents=True, exist_ok=True)

METHODS = ["fed_mdbscan_g", "mdbg_l0_only", "flame_hdbscan",
           "krum_bound30", "fltrust_normalized", "fedavg"]
DATASETS = ["mnist", "fashion_mnist", "har"]
SEEDS = [42, 137, 2024]


def pooled(d: pd.DataFrame) -> float:
    denom = d.fp.sum() + d.tn.sum()
    return float(d.fp.sum() / denom) if denom else float("nan")


def quartile_profile(d: pd.DataFrame) -> dict:
    q = {lvl: pooled(g) for lvl, g in d.groupby("lvl")}
    return dict(q0=q.get("0"), q1=q.get("1"), q2=q.get("2"), q3=q.get("3"),
                gradient=(q.get("3", np.nan) - q.get("0", np.nan)), fpr=pooled(d))


def load_groups():
    new = pd.read_csv(NEW / "report/benign_groups.csv")
    old = pd.read_csv(ROOT / "tifs_submission/evidence/benign_groups.csv")
    for d in (new, old):
        d["scenario"] = d.scenario.astype(str)
        d["kind"] = d.group.str.split(":").str[0]
        d["lvl"] = d.group.str.split(":").str[1]
    old["phase"] = old.job.str.split("/").str[0]
    return new, old


# ----------------------------------------------------------------------
# O1 — boyut egimi: 3 epoch vs 5 sabit adim, temiz kosulda
# ----------------------------------------------------------------------
def o1_boyut_egimi(new_g, old_g):
    rows = []
    for m in METHODS:
        o = old_g[(old_g.method == m) & (old_g.scenario == "6.2")
                  & (old_g.kind == "size_quartile")
                  & (old_g.phase.isin(["main", "ablation"]))]
        n = new_g[(new_g.method == m) & (new_g.scenario == "6.2")
                  & (new_g.kind == "size_quartile")]
        if o.empty or n.empty:
            continue
        a, b = quartile_profile(o), quartile_profile(n)
        rows.append(dict(method=m,
                         ep3_q0=a["q0"], ep3_q3=a["q3"], ep3_gradient=a["gradient"], ep3_fpr=a["fpr"],
                         st5_q0=b["q0"], st5_q3=b["q3"], st5_gradient=b["gradient"], st5_fpr=b["fpr"],
                         gradient_reduction=1 - b["gradient"] / a["gradient"] if a["gradient"] else None,
                         fpr_reduction=1 - b["fpr"] / a["fpr"] if a["fpr"] else None))
    t = pd.DataFrame(rows).round(4)
    t.to_csv(OUT / "adimkontrol_boyut_egimi.csv", index=False)
    return t.to_dict("records")


# ----------------------------------------------------------------------
# O2 — tuzak olcutu: sabit adimda tespit korunuyor mu?
# ----------------------------------------------------------------------
def o2_tuzak():
    new = pd.read_csv(NEW / "report/units.csv")
    old = pd.read_csv(ROOT / "tifs_submission/evidence/units.csv")
    for d in (new, old):
        d["scenario"] = d.scenario.astype(str)
    old = old[old.phase == "main"]
    rows = []
    for m in METHODS:
        for sc in ["6.2", "3.1"]:
            o = old[(old.method == m) & (old.scenario == sc)]
            n = new[(new.method == m) & (new.scenario == sc)]
            if n.empty:
                continue
            rows.append(dict(
                method=m, scenario=sc,
                ep3_tpr=float(o.tpr.mean()) if len(o) else None,
                st5_tpr=float(n.tpr.mean()),
                ep3_fpr=float(o.fpr.mean()) if len(o) else None,
                st5_fpr=float(n.fpr.mean()),
                ep3_acc=float(o.accuracy.mean()) if len(o) else None,
                st5_acc=float(n.accuracy.mean())))
    t = pd.DataFrame(rows).round(4)
    t.to_csv(OUT / "adimkontrol_tuzak.csv", index=False)
    return t.to_dict("records")


# ----------------------------------------------------------------------
# O3 — artik mekanizma: adimlar esitken norm hala veri hacmine mi bagli?
#      (yalnizca yeni kosumda mumkun; kanonik kayitta norm yok)
# ----------------------------------------------------------------------
def o3_artik_mekanizma():
    rows = []
    for seed in SEEDS:
        for ds in DATASETS:
            p = NEW / f"runs/step_control_5/{ds}/scenario_6.2/runs/fed_mdbscan_g_seed{seed}.json"
            if not p.exists():
                continue
            x = json.loads(p.read_text())
            meta = x["run_metadata"]["client_metadata"]
            for r in x["records"]:
                rejected = {str(c) for c in r["rejected_ids"]}
                for cid in (str(c) for c in r["server_input_ids"]):
                    norm = r["update_norms"].get(cid)
                    if norm is None:
                        continue
                    rows.append((ds, meta[cid]["sample_count"],
                                 r["optimizer_steps"][cid], norm, int(cid in rejected)))
    d = pd.DataFrame(rows, columns=["dataset", "samples", "steps", "norm", "rejected"])

    # Bolusum onarimi cogu istemciyi tam olarak tabana yerlestirir; kova analizi
    # tabandaki kutleyi ayri gostermek icin bu sekilde kesilmistir.
    d["bucket"] = pd.cut(d.samples, [0, 20, 50, 150, 500, 10 ** 9],
                         labels=["=20", "21-50", "51-150", "151-500", ">500"])
    buckets = (d.groupby("bucket", observed=True)
               .agg(observations=("samples", "size"), median_samples=("samples", "median"),
                    median_norm=("norm", "median"), rejection=("rejected", "mean"))
               .reset_index().round(4))
    buckets.to_csv(OUT / "adimkontrol_artik_mekanizma.csv", index=False)

    return dict(
        client_round_observations=int(len(d)),
        steps_fully_equalised=bool(d.steps.nunique() == 1),
        step_values=sorted(int(v) for v in d.steps.unique()),
        share_at_repair_floor=round(float((d.samples == 20).mean()), 4),
        spearman_samples_norm=round(float(spearmanr(d.samples, d.norm).statistic), 4),
        spearman_norm_rejected=round(float(spearmanr(d.norm, d.rejected).statistic), 4),
        spearman_samples_rejected=round(float(spearmanr(d.samples, d.rejected).statistic), 4),
        buckets=buckets.to_dict("records"))


# ----------------------------------------------------------------------
# O4 — mudahale gercekten adimlari esitledi mi? (iki rejimin karsilastirmasi)
# ----------------------------------------------------------------------
def o4_adim_dogrulamasi():
    out = {}
    for label, base, phase in [("ep3", OLD, "main"), ("st5", NEW, "step_control_5")]:
        agg = collections.defaultdict(lambda: dict(steps=[], samples=[], fp=0, tn=0))
        for seed in SEEDS:
            for ds in DATASETS:
                p = base / f"runs/{phase}/{ds}/scenario_6.2/runs/fed_mdbscan_g_seed{seed}.json"
                if not p.exists():
                    continue
                x = json.loads(p.read_text())
                meta = x["run_metadata"]["client_metadata"]
                for r in x["records"]:
                    rejected = {str(c) for c in r["rejected_ids"]}
                    for cid in (str(c) for c in r["server_input_ids"]):
                        g = agg[meta[cid]["size_quartile"]]
                        g["steps"].append(r["optimizer_steps"][cid])
                        g["samples"].append(meta[cid]["sample_count"])
                        g["fp" if cid in rejected else "tn"] += 1
        out[label] = [
            dict(quartile=int(q), median_samples=float(np.median(g["samples"])),
                 mean_steps_per_round=round(float(np.mean(g["steps"])), 2),
                 rejection=round(g["fp"] / (g["fp"] + g["tn"]), 4))
            for q, g in sorted(agg.items())]
    rows = []
    for label, recs in out.items():
        for r in recs:
            rows.append(dict(regime=label, **r))
    pd.DataFrame(rows).to_csv(OUT / "adimkontrol_adim_dogrulamasi.csv", index=False)
    return out


def main():
    new_g, old_g = load_groups()
    completeness = json.loads((NEW / "report/completeness.json").read_text())
    report = {
        "kampanya": str(NEW.relative_to(ROOT)),
        "kapsam": dict(valid=completeness["valid_units"],
                       expected=completeness["expected_units"],
                       complete=completeness["complete"],
                       invalid=completeness["invalid"], missing=completeness["missing"]),
        "O1_boyut_egimi": o1_boyut_egimi(new_g, old_g),
        "O2_tuzak_olcutu": o2_tuzak(),
        "O3_artik_mekanizma": o3_artik_mekanizma(),
        "O4_adim_dogrulamasi": o4_adim_dogrulamasi(),
    }
    (OUT / "adimkontrol_ozet.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
