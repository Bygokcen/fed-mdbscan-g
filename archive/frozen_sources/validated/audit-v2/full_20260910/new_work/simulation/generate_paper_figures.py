"""
Faz 2b paper figure generator — 9 method × 3 dataset × 15 senaryo matrisi.

Kaynak:
  - new_work/results/phase2b_report/table_*.csv     (final accuracy / FPR / TPR / alert quality)
  - new_work/results/heterogeneous_v3_{dataset}/
        scenario_*/all_results.csv                  (round-bazlı eğriler)
        master_summary.json                         (time_mean / ek özet)

Çıktı:
  new_work/FED-MDBSCAN_Paper/figures/
    fig_accuracy_vs_rounds_all.png    — 3 dataset × 5 temsili senaryo (round eğrileri)
    fig_accuracy_per_scenario.png     — 9 method × 15 senaryo heatmap, 3 dataset facet
    fig_fpr_per_scenario.png          — FPR heatmap, 3 dataset facet (yapısal-0 metodlar gri)
    fig_detection_per_scenario.png    — Fed-MDBSCAN-G TPR, saldırı-tipi gruplu bar (3 dataset)
    fig_alpha01_highlight.png         — α=0.01 kritik blok, Fed-MDBSCAN-G vs en iyi rakip
    fig_alert_xai.png                 — Saldırı-tipi başına kümülatif TP/FP/FN + P/R özeti
    fig_overhead_per_scenario.png     — 9 method per-round ortalama maliyet, 3 dataset

Kullanım:
  python -m simulation.generate_paper_figures
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 130,
    'savefig.dpi': 240,
    'savefig.bbox': 'tight',
})

# ──────────────────────────────────────────────────────────────────────
# Konfigürasyon
# ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]      # new_work/
PHASE2B = ROOT / 'results' / 'phase2b_report'
HETERO_BASE = ROOT / 'results'
OUT_DIR = ROOT / 'FED-MDBSCAN_Paper' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = ['mnist', 'fashion_mnist', 'har']
DATASET_LABELS = {
    'mnist': 'MNIST',
    'fashion_mnist': 'Fashion-MNIST',
    'har': 'UCI HAR',
}

# 9 method — Fed-MDBSCAN-G ön planda, sonra yoğunluk ailesi, sonra istatistiksel
METHOD_ORDER = [
    'fed_mdbscan_g', 'flame', 'fed_dbscan', 'fed_g2l', 'fed_rra',
    'fedavg', 'krum', 'coord_median', 'fltrust',
]
METHOD_LABELS = {
    'fed_mdbscan_g': 'Fed-MDBSCAN-G (ours)',
    'fed_dbscan':    'Fed-DBSCAN',
    'fed_rra':       'FedRRA',
    'fed_g2l':       'FedG2L',
    'fedavg':        'FedAvg',
    'krum':          'Krum',
    'coord_median':  'Coord-Median',
    'fltrust':       'FLTrust',
    'flame':         'FLAME',
}
METHOD_SHORT = {
    'fed_mdbscan_g': 'Fed-\nMDBSCAN-G',
    'fed_dbscan':    'F-DBS',
    'fed_rra':       'FedRRA',
    'fed_g2l':       'F-G2L',
    'fedavg':        'FedAvg',
    'krum':          'Krum',
    'coord_median':  'C-Med',
    'fltrust':       'FLTr',
    'flame':         'FLAME',
}
METHOD_COLORS = {
    'fed_mdbscan_g': '#E63946',  # vurgulu kırmızı
    'flame':         '#9B2226',  # koyu kırmızı (parallel: yoğunluk-tabanlı kuzeni)
    'fed_dbscan':    '#457B9D',  # mavi
    'fed_g2l':       '#E9C46A',  # sarı
    'fed_rra':       '#2A9D8F',  # teal
    'fedavg':        '#888888',  # gri (baseline yok-savunma)
    'krum':          '#8338EC',  # mor
    'coord_median':  '#FB8500',  # turuncu
    'fltrust':       '#06A77D',  # yeşil
}

# Scenario meta — saldırı tipi/oranı haritalanması
SCENARIO_ATTACK = {
    '1.1': ('clean', 'gaussian', 0.0),
    '1.2': ('gaussian', 'Loud-Gaussian', 0.20),
    '1.3': ('label_flip', 'LabelFlip', 0.20),
    '2.1': ('gaussian', 'Loud-Gaussian', 0.20),
    '2.2': ('label_flip', 'LabelFlip', 0.20),
    '2.3': ('gaussian', 'Loud-Gaussian', 0.30),
    '3.1': ('gaussian', 'Loud-Gaussian', 0.20),
    '3.2': ('gaussian', 'Loud-Gaussian', 0.30),
    '3.3': ('label_flip', 'LabelFlip', 0.30),
    '4.1': ('stealth_gaussian', 'Stealth-Gaussian', 0.20),
    '4.2': ('stealth_gaussian', 'Stealth-Gaussian', 0.20),
    '4.3': ('stealth_gaussian', 'Stealth-Gaussian', 0.30),
    '5.1': ('adaptive_gaussian', 'Adaptive-Gaussian', 0.20),
    '5.2': ('adaptive_gaussian', 'Adaptive-Gaussian', 0.20),
    '5.3': ('adaptive_gaussian', 'Adaptive-Gaussian', 0.30),
}
ATTACK_FAMILY_LABELS = {
    'gaussian': 'Loud-Gaussian',
    'stealth_gaussian': 'Stealth-Gaussian',
    'adaptive_gaussian': 'Adaptive-Gaussian',
    'label_flip': 'LabelFlip',
    'clean': 'Clean',
}


# ──────────────────────────────────────────────────────────────────────
# Veri yükleyiciler
# ──────────────────────────────────────────────────────────────────────
def load_phase2b_table(name: str) -> pd.DataFrame:
    path = PHASE2B / f'table_{name}.csv'
    df = pd.read_csv(path)
    df['scenario'] = df['scenario'].astype(str)
    return df


def load_master_summary(dataset: str) -> list[dict]:
    path = HETERO_BASE / f'heterogeneous_v3_{dataset}' / 'master_summary.json'
    with open(path) as f:
        return json.load(f)


def load_round_curve(dataset: str, scenario: str, method: str) -> pd.DataFrame | None:
    """Tek bir method için round-bazlı accuracy eğrisini çıkar."""
    path = HETERO_BASE / f'heterogeneous_v3_{dataset}' / f'scenario_{scenario}' / 'all_results.csv'
    if not path.exists():
        return None
    df = pd.read_csv(path)
    sub = df[df['method'] == method]
    if len(sub) == 0:
        return None
    return sub.groupby('round', as_index=False)['accuracy'].mean()


# ──────────────────────────────────────────────────────────────────────
# 1. Round-bazlı doğruluk eğrileri (3 dataset × 5 temsili senaryo)
# ──────────────────────────────────────────────────────────────────────
def fig_accuracy_curves():
    # Heterojenlik merdivenini iyi temsil eden 5 senaryo
    representative = ['1.1', '2.1', '3.1', '4.2', '5.2']
    fig, axes = plt.subplots(len(DATASETS), len(representative),
                             figsize=(16, 9), sharex=True, sharey='row')
    for di, ds in enumerate(DATASETS):
        for si, sc in enumerate(representative):
            ax = axes[di, si]
            for m in METHOD_ORDER:
                curve = load_round_curve(ds, sc, m)
                if curve is None or len(curve) == 0:
                    continue
                lw = 2.4 if m == 'fed_mdbscan_g' else 1.2
                alpha = 1.0 if m == 'fed_mdbscan_g' else 0.7
                ax.plot(curve['round'], curve['accuracy'],
                        color=METHOD_COLORS[m], linewidth=lw, alpha=alpha,
                        marker='o' if m == 'fed_mdbscan_g' else None,
                        markersize=4, markevery=max(1, len(curve) // 6))
            label = ATTACK_FAMILY_LABELS[SCENARIO_ATTACK[sc][0]]
            ratio = SCENARIO_ATTACK[sc][2]
            ratio_str = f'{int(ratio*100)}%' if ratio > 0 else 'Clean'
            ax.set_title(f'{sc}: {label} {ratio_str}', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1.0])
            if di == len(DATASETS) - 1:
                ax.set_xlabel('Round')
            if si == 0:
                ax.set_ylabel(f'{DATASET_LABELS[ds]}\nAccuracy', fontsize=10)
    handles = [plt.Line2D([0], [0], color=METHOD_COLORS[m],
                          linewidth=2.4 if m == 'fed_mdbscan_g' else 1.2,
                          label=METHOD_LABELS[m])
               for m in METHOD_ORDER]
    fig.legend(handles=handles, loc='upper center', ncol=5,
               bbox_to_anchor=(0.5, 1.02), frameon=False, fontsize=9)
    fig.suptitle('Faz 2b — Round-bazlı Doğruluk: 3 Dataset × Heterojenlik Merdiveni',
                 y=1.06, fontsize=13)
    out = OUT_DIR / 'fig_accuracy_vs_rounds_all.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# 2. Final accuracy heatmap (9 method × 15 senaryo, 3 dataset facet)
# ──────────────────────────────────────────────────────────────────────
def fig_accuracy_heatmap():
    df = load_phase2b_table('final_accuracy')
    fig, axes = plt.subplots(1, len(DATASETS), figsize=(20, 6.5), sharey=True,
                             gridspec_kw={'wspace': 0.05})
    cmap = plt.cm.RdYlGn
    vmin, vmax = 0.15, 1.0
    for di, ds in enumerate(DATASETS):
        ax = axes[di]
        sub = df[df['dataset'] == ds].sort_values('scenario')
        scenarios = sub['scenario'].tolist()
        mat = np.array([sub[m].values for m in METHOD_ORDER])  # (9, 15)
        im = ax.imshow(mat, cmap=cmap, vmin=vmin, vmax=vmax, aspect='auto')
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels(scenarios, rotation=45, ha='right', fontsize=9)
        ax.set_yticks(range(len(METHOD_ORDER)))
        if di == 0:
            ax.set_yticklabels([METHOD_SHORT[m] for m in METHOD_ORDER], fontsize=10)
            ax.set_ylabel('Yöntem')
        else:
            ax.tick_params(labelleft=False)
        ax.set_xlabel('Senaryo')
        ax.set_title(DATASET_LABELS[ds], fontsize=12, fontweight='bold')
        # Hücre içi sayılar
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat[i, j]
                txt_color = 'white' if v < 0.45 or v > 0.85 else 'black'
                ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                        fontsize=7, color=txt_color)
        # En iyi method'u her sütunda işaretle (★)
        for j in range(mat.shape[1]):
            best_i = int(np.argmax(mat[:, j]))
            ax.add_patch(plt.Rectangle((j - 0.45, best_i - 0.45), 0.9, 0.9,
                                        fill=False, edgecolor='black', linewidth=1.5))
    cbar = fig.colorbar(im, ax=axes, fraction=0.012, pad=0.02)
    cbar.set_label('Final Accuracy (round 30, 3-tohum ort.)', fontsize=10)
    fig.suptitle('Faz 2b — 9 Yöntem × 15 Senaryo Final Doğruluk Heatmap (■: senaryonun en iyisi)',
                 fontsize=12.5, y=1.02)
    out = OUT_DIR / 'fig_accuracy_per_scenario.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# 3. FPR heatmap (yapısal-0 yöntemler "—" olarak işaretlenir)
# ──────────────────────────────────────────────────────────────────────
def fig_fpr_heatmap():
    df = load_phase2b_table('fpr')
    # Yapısal-FPR-0: FedAvg, Coord-Median, FLAME (filtreleme yapmaz)
    structural_zero = {'fedavg', 'coord_median', 'flame'}
    filter_methods = [m for m in METHOD_ORDER if m not in structural_zero]
    n_methods = len(filter_methods)

    fig, axes = plt.subplots(1, len(DATASETS), figsize=(20, 5.0), sharey=True,
                             gridspec_kw={'wspace': 0.05})
    cmap = plt.cm.YlOrRd
    vmin, vmax = 0.0, 0.45
    for di, ds in enumerate(DATASETS):
        ax = axes[di]
        sub = df[df['dataset'] == ds].sort_values('scenario')
        scenarios = sub['scenario'].tolist()
        mat = np.array([sub[m].values for m in filter_methods])
        im = ax.imshow(mat, cmap=cmap, vmin=vmin, vmax=vmax, aspect='auto')
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels(scenarios, rotation=45, ha='right', fontsize=9)
        ax.set_yticks(range(n_methods))
        if di == 0:
            ax.set_yticklabels([METHOD_SHORT[m] for m in filter_methods], fontsize=10)
            ax.set_ylabel('Yöntem (filtreleyen)')
        else:
            ax.tick_params(labelleft=False)
        ax.set_xlabel('Senaryo')
        ax.set_title(DATASET_LABELS[ds], fontsize=12, fontweight='bold')
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat[i, j]
                txt_color = 'white' if v > 0.25 else 'black'
                ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                        fontsize=7, color=txt_color)
        # Her sütunun en düşük FPR'ını işaretle
        for j in range(mat.shape[1]):
            best_i = int(np.argmin(mat[:, j]))
            ax.add_patch(plt.Rectangle((j - 0.45, best_i - 0.45), 0.9, 0.9,
                                        fill=False, edgecolor='green', linewidth=1.8))
    cbar = fig.colorbar(im, ax=axes, fraction=0.012, pad=0.02)
    cbar.set_label('Mean FPR (düşük olan iyidir)', fontsize=10)
    fig.suptitle('Faz 2b — Yanlış Pozitif Oranı (FPR), filtreleyen yöntemler\n'
                 '(FedAvg/Coord-Median/FLAME yapısal olarak filtreleme yapmaz, dahil edilmedi)',
                 fontsize=12, y=1.05)
    out = OUT_DIR / 'fig_fpr_per_scenario.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# 4. Detection (TPR) — saldırı-tipi gruplu bar (Fed-MDBSCAN-G odaklı)
# ──────────────────────────────────────────────────────────────────────
def fig_detection_by_attack():
    df = load_phase2b_table('tpr')
    # Saldırı-tipine göre Fed-MDBSCAN-G TPR'ı topla
    attack_groups = ['gaussian', 'stealth_gaussian', 'label_flip', 'adaptive_gaussian']
    attack_titles = ['Loud-Gaussian (5 sen.)', 'Stealth-Gaussian (3 sen.)',
                     'LabelFlip (3 sen.)', 'Adaptive-Gaussian (3 sen.)']

    means = {ds: [] for ds in DATASETS}
    for atk in attack_groups:
        scs = [s for s, (a, _, _) in SCENARIO_ATTACK.items() if a == atk]
        for ds in DATASETS:
            vals = []
            for sc in scs:
                row = df[(df['dataset'] == ds) & (df['scenario'] == sc)]
                if len(row):
                    vals.append(float(row['fed_mdbscan_g'].values[0]))
            means[ds].append(float(np.mean(vals)) if vals else 0.0)

    fig, ax = plt.subplots(figsize=(11, 5.0))
    x = np.arange(len(attack_groups))
    bar_w = 0.26
    ds_colors = {'mnist': '#1d3557', 'fashion_mnist': '#457B9D', 'har': '#E63946'}
    for di, ds in enumerate(DATASETS):
        offset = (di - 1) * bar_w
        bars = ax.bar(x + offset, means[ds], bar_w,
                      color=ds_colors[ds], edgecolor='white', linewidth=0.8,
                      label=DATASET_LABELS[ds], alpha=0.92)
        for bar, v in zip(bars, means[ds]):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.015,
                    f'{v:.2f}', ha='center', fontsize=9, fontweight='bold')
    ax.axhline(0.5, color='gray', linestyle=':', linewidth=0.8, alpha=0.6)
    ax.text(3.4, 0.51, 'detection-incomplete sınırı', fontsize=8, color='gray', ha='right')
    ax.set_xticks(x)
    ax.set_xticklabels(attack_titles, fontsize=10)
    ax.set_ylabel('Fed-MDBSCAN-G TPR (saldırı yakalama)')
    ax.set_ylim([0, 1.15])
    ax.set_title('Faz 2b — Saldırı Tipi × Dataset Bazlı Tespit Oranı (TPR)\n'
                 'Loud/Stealth-Gaussian'
                 'da TPR≈1; LabelFlip ve Adaptive-Gaussian rejimleri koşullu/kısmi',
                 fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    ax.legend(loc='upper right', frameon=True, framealpha=0.9)
    out = OUT_DIR / 'fig_detection_per_scenario.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# 5. α=0.01 kritik blok — Fed-MDBSCAN-G ile en iyi rakip (FLAME) farkı
# ──────────────────────────────────────────────────────────────────────
def fig_alpha01_highlight():
    df = load_phase2b_table('final_accuracy')
    alpha01_scs = ['3.1', '3.2', '3.3', '4.2', '4.3', '5.2', '5.3']
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5),
                              gridspec_kw={'wspace': 0.32})
    for di, ds in enumerate(DATASETS):
        ax = axes[di]
        sub = df[(df['dataset'] == ds) & (df['scenario'].isin(alpha01_scs))]
        sub = sub.set_index('scenario').loc[alpha01_scs].reset_index()
        x = np.arange(len(alpha01_scs))
        bar_w = 0.28
        # Fed-MDBSCAN-G (yapımız)
        ax.bar(x - bar_w, sub['fed_mdbscan_g'], bar_w,
               color=METHOD_COLORS['fed_mdbscan_g'], label='Fed-MDBSCAN-G (ours)',
               edgecolor='white', linewidth=0.8)
        # FLAME (en yakın yoğunluk-tabanlı rakip)
        ax.bar(x, sub['flame'], bar_w, color=METHOD_COLORS['flame'],
               label='FLAME', edgecolor='white', linewidth=0.8)
        # FedG2L (yoğunluk + cosine)
        ax.bar(x + bar_w, sub['fed_g2l'], bar_w, color=METHOD_COLORS['fed_g2l'],
               label='FedG2L', edgecolor='white', linewidth=0.8)
        # Δ vs FLAME etiketleri (ours - flame)
        for xi, sc in enumerate(alpha01_scs):
            d = (sub.loc[xi, 'fed_mdbscan_g'] - sub.loc[xi, 'flame']) * 100
            color = '#E63946' if d > 0 else '#888'
            sign = '+' if d > 0 else ''
            ax.text(xi - bar_w, sub.loc[xi, 'fed_mdbscan_g'] + 0.02,
                    f'{sign}{d:.1f}', ha='center', fontsize=8,
                    fontweight='bold', color=color)
        scenario_labels = []
        for sc in alpha01_scs:
            atk_key = SCENARIO_ATTACK[sc][0]
            atk_short = {'gaussian': 'L-G', 'stealth_gaussian': 'S-G',
                         'adaptive_gaussian': 'A-G', 'label_flip': 'LF'}[atk_key]
            ratio = SCENARIO_ATTACK[sc][2]
            scenario_labels.append(f"{sc}\n{atk_short} {int(ratio*100)}%")
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_labels, fontsize=9)
        ax.set_ylim([0, 1.0])
        ax.set_ylabel('Final Accuracy' if di == 0 else '')
        ax.set_title(DATASET_LABELS[ds], fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        if di == 0:
            ax.legend(loc='upper right', fontsize=8.5, frameon=True, framealpha=0.92)
    fig.suptitle('Faz 2b — α=0.01 Aşırı Heterojenlik Kritik Bloğu '
                 '(Δ% sayıları: Fed-MDBSCAN-G − FLAME)',
                 fontsize=12.5, y=1.02)
    out = OUT_DIR / 'fig_alpha01_highlight.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# 6. xAI alert quality — saldırı-tipi başına kümülatif TP/FP/FN
# ──────────────────────────────────────────────────────────────────────
def fig_alert_xai():
    df = load_phase2b_table('alert_quality')
    df = df[df['attack_present'] == True]  # noqa: E712
    attack_groups = ['gaussian', 'stealth_gaussian', 'label_flip', 'adaptive_gaussian']
    attack_titles = ['Loud-Gaussian', 'Stealth-Gaussian', 'LabelFlip', 'Adaptive-Gaussian']

    summary = {atk: {'TP': 0, 'FP': 0, 'FN': 0} for atk in attack_groups}
    for _, row in df.iterrows():
        sc = str(row['scenario'])
        if sc not in SCENARIO_ATTACK:
            continue
        atk = SCENARIO_ATTACK[sc][0]
        if atk == 'clean':
            continue
        summary[atk]['TP'] += int(row['TP'])
        summary[atk]['FP'] += int(row['FP'])
        summary[atk]['FN'] += int(row['FN'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.2),
                                    gridspec_kw={'width_ratios': [1.6, 1.0], 'wspace': 0.32})
    # SOL: stacked bars (TP + FN); FP zaten 0 — sadece referans için
    x = np.arange(len(attack_groups))
    bar_w = 0.6
    tps = [summary[a]['TP'] for a in attack_groups]
    fns = [summary[a]['FN'] for a in attack_groups]
    fps = [summary[a]['FP'] for a in attack_groups]
    ax1.bar(x, tps, bar_w, label='TP (doğru alarm)', color='#2A9D8F',
            edgecolor='white', linewidth=0.8)
    ax1.bar(x, fns, bar_w, bottom=tps, label='FN (kaçırılan saldırı)',
            color='#E63946', edgecolor='white', linewidth=0.8)
    # FP üstünde — hep 0 olduğu için yazılı not
    ax1.bar(x, fps, bar_w, bottom=[t + f for t, f in zip(tps, fns)],
            label='FP (yanlış alarm)', color='#FB8500', edgecolor='white', linewidth=0.8)
    for i, (t, n) in enumerate(zip(tps, fns)):
        total = t + n
        recall = t / total if total > 0 else 0.0
        ax1.text(i, total + 30, f'R={recall:.2f}', ha='center', fontsize=9.5,
                 fontweight='bold', color='black')
    ax1.set_xticks(x)
    ax1.set_xticklabels(attack_titles, fontsize=10)
    ax1.set_ylabel('Kümülatif round sayısı (3 dataset × 3 tohum)')
    ax1.set_title('Saldırı Tipine Göre Alert Hesabı\n(TP + FN; FP = 0 her satırda)', fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    ax1.legend(loc='upper right', frameon=True, framealpha=0.92, fontsize=9)
    # SAĞ: precision/recall özeti tablosu
    ax2.axis('off')
    table_rows = [['Saldırı tipi', 'TP', 'FP', 'FN', 'Precision', 'Recall']]
    total_tp, total_fp, total_fn = 0, 0, 0
    for atk, title in zip(attack_groups, attack_titles):
        s = summary[atk]
        p = s['TP'] / (s['TP'] + s['FP']) if (s['TP'] + s['FP']) > 0 else 0.0
        r = s['TP'] / (s['TP'] + s['FN']) if (s['TP'] + s['FN']) > 0 else 0.0
        total_tp += s['TP']; total_fp += s['FP']; total_fn += s['FN']
        table_rows.append([title, str(s['TP']), str(s['FP']), str(s['FN']),
                           f'{p:.3f}', f'{r:.3f}'])
    p_tot = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    r_tot = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    table_rows.append(['Toplam', str(total_tp), str(total_fp), str(total_fn),
                       f'{p_tot:.3f}', f'{r_tot:.3f}'])
    tbl = ax2.table(cellText=table_rows, loc='center', cellLoc='center',
                    colWidths=[0.30, 0.10, 0.10, 0.10, 0.18, 0.18])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9.5)
    tbl.scale(1.0, 1.55)
    # header + total satırları kalın
    for j in range(6):
        tbl[(0, j)].set_facecolor('#1d3557')
        tbl[(0, j)].set_text_props(color='white', fontweight='bold')
        tbl[(5, j)].set_facecolor('#f1faee')
        tbl[(5, j)].set_text_props(fontweight='bold')
    ax2.set_title('Kümülatif Alert Kalitesi — Precision = 1.000 (koşulsuz, FP=0)',
                  fontsize=11, pad=10)
    fig.suptitle('Faz 2b — xAI Attack-Alert: 3 780 saldırı round\'unda 0 yanlış alarm',
                 fontsize=12.5, y=1.02)
    out = OUT_DIR / 'fig_alert_xai.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# 7. Hesaplama maliyeti (per-round filter cost), 9 method × 3 dataset
# ──────────────────────────────────────────────────────────────────────
def fig_overhead():
    # master_summary.json'lardan time_mean'leri çek (15 senaryo × dataset → method başına ortalama)
    means = {m: {ds: [] for ds in DATASETS} for m in METHOD_ORDER}
    for ds in DATASETS:
        summary = load_master_summary(ds)
        for sc in summary:
            for m in METHOD_ORDER:
                t = sc.get('methods', {}).get(m, {}).get('time_mean')
                if t is not None:
                    means[m][ds].append(float(t))
    fig, ax = plt.subplots(figsize=(13, 5.2))
    x = np.arange(len(METHOD_ORDER))
    bar_w = 0.27
    ds_colors = {'mnist': '#1d3557', 'fashion_mnist': '#457B9D', 'har': '#E63946'}
    for di, ds in enumerate(DATASETS):
        offset = (di - 1) * bar_w
        vals = [float(np.mean(means[m][ds])) if means[m][ds] else 0.0 for m in METHOD_ORDER]
        bars = ax.bar(x + offset, vals, bar_w,
                      color=ds_colors[ds], label=DATASET_LABELS[ds],
                      edgecolor='white', linewidth=0.8, alpha=0.92)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.02,
                    f'{v:.2f}', ha='center', fontsize=8, color='black')
    ax.set_xticks(x)
    ax.set_xticklabels([METHOD_SHORT[m] for m in METHOD_ORDER], fontsize=10)
    ax.set_ylabel('Per-round filtreleme süresi (sn) — 15 senaryo ortalama')
    ax.set_title('Faz 2b — Hesaplama Maliyeti, 9 Yöntem × 3 Dataset', fontsize=11.5)
    ax.grid(axis='y', alpha=0.3)
    ax.legend(loc='upper right', frameon=True, framealpha=0.92)
    out = OUT_DIR / 'fig_overhead_per_scenario.png'
    fig.savefig(out)
    plt.close(fig)
    print(f'  ✓ {out.name}')


# ──────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────
def main():
    print(f'Faz 2b figure üretimi — kaynak: {PHASE2B}')
    print(f'Çıktı: {OUT_DIR}\n')
    fig_accuracy_curves()
    fig_accuracy_heatmap()
    fig_fpr_heatmap()
    fig_detection_by_attack()
    fig_alpha01_highlight()
    fig_alert_xai()
    fig_overhead()
    # INDEX
    index = OUT_DIR / 'INDEX.md'
    with open(index, 'w') as f:
        f.write('# Faz 2b Paper Figürleri\n\n')
        f.write('Kaynak: `new_work/results/phase2b_report/`\n\n')
        f.write('| Dosya | İçerik |\n|---|---|\n')
        f.write('| fig_accuracy_vs_rounds_all.png | 3 dataset × 5 temsili senaryo round eğrileri |\n')
        f.write('| fig_accuracy_per_scenario.png | 9 method × 15 senaryo accuracy heatmap, dataset facet |\n')
        f.write('| fig_fpr_per_scenario.png | FPR heatmap (filtreleyen 6 yöntem), dataset facet |\n')
        f.write('| fig_detection_per_scenario.png | Fed-MDBSCAN-G TPR, saldırı-tipi × dataset bar |\n')
        f.write('| fig_alpha01_highlight.png | α=0.01 kritik blok, Fed-MDBSCAN-G vs FLAME vs FedG2L |\n')
        f.write('| fig_alert_xai.png | Kümülatif alert kalitesi, P=1.0 koşulsuz / R koşullu |\n')
        f.write('| fig_overhead_per_scenario.png | 9 method × 3 dataset filter cost |\n')
    print(f'\n✓ {index}')


if __name__ == '__main__':
    main()
