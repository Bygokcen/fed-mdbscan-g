#!/usr/bin/env python3
"""Turkish working-translation tables and figure for manuscript/main_tr.tex.

Reads the English tables written by build_tables.py (manuscript/generated/*.tex),
replaces captions, notes, headers and row labels with Turkish text, and writes
manuscript/generated_tr/*.tex plus figures/ber_vs_alpha_tr.pdf.  Each translated
table must contain the same multiset of digit groups as its English source, so the
numbers cannot drift between the two versions.  Run build_tables.py first.

Run:  python3 analysis/build_tr.py --root .
"""
from __future__ import annotations

import argparse
import os
import re
import statistics as st
import sys
from collections import Counter

# Row labels shared by several tables (longest first where one contains another).
COMMON = [
    ("Sample-weighted mean (undefended)", "Örnek ağırlıklı ortalama (savunmasız)"),
    ("Uniform mean (undefended)", "Düz ortalama (savunmasız)"),
    ("Coordinate-wise median", "Koordinat bazında medyan"),
    ("Norm clipping", "Norm kırpma"),
    ("FLTrust (normalized)", "FLTrust (normalize)"),
    ("Fed-MDBSCAN-G (full)", "Fed-MDBSCAN-G (tam)"),
    ("Fed-MDBSCAN-G, stage 1 only", "Fed-MDBSCAN-G, yalnız 1. aşama"),
    ("Fed-MDBSCAN-G, no activation memory", "Fed-MDBSCAN-G, etkinleşme belleği yok"),
    ("Fed-MDBSCAN-G, no valve", "Fed-MDBSCAN-G, valf yok"),
    ("Geometric-median distance control", "Geometrik medyan uzaklık kontrolü"),
    ("Trust-region multiplier", "Güven bölgesi çarpanı"),
    (r"Loud Gaussian ($\sigma=5$)", r"Yüksek Gauss gürültüsü ($\sigma=5$)"),
    ("Label flipping", "Etiket çevirme"),
    ("Patch backdoor", "Yama arka kapısı"),
    ("Bounded random direction", "Sınırlı rastgele yön"),
    ("Constrained omniscient", "Kısıtlı her şeyi bilen"),
]

UNITS6 = (r" &  & (\%) & (\%) & (pp) & (pp) \\", r" &  & (\%) & (\%) & (yp) & (yp) \\")
HDR_RULE = ("\nRule & MNIST", "\nKural & MNIST")

TABLES = {
    "ablation": dict(
        caption=r"Uç Nokta Ablasyonları: Varyant ile Tam Yöntem Arasındaki Son Doğruluk Farkı (Yüzde Puan)",
        notes=r"Varyant eksi tam bileşik yöntem, yüzde puan cinsinden son doğruluk farkı; hücreler eşleşen ablasyon bloğunda üç tohum üzerinden veri kümesi~$\times$~koşul ortalamalarıdır. Aralıklar koşullar arasındaki değişkenliği gösterir, güven aralığı değildir. Ek belge, eşleşmiş yarıçaplı bir kontrolü ve Aşama-1 yarıçap çarpanına duyarlılığı ekler.",
        rows=[(r"Variant & Cells & Mean & Min. & Max. \\", r"Varyant & Hücre & Ort. & En az & En çok \\")]),
    "alarm": dict(
        caption=r"Fed-MDBSCAN-G'nin Saldırgansız Tur Düzeyi Alarm Oranı",
        notes=r"Payda saldırgansız turlardır; dolayısıyla her alarm yanlıştır. Değerlendirilen kurallar içinde tur düzeyinde alarm üreten tek kural Fed-MDBSCAN-G'dir; diğer kurallarda alarm kanalı yoktur ve onlar için oran verilmemiştir.",
        rows=[(r"$\alpha$ & Dataset & Alarming rounds & Rate (\%) & BER (\%) \\",
               r"$\alpha$ & Veri kümesi & Alarm veren tur & Oran (\%) & BER (\%) \\")]),
    "backdoor": dict(
        caption=r"Fed-MDBSCAN-G'nin Yama Arka Kapısı Sonuçları ve Eşleşen Kontroller",
        notes=r"ASR, tetiklenmiş hedef dışı örneklerdeki saldırı başarı oranıdır. Doğruluk ve ASR birlikte verilmiştir; düşük doğruluklu $\alpha=0.01$ bloğu etkili koruma olarak okunmamalıdır.",
        rows=[(r"\multicolumn{2}{c}{Attacked} & \multicolumn{2}{c}{Attack disabled}",
               r"\multicolumn{2}{c}{Saldırılı} & \multicolumn{2}{c}{Saldırı kapalı}"),
              (r"$\alpha$ & Dataset & Acc. (\%) & ASR (\%) & Acc. (\%) & ASR (\%) \\",
               r"$\alpha$ & Veri kümesi & Doğr. (\%) & ASR (\%) & Doğr. (\%) & ASR (\%) \\")]),
    "ber": dict(
        caption=r"Saldırgansız Dürüst İstemci Dışlama Oranı (BER, \%)",
        notes=r"Hiç saldırgan yokken reddedilen dürüst istemci--tur gönderimleri; üç tohum, 30 tur ve turda 90 katılımcı (hücre başına 8{,}100 dürüst istemci--tur). Fashion, Fashion-MNIST anlamına gelir; tireler planlanan kapsam dışındaki koşullardır. FLTrust sıfır ağırlıklı gönderimleri sayar. Norm kırpma ve koordinat bazında medyan hiçbir istemciyi reddetmez; bu yüzden BER değerleri tanım gereği sıfırdır ve dürüst maliyetleri Tablo~\ref{tab:buc} içinde görülür.",
        rows=[HDR_RULE]),
    "buc": dict(
        caption=r"Saldırgansız Dürüst Fayda Kaybı (BUC, Yüzde Puan)",
        notes=r"Savunmasız düz ortalamanın son tur doğruluğu eksi savunmanınki; Tablo~\ref{tab:ber} ile aynı koşumlar. Pozitif değerler düz ortalamadan daha düşük doğruluğu gösterir. Üç tohum üzerinden ortalamalar; tohum başına aralıklar ek belgede verilmiştir.",
        rows=[HDR_RULE]),
    "cluster_ratios": dict(
        caption=r"Saldırgansız Bir MNIST Kontrol Noktasında Bulunan Kümeler",
        notes=r"Tohum 2024, tur 9; bütün istemciler dürüsttür. Mini-batch rejimleri: A, 32 örneklik standart yükleyici; B, her yerel adımda yeni bir 20 örneklik altküme; C, ilk 20 örneklik mini-batch'in beş kez tekrarı. Oran, $\tau=2$ ve $R_0$ ana metindeki uzlaşma testindeki gibi tanımlı olmak üzere $\lVert c_S-m_{B_0}\rVert/(\tau R_0)$ değeridir; oran 1'i aşınca grup reddedilir.",
        rows=[(r"Arm & Cluster & Size & In $B_0$ & Ratio & Decision \\",
               r"Kol & Küme & Boyut & $B_0$ içinde & Oran & Karar \\"),
              (r" & accept \\", r" & kabul \\"), (r" & reject \\", r" & ret \\")]),
    "constrained": dict(
        caption=r"Kısıtlı Her Şeyi Bilen Saldırgan Altında Çalışma Noktaları",
        notes=r"Yüzde otuz saldırgan: turda 63 dürüst ve 27 saldırgan katılımcı. Öngörülen FPR, sıfır saldırgan yakalamadaki ($\mathrm{TPR}=0$) değerdir: Multi-Krum için bir özdeşlik, FLAME için bir üst sınır (Sonuç~\ref{cor:cardinality}--\ref{cor:majority}). FLTrust ve Fed-MDBSCAN-G böyle bir öngörü vermez; kural bazındaki oranları ek belgededir. CIFAR-10/FLAME/$\alpha=0.1$ (iki tamamlanmış tohumdan 60 tur) dışında her hücrede 90 kayıtlı tur vardır.",
        rows=[(r"Dataset & Rule & TPR & FPR & $J$ & Predicted \\", r"Veri kümesi & Kural & TPR & FPR & $J$ & Öngörülen \\"),
              (r" &  & (\%) & (\%) & (pp) & FPR (\%) \\", r" &  & (\%) & (\%) & (yp) & FPR (\%) \\")]),
    "coverage": dict(
        caption=r"Bloklara Göre Planlanan Değerlendirme Kapsamı",
        notes=r"Bir birim, bir kural--koşul--tohum koşumudur. Planlanan 2130 birimin 2125'i tamamlanmış, 5'i doldurulmak ya da yeni tohumla tekrarlanmak yerine başarısız olarak tutulmuştur. Bloklar dengeli bir tam faktöriyel tasarım oluşturmaz.",
        rows=[(r"Block & Units \\", r"Blok & Birim \\"),
              ("Main matrix (attacked and adversary-free)", "Ana matris (saldırılı ve saldırgansız)"),
              ("Ablation variants", "Ablasyon varyantları"),
              ("Matched attack-disabled controls", "Eşleşen saldırısı kapatılmış kontroller"),
              ("Oracle diagnostics", "Kâhin (oracle) tanıları"),
              ("Alternative partition policy", "Alternatif bölümleme politikası"),
              ("Fixed local-step control", "Sabit yerel adım kontrolü"),
              ("Onset/offset timing", "Saldırı başlangıç/bitiş zamanlaması"),
              ("Total planned", "Planlanan toplam")]),
    "coverage_replay": dict(
        caption=r"72 Beş Adımlı Güncelleme Matrisinde Uzlaşma Testi Kapsamının Yeniden Oynatılması",
        notes=r"Küme yapısı, geometri ve etkinleşme belleği sabit tutulmuştur. Değerler, emniyet valfinden sonraki istemci--kontrol noktası sayımı olarak dürüst/saldırgan retleridir. P0 kullanılan politikadır (yalnız kümeler); P1 kümelenmemiş düşük yoğunluklu güncellemeleri ayrıca tekil olarak aynı teste sokar; P2 bunları doğrudan dışlar. Her saldırılı blok 1{,}296 dürüst ve 324 saldırgan gözlemi, her saldırısı kapatılmış blok 1{,}620 dürüst gözlemi içerir.",
        rows=[(r"Gate & Attack & P0 & P1 & P2 \\", r"Kapı & Saldırı & P0 & P1 & P2 \\"),
              (r"\emph{Attacked matrices}", r"\emph{Saldırılı matrisler}"),
              (r"\emph{Attack-disabled controls}", r"\emph{Saldırısı kapatılmış kontroller}"),
              (r"\quad As deployed & ", r"\quad Kullanılan kapı & "),
              (r"\quad Density-only & ", r"\quad Yalnız yoğunluk & "),
              (" & Patch & ", " & Yama & ")]),
    "discrimination": dict(
        caption=r"Saldırı Ailesine Göre İstemci Düzeyinde Ayırt Etme",
        notes=r"$J=\mathrm{TPR}-\mathrm{FPR}$ (Youden indeksi); $J<0$ dürüst istemcilerin saldırganlardan önce reddedildiğini gösterir. Fayda, aynı koşulda savunmanın doğruluğu eksi savunmasız doğruluktur. Her satır, ret yapan dört kuralın kural~$\times$~veri kümesi~$\times$~koşul hücrelerini birleştirir; ailelerin kapsamı farklı olduğundan satırlar betimsel ortalamalardır.",
        rows=[(r"Attacker family & Cells & TPR & FPR & $J$ & Benefit \\", r"Saldırgan ailesi & Hücre & TPR & FPR & $J$ & Fayda \\"), UNITS6]),
    "discrimination_method": dict(
        caption=r"Kurala ve Saldırı Ailesine Göre Ayırt Etme",
        notes=r"Mevcut hücreler üzerinden ortalamalar; sütunlar ana metindeki Tablo~VII ile aynıdır. FLTrust sıfır ağırlık kararlarını sayar.",
        rows=[(r"Attack family / rule & Cells & TPR & FPR & $J$ & Benefit \\", r"Saldırı ailesi / kural & Hücre & TPR & FPR & $J$ & Fayda \\"), UNITS6]),
    "flame_sizes": dict(
        caption=r"Saldırgansız Koşullarda FLAME'in Tuttuğu Küme Boyutları",
        notes=r"Saldırgansız ana hücrelerde kaydedilmiş kabul kimliklerinden sayılmıştır; her satır üç tohum ve 90 tur kapsar. Boyut 46, izin verilen en küçük boyuttur: $\lfloor n/2\rfloor+1$.",
        rows=[(r"Dataset & $\alpha$ & Mean size & Range & Size 46 \\",
               r"Veri kümesi & $\alpha$ & Ort. boyut & Aralık & Boyut 46 \\")]),
    "gamma": dict(
        caption=r"Saldırılı Kontrol Noktalarında İlk Kabul Havuzunun Radyal Oranı",
        notes=r"Farklı saldırılı kontrol noktası matrisleri; eşik $\tau=2$ değeridir. Beş adımlı matrisler 90 katılımcıdan 18'inin saldırgan olduğu ayrı kesme çalışmasından, kanonik matrisler ise 90 katılımcıdan 27'sinin saldırgan olduğu yeniden yürütülmüş kanonik koşumlardan gelir. Her beş adımlı matriste $B_0$ 90 katılımcının tamamını içerir; beş adımlı istisna Fashion, tohum 137, yama, tur 29'dur.",
        rows=[(r"Attack & Matrices & $\Gamma\leq2$ & Median & Maximum \\",
               r"Saldırı & Matris & $\Gamma\leq2$ & Medyan & En büyük \\"),
              (r"\emph{Five-step development runs}", r"\emph{Beş adımlı geliştirme koşumları}"),
              (r"\emph{Canonical runs}", r"\emph{Kanonik koşumlar}"),
              ("\nPatch, ", "\nYama, "), ("\nAll attacked & ", "\nTüm saldırılı & ")]),
}

CAPTION = re.compile(r"(\\caption\{)(.*?)(\}\\label\{)", re.S)
NOTES = re.compile(r"(\\parbox\{\\linewidth\}\{\\footnotesize )(.*?)(\}\n\\end\{table\*?\})", re.S)


def translate(name, text, spec):
    out, n = CAPTION.subn(lambda m: m.group(1) + spec["caption"] + m.group(3), text)
    assert n == 1, (name, "caption")
    if "notes" in spec:
        out, n = NOTES.subn(lambda m: m.group(1) + spec["notes"] + m.group(3), out)
        assert n == 1, (name, "notes")
    else:
        assert not NOTES.search(out), (name, "untranslated notes")
    for en, tr in spec.get("rows", []):
        assert en in out, (name, en)
        out = out.replace(en, tr)
    for en, tr in COMMON:
        out = out.replace(en, tr)
    out = re.sub(r"(\d)\{,\}(\d{3})", r"\1\\,\2", out)
    left = [en for en, _ in COMMON if en in out] + [en for en, _ in spec.get("rows", []) if en in out]
    assert not left, (name, left)
    digits = lambda s: Counter(re.findall(r"\d+", s))
    assert digits(out) == digits(text), (name, digits(text) - digits(out), digits(out) - digits(text))
    return out


def figure(root):
    sys.path.insert(0, os.path.join(root, "analysis"))
    import build_tables as bt
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})
    import matplotlib.pyplot as plt

    idx = {(r["phase"], r["scenario"], r["dataset"], r["method"]): r for r in bt.load(root)["cells"]}
    labels = {"krum_bound30": "Multi-Krum", "fltrust_normalized": "FLTrust (normalize)",
              "flame_hdbscan": "FLAME (HDBSCAN)", "fed_mdbscan_g": "Fed-MDBSCAN-G"}
    marks = {"krum_bound30": "o", "fltrust_normalized": "s", "flame_hdbscan": "^", "fed_mdbscan_g": "D"}
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    for m in bt.REJECTORS:
        xx, ys = [], []
        for a, sid in zip([0.5, 0.1, 0.01], ["1.1", "6.1", "6.2"]):
            vals = [bt.pf(idx[("main", sid, d, m)]["fpr_mean"]) for d in bt.DS_ORDER
                    if ("main", sid, d, m) in idx and bt.pf(idx[("main", sid, d, m)]["fpr_mean"]) is not None]
            if vals:
                xx.append(a)
                ys.append(100 * st.mean(vals))
        ax.plot(xx, ys, marker=marks[m], ms=4, lw=1.1, label=labels[m])
    ax.set_xscale("log")
    ax.invert_xaxis()
    ax.set_xlabel(r"Dirichlet $\alpha$ (saldırgansız)", fontsize=7)
    ax.set_ylabel("dürüst istemci dışlama oranı (%)", fontsize=7)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=5.6, frameon=False, loc="lower right")
    ax.grid(alpha=0.25, lw=0.5)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(root, "manuscript", "figures", "ber_vs_alpha_tr.pdf"), dpi=300)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    root = os.path.abspath(ap.parse_args().root)
    src = os.path.join(root, "manuscript", "generated")
    dst = os.path.join(root, "manuscript", "generated_tr")
    os.makedirs(dst, exist_ok=True)
    for name, spec in TABLES.items():
        with open(os.path.join(src, name + ".tex"), encoding="utf-8") as fh:
            text = fh.read()
        with open(os.path.join(dst, name + ".tex"), "w", encoding="utf-8") as fh:
            fh.write(translate(name, text, spec))
    figure(root)
    print(f"{len(TABLES)} Turkish tables and 1 figure written; digit groups match the English tables.")


if __name__ == "__main__":
    main()
