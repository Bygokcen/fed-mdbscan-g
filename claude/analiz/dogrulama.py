"""Bagimsiz dogrulama ve ek analiz — Fed-MDBSCAN-G / TIFS.

Salt okunur. Kanonik arsivi ve dondurulmus kaynagi degistirmez.

Girdi olarak yalnizca Git'te izlenen kanit dosyalarini kullanir:
    tifs_submission/evidence/*.csv, scenario_manifest.json
    analysis/clean_geometry_20260913/quartiles.csv   (optimizer adim sayilari icin)

Cikti: claude/analiz/ciktilar/ altinda CSV + JSON.

Calistirma:
    cd /home/gokcen/Fed_MDBSCAN_TIFS && .venv/bin/python claude/analiz/dogrulama.py

NOT — istatistiksel yorum siniri: kampanya 3 seed icerir ve ayni kosum
icindeki turlar/istemciler bagimsiz degildir. Asagida raporlanan Spearman
katsayilari ve p degerleri BETIMSEL etki buyuklugudur; hipotez testi olarak
kullanilamaz. Bu, AGENTS.md'deki "temelsiz anlamlilik cikarma" kuralina uyar.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "tifs_submission/evidence"
OUT = Path(__file__).resolve().parent / "ciktilar"
OUT.mkdir(parents=True, exist_ok=True)

REJECTING = ["fed_mdbscan_g", "flame_hdbscan", "krum_bound30", "fltrust_normalized"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    """Kanit tablolarini oku ve senaryo meta verisini birlestir."""
    units = pd.read_csv(EV / "units.csv")
    groups = pd.read_csv(EV / "benign_groups.csv")
    outcomes = pd.read_csv(EV / "outcomes.csv")
    deltas = pd.read_csv(EV / "paired_deltas.csv")
    manifest = json.loads((EV / "scenario_manifest.json").read_text())

    rows = []
    for job in manifest:
        s = job["scenario"]
        rows.append(
            dict(
                phase=job["phase"],
                dataset=job["dataset"],
                scenario=str(s["id"]),
                alpha=s.get("alpha"),
                attack=s.get("attack_type"),
                mal=s.get("malicious_ratio"),
                label=s.get("label"),
            )
        )
    scen = pd.DataFrame(rows).drop_duplicates(subset=["phase", "dataset", "scenario"])

    for df in (units, groups, deltas):
        df["scenario"] = df["scenario"].astype(str)
    groups["phase"] = groups["job"].str.split("/").str[0]

    units = units.merge(scen, on=["phase", "dataset", "scenario"], how="left")
    groups = groups.merge(scen, on=["phase", "dataset", "scenario"], how="left")
    groups["kind"] = groups["group"].str.split(":").str[0]
    groups["lvl"] = groups["group"].str.split(":").str[1]
    return units, groups, outcomes, deltas


def pooled_fpr(d: pd.DataFrame) -> float:
    denom = d.fp.sum() + d.tn.sum()
    return float(d.fp.sum() / denom) if denom else float("nan")


# ----------------------------------------------------------------------
# K1 — kapsam ve basarisizlik muhasebesi
# ----------------------------------------------------------------------
def k1_kapsam(units, outcomes):
    vc = outcomes.outcome.value_counts().to_dict()
    failed = outcomes[outcomes.outcome != "valid"]
    return dict(
        planlanan_birim=int(len(outcomes)),
        gecerli=int(vc.get("valid", 0)),
        basarisiz=int(vc.get("failed", 0)),
        units_csv_satiri=int(len(units)),
        makale_iddiasi_2125_5=bool(vc.get("valid") == 2125 and vc.get("failed") == 5),
        basarisizlar=failed[
            ["dataset", "scenario", "method", "seed", "reason"]
        ].to_dict("records"),
    )


# ----------------------------------------------------------------------
# K2 — fed_g2l_25 ile mdbg_l0_only ayni tahmin ediciyi mi calistiriyor?
# ----------------------------------------------------------------------
def k2_baseline_tekrari(units):
    ab = units[units.phase == "ablation"]
    key = ["dataset", "scenario", "seed"]
    a = ab[ab.method == "fed_g2l_25"].set_index(key).sort_index()
    b = ab[ab.method == "mdbg_l0_only"].set_index(key).sort_index()
    cols = ["accuracy", "balanced_accuracy", "fp", "tn", "tp", "fn", "fpr", "fallback_rounds"]
    ayni = {c: bool(np.array_equal(a[c].values, b[c].values)) for c in cols}
    return dict(
        eslesen_uc_nokta=int(len(a)),
        indeks_ayni=bool(a.index.equals(b.index)),
        alanlar_ayni=ayni,
        hepsi_ayni=bool(all(ayni.values())),
        max_mutlak_dogruluk_farki=float((a.accuracy - b.accuracy).abs().max()),
        not_="Alarm sayaclari (alert_fp/alert_tn) farklidir: l0_only alarmi hesaplayip "
        "kaydeder, fed_g2l_25 kaydetmez. Filtreleme kararlari ozdestir.",
    )


# ----------------------------------------------------------------------
# K3 — ayirt etme gucu: J = TPR - FPR
# ----------------------------------------------------------------------
def k3_ayirt_etme(units):
    f = units[
        (units.method == "fed_mdbscan_g") & (units.phase == "main") & (units.mal > 0)
    ].copy()
    f["J"] = f.tpr - f.fpr

    tablo = (
        f.groupby(["attack", "alpha"])
        .agg(
            n=("seed", "size"),
            TPR=("tpr", "mean"),
            FPR=("fpr", "mean"),
            J=("J", "mean"),
            J_min=("J", "min"),
            J_max=("J", "max"),
            alarm_recall=("alert_recall", "mean"),
        )
        .reset_index()
        .round(4)
    )
    tablo.to_csv(OUT / "ayirt_etme_saldiri_ailesi.csv", index=False)

    def havuz(d):
        tp, fp, tn, fn = d.tp.sum(), d.fp.sum(), d.tn.sum(), d.fn.sum()
        tpr = tp / (tp + fn) if (tp + fn) else float("nan")
        fpr = fp / (fp + tn) if (fp + tn) else float("nan")
        return dict(
            TP=int(tp), FP=int(fp), TN=int(tn), FN=int(fn),
            TPR=round(float(tpr), 4), FPR=round(float(fpr), 4),
            precision=round(float(tp / (tp + fp)), 4) if (tp + fp) else None,
            J=round(float(tpr - fpr), 4),
        )

    return dict(
        saldirili_kosum_sayisi=int(len(f)),
        J_sifir_veya_alti=int((f.J <= 0).sum()),
        havuzlanmis_tum_saldirilar=havuz(f),
        havuzlanmis_gurultulu_gaussian_haric=havuz(f[f.attack != "gaussian"]),
        minsum_omniscient_alpha001=dict(
            n=int(len(f[f.attack == "minsum_omniscient"])),
            TPR_hepsi_sifir=bool((f[f.attack == "minsum_omniscient"].tpr == 0).all()),
            FPR_ortalama=round(float(f[f.attack == "minsum_omniscient"].fpr.mean()), 4),
            alarm_recall=round(float(f[f.attack == "minsum_omniscient"].alert_recall.mean()), 4),
        ),
    )


# ----------------------------------------------------------------------
# K4 — alarm ozgullugu: saldirisiz kosullarda alarm orani
# ----------------------------------------------------------------------
def k4_alarm(units):
    f = units[(units.method == "fed_mdbscan_g") & (units.phase == "main") & (units.mal == 0)]
    t = (
        f.groupby(["alpha", "dataset"])
        .agg(
            n=("seed", "size"),
            honest_fpr=("fpr", "mean"),
            alarm_clean_fpr=("alert_clean_fpr", "mean"),
            alarmli_tur=("alert_fp", "sum"),
            sessiz_tur=("alert_tn", "sum"),
        )
        .reset_index()
        .round(4)
    )
    t.to_csv(OUT / "alarm_ozgullugu.csv", index=False)
    return t.to_dict("records")


# ----------------------------------------------------------------------
# K5 — boyut yanliligi: yerel veri hacmine gore ret orani, yontem yontem
# ----------------------------------------------------------------------
def k5_boyut_yanliligi(groups):
    sq = groups[(groups.kind == "size_quartile") & (groups.phase == "main")]
    temiz = sq[sq.mal == 0]

    satir = []
    for m, d in temiz.groupby("method"):
        q = {lvl: pooled_fpr(g) for lvl, g in d.groupby("lvl")}
        rhos = []
        for _, run in d.groupby(["job", "seed"]):
            if run.fpr.nunique() > 1:
                rhos.append(float(spearmanr(run.lvl.astype(int), run.fpr).statistic))
        satir.append(
            dict(
                method=m,
                q0_en_kucuk=round(q.get("0", float("nan")), 4),
                q1=round(q.get("1", float("nan")), 4),
                q2=round(q.get("2", float("nan")), 4),
                q3_en_buyuk=round(q.get("3", float("nan")), 4),
                egim_q3_eksi_q0=round(q.get("3", np.nan) - q.get("0", np.nan), 4),
                kosum_sayisi=len(rhos),
                spearman_ortalama=round(float(np.mean(rhos)), 3) if rhos else None,
                pozitif_kosum=int(sum(r > 0 for r in rhos)) if rhos else 0,
            )
        )
    t = pd.DataFrame(satir).sort_values("egim_q3_eksi_q0", ascending=False)
    t.to_csv(OUT / "boyut_yanliligi_yontem.csv", index=False)

    # Katman atfi: ablation varyantlari ayni egimi gosteriyor mu?
    ab = groups[(groups.kind == "size_quartile") & (groups.phase == "ablation")]
    katman = []
    for m, d in ab.groupby("method"):
        q = {lvl: pooled_fpr(g) for lvl, g in d.groupby("lvl")}
        katman.append(
            dict(
                method=m,
                q0=round(q.get("0", np.nan), 4),
                q3=round(q.get("3", np.nan), 4),
                egim=round(q.get("3", np.nan) - q.get("0", np.nan), 4),
            )
        )
    kt = pd.DataFrame(katman).sort_values("egim", ascending=False)
    kt.to_csv(OUT / "boyut_yanliligi_katman_atfi.csv", index=False)
    return t.to_dict("records"), kt.to_dict("records")


# ----------------------------------------------------------------------
# K6 — mudahale testi: yerel adim sayisi esitlenince yanlilik kayboluyor mu?
# ----------------------------------------------------------------------
def k6_sabit_adim(groups, units):
    sq = groups[(groups.kind == "size_quartile") & (groups.method == "fed_mdbscan_g")]
    satir = []
    for scen in ["3.3", "5.2"]:
        for ds in ["mnist", "fashion_mnist", "har"]:
            rec = dict(dataset=ds, scenario=scen)
            ok = True
            for ph in ["main", "fixed_steps"]:
                d = sq[(sq.phase == ph) & (sq.dataset == ds) & (sq.scenario == scen)]
                if d.empty:
                    ok = False
                    break
                q = {lvl: pooled_fpr(g) for lvl, g in d.groupby("lvl")}
                rec[f"{ph}_fpr"] = round(pooled_fpr(d), 4)
                rec[f"{ph}_egim"] = round(q.get("3", np.nan) - q.get("0", np.nan), 4)
                u = units[
                    (units.phase == ph)
                    & (units.dataset == ds)
                    & (units.scenario == scen)
                    & (units.method == "fed_mdbscan_g")
                ]
                rec[f"{ph}_tpr"] = round(float(u.tpr.mean()), 4)
                rec[f"{ph}_acc"] = round(float(u.accuracy.mean()), 4)
                fa = units[
                    (units.phase == ph)
                    & (units.dataset == ds)
                    & (units.scenario == scen)
                    & (units.method == "fedavg")
                ]
                rec[f"{ph}_fedavg_acc"] = round(float(fa.accuracy.mean()), 4) if len(fa) else None
            if ok:
                satir.append(rec)
    t = pd.DataFrame(satir)
    t.to_csv(OUT / "mudahale_sabit_adim.csv", index=False)
    return t.to_dict("records")


# ----------------------------------------------------------------------
# K7 — mekanizma: optimizer adim sayisi ile ret orani iliskisi
# ----------------------------------------------------------------------
def k7_adim_mekanizmasi():
    p = ROOT / "analysis/clean_geometry_20260913/quartiles.csv"
    if not p.exists():
        return dict(mevcut_degil=str(p))
    q = pd.read_csv(p)
    q["scenario"] = q.scenario.astype(str)
    q["fpr"] = q.fp / (q.fp + q.tn)

    per_scen = {}
    for sc, d in q.groupby("scenario"):
        r = spearmanr(d.steps_sum, d.fpr)
        per_scen[sc] = dict(
            grup=int(len(d)),
            spearman=round(float(r.statistic), 3),
            p_betimsel=float(f"{r.pvalue:.3e}"),
        )

    d = q[q.scenario == "6.2"]
    g = d.groupby("quartile").agg(steps=("steps_sum", "mean"), fp=("fp", "sum"), tn=("tn", "sum"))
    g["fpr"] = (g.fp / (g.fp + g.tn)).round(4)
    g["adim_q0_kati"] = (g.steps / g.steps.min()).round(1)
    g.reset_index().to_csv(OUT / "adim_sayisi_mekanizma.csv", index=False)
    return dict(senaryo_bazli=per_scen, alpha001_ceyrek=g.reset_index().to_dict("records"))


# ----------------------------------------------------------------------
# K8 — backdoor: savunma FedAvg'den farkli bir sey yapiyor mu?
# ----------------------------------------------------------------------
def k8_backdoor(units):
    m = units[(units.scenario == "8.1") & (units.phase == "main")]
    c = units[(units.scenario == "8.1") & (units.phase == "clean")]
    out = []
    for ds in sorted(m.dataset.unique()):
        full = m[(m.dataset == ds) & (m.method == "fed_mdbscan_g")]
        fa = m[(m.dataset == ds) & (m.method == "fedavg")]
        ctl = c[(c.dataset == ds) & (c.method == "fed_mdbscan_g")]
        out.append(
            dict(
                dataset=ds,
                full_asr=round(float(full.backdoor_asr.mean()), 5),
                fedavg_asr=round(float(fa.backdoor_asr.mean()), 5) if len(fa) else None,
                kontrol_asr=round(float(ctl.backdoor_asr.mean()), 5) if len(ctl) else None,
                full_acc=round(float(full.accuracy.mean()), 5),
                fedavg_acc=round(float(fa.accuracy.mean()), 5) if len(fa) else None,
                saldirgan_ret_tpr=round(float(full.tpr.mean()), 5),
                alarm_recall=round(float(full.alert_recall.mean()), 5),
            )
        )
    t = pd.DataFrame(out)
    t.to_csv(OUT / "backdoor_81.csv", index=False)
    return t.to_dict("records")


# ----------------------------------------------------------------------
# K9 — ablation ozet dogrulamasi (makale sayilari)
# ----------------------------------------------------------------------
def k9_ablation(deltas):
    ab = deltas[deltas.contrast == "ablation_minus_full"]
    g = (
        ab.groupby("method")
        .accuracy_delta.agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )
    g["ortalama_yuzde_puan"] = (g["mean"] * 100).round(4)
    g.round(6).to_csv(OUT / "ablation_dogrulama.csv", index=False)
    l0 = float(ab[ab.method == "mdbg_l0_only"].accuracy_delta.mean() * -100)
    valve = float(ab[ab.method == "mdbg_no_valve"].accuracy_delta.mean() * 100)
    mom = ab[ab.method == "mdbg_no_momentum"].accuracy_delta
    return dict(
        full_eksi_l0_yuzde_puan=round(l0, 4),
        makale_iddiasi_0_081=bool(abs(l0 - 0.081) < 0.001),
        valve_kaldirma_kazanci_yuzde_puan=round(valve, 4),
        makale_iddiasi_0_278=bool(abs(valve - 0.278) < 0.001),
        momentum_36_uc_noktada_tam_ayni=bool((mom == 0).all() and len(mom) == 36),
    )


def main():
    units, groups, outcomes, deltas = load()
    boyut, katman = k5_boyut_yanliligi(groups)
    rapor = {
        "K1_kapsam": k1_kapsam(units, outcomes),
        "K2_baseline_tekrari": k2_baseline_tekrari(units),
        "K3_ayirt_etme": k3_ayirt_etme(units),
        "K4_alarm_ozgullugu": k4_alarm(units),
        "K5_boyut_yanliligi": boyut,
        "K5b_katman_atfi": katman,
        "K6_mudahale_sabit_adim": k6_sabit_adim(groups, units),
        "K7_adim_mekanizmasi": k7_adim_mekanizmasi(),
        "K8_backdoor": k8_backdoor(units),
        "K9_ablation": k9_ablation(deltas),
    }
    (OUT / "ozet.json").write_text(json.dumps(rapor, indent=2, ensure_ascii=False) + "\n")

    kaynaklar = {}
    for p in sorted(EV.glob("*.csv")) + [EV / "scenario_manifest.json"]:
        kaynaklar[str(p.relative_to(ROOT))] = sha256(p)
    q = ROOT / "analysis/clean_geometry_20260913/quartiles.csv"
    if q.exists():
        kaynaklar[str(q.relative_to(ROOT))] = sha256(q)
    (OUT / "provenance.json").write_text(
        json.dumps(
            {
                "salt_okunur": True,
                "kanonik_arsiv_degistirilmedi": True,
                "girdi_hashleri": kaynaklar,
                "betik_sha256": sha256(Path(__file__)),
                "birim": int(len(units)),
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(rapor, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
