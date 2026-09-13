"""
Graphical Abstract — Fed-MDBSCAN-G (Faz 2b: 9 yöntem × 3 dataset × 15 senaryo)
==============================================================================

Tek bir geniş panel çalışmanın tüm hikayesini anlatır:
  (A) N=100 IoT istemci + 4 saldırı tipi (Loud/Stealth/Adaptive Gauss + LabelFlip)
  (B) Gradyan uzayında bimodal göreceli yoğunluk (rd) ayrıştırması
  (C) 9 savunma mimarisi (4-katmanlı Fed-MDBSCAN-G + 8 baseline)
  (D) Üç datasette ortalama final accuracy (Fed-MDBSCAN-G lider) + saldırı-tipi koşullu TPR

Çalıştırma:
    cd /home/gokcen/Fed_MDBSCAN/new_work
    python -m simulation.generate_graphical_abstract
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

OUT_DIR = Path(__file__).resolve().parents[1] / 'FED-MDBSCAN_Paper' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Renk paleti (paper figure'ları ile uyumlu) ────────────────────────
COL_BENIGN = '#2E86AB'
COL_MAL    = '#D62828'
COL_OURS   = '#E63946'  # Fed-MDBSCAN-G vurgu
COL_FLAME  = '#9B2226'
COL_DENS   = '#457B9D'  # yoğunluk-tabanlı aile
COL_STAT   = '#888888'  # istatistiksel aile
DS_COLORS  = {'mnist': '#1d3557', 'fashion': '#457B9D', 'har': '#E63946'}

# ── Faz 2b kanıt rakamları (phase2b_report/table_final_accuracy.csv'den ────
# 15-senaryo ortalama final accuracy
DS_LABELS = ['MNIST', 'Fashion-MNIST', 'UCI HAR']
DS_KEYS   = ['mnist', 'fashion', 'har']
MEAN_ACC = {
    'fed_mdbscan_g': [0.901, 0.789, 0.553],
    'flame':         [0.883, 0.778, 0.532],
    'fedavg':        [0.847, 0.733, 0.463],
    'fed_dbscan':    [0.828, 0.731, 0.518],
    'krum':          [0.827, 0.722, 0.486],
    'fed_g2l':       [0.826, 0.725, 0.521],
    'fed_rra':       [0.805, 0.723, 0.473],
    'coord_median':  [0.797, 0.698, 0.397],
    'fltrust':       [0.772, 0.694, 0.285],
}
# Saldırı-tipi başına TPR (3-dataset ortalama)
TPR_BY_ATTACK = {
    'Loud-Gauss': 1.000,
    'Stealth-G':  0.993,
    'LabelFlip':  0.424,
    'Adaptive-G': 0.127,
}


# ── Yardımcı çizim ────────────────────────────────────────────────────
def _panel_title(ax, letter, title):
    ax.set_title(f'({letter}) {title}', fontsize=10.5, fontweight='bold',
                 loc='left', pad=8)


def _clean(ax, keep_box=False):
    ax.set_xticks([]); ax.set_yticks([])
    if not keep_box:
        for s in ('top', 'right', 'left', 'bottom'):
            ax.spines[s].set_visible(False)


def _flow_arrow(fig, x0, x1, y=0.50, color='#444'):
    fig.patches.append(
        FancyArrowPatch((x0, y), (x1, y), transform=fig.transFigure,
                        arrowstyle='-|>', mutation_scale=22,
                        linewidth=2.2, color=color, zorder=5))


# ── PANEL A: N=100 IoT istemci + 4 saldırı tipi ───────────────────────
def draw_panel_A(ax):
    _panel_title(ax, 'A', 'Heterojen IoT (N=100) + 4 Saldırı Tipi')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    _clean(ax)

    # Istemci grid: 5×4 = 20 örnek, gerçekte N=100; ölçek küçük tutuldu
    rng = np.random.RandomState(0)
    rows, cols = 4, 5
    palette = plt.cm.tab10(np.linspace(0, 1, 6))  # 6 sınıf (HAR'ı temsil)
    # 4 saldırı tipi cells: pos (0,0), (0,4), (3,0), (3,4)
    attack_positions = {
        (0, 0): ('L-G', '#D62828'),
        (0, 4): ('S-G', '#9B2226'),
        (3, 0): ('LF',  '#E76F51'),
        (3, 4): ('A-G', '#FB8500'),
    }
    for r in range(rows):
        for c in range(cols):
            cx = 1.0 + c * 1.7
            cy = 7.8 - r * 1.8
            is_mal = (r, c) in attack_positions
            # Cihaz kutusu
            body = FancyBboxPatch(
                (cx - 0.6, cy - 0.7), 1.2, 1.4,
                boxstyle="round,pad=0.04,rounding_size=0.15",
                linewidth=1.6,
                edgecolor=attack_positions.get((r, c), (None, '#4A4A4A'))[1] if is_mal else '#4A4A4A',
                facecolor='#FBE9E7' if is_mal else '#F2F4F7', zorder=2)
            ax.add_patch(body)
            # Dirichlet bar
            dist = rng.dirichlet(np.full(6, 0.1))
            x_bar, y_bar = cx - 0.50, cy - 0.45
            x_cursor = x_bar
            for ci, frac in enumerate(dist):
                ax.add_patch(plt.Rectangle((x_cursor, y_bar), 1.0 * frac, 0.08,
                                            facecolor=palette[ci],
                                            edgecolor='none', zorder=3))
                x_cursor += 1.0 * frac
            # Etiket
            if is_mal:
                tag, color = attack_positions[(r, c)]
                ax.text(cx, cy + 0.40, tag, ha='center', va='center',
                        fontsize=9, fontweight='bold', color=color, zorder=4)
            else:
                ax.text(cx, cy + 0.40, '✓', ha='center', va='center',
                        fontsize=9, color='#2A9D8F', zorder=4)

    # Alt-yazı
    ax.text(5.0, 0.9,
            'N=100 istemci · Dirichlet α∈{0.5, 0.1, 0.01} · 4 saldırı tipi:\n'
            'Loud-Gauss (L-G) · Stealth-Gauss (S-G) · LabelFlip (LF) · Adaptive-Gauss (A-G)',
            ha='center', va='center', fontsize=8.5, color='#333')
    ax.text(5.0, 9.5,
            '(Şema temsili — 100 cihaz arasından 20–30\'u saldırgan)',
            ha='center', va='center', fontsize=8, style='italic', color='#555')


# ── PANEL B: Gradyan uzayı + bimodal rd ayrıştırma ────────────────────
def draw_panel_B(ax):
    _panel_title(ax, 'B', 'Gradyan Uzayında Bimodal rd Ayrıştırma')
    rng = np.random.RandomState(7)
    # Benign: iki Non-IID alt-küme
    benign_a = rng.randn(8, 2) * 0.40 + np.array([-1.0, 0.5])
    benign_b = rng.randn(6, 2) * 0.40 + np.array([1.2, -0.3])
    mal      = rng.randn(4, 2) * 0.50 + np.array([0.2, 3.0])

    ax.scatter(benign_a[:, 0], benign_a[:, 1], s=110, c=COL_BENIGN,
               edgecolor='white', linewidth=1.0, label='Benign (yoğun)', zorder=3)
    ax.scatter(benign_b[:, 0], benign_b[:, 1], s=110, c=COL_BENIGN,
               edgecolor='white', linewidth=1.0, zorder=3)
    ax.scatter(mal[:, 0], mal[:, 1], s=200, marker='*', c=COL_MAL,
               edgecolor='white', linewidth=1.0, label='Saldırgan (düşük rd)',
               zorder=4)

    # Geometrik medyan işareti
    all_pts = np.vstack([benign_a, benign_b, mal])
    gm = np.median(all_pts, axis=0)
    ax.scatter(*gm, s=200, marker='X', c='#1A1A1A', edgecolor='gold',
               linewidth=1.5, label='Geom. medyan ($\\mu_{GM}$)', zorder=5)

    # L0 trust-region dairesi
    radius = 1.8
    circle = plt.Circle(gm, radius, fill=False, edgecolor='#2A9D8F',
                        linewidth=1.8, linestyle='--',
                        label='L0 trust-region', zorder=2)
    ax.add_patch(circle)

    # Bimodal gap oku (saldırgan ile benign arasında)
    ax.annotate('', xy=(0.5, 2.4), xytext=(0.5, 1.0),
                arrowprops=dict(arrowstyle='<->', color=COL_MAL, lw=1.6))
    ax.text(0.85, 1.7, 'Bimodal\nrd boşluğu', fontsize=8,
            color=COL_MAL, fontweight='bold')

    ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.0, 4.5)
    ax.set_aspect('equal', adjustable='box')
    _clean(ax, keep_box=True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.set_xlabel('gradyan ekseni 1', fontsize=8.5, color='#555')
    ax.set_ylabel('gradyan ekseni 2', fontsize=8.5, color='#555')
    ax.legend(loc='lower left', fontsize=7.5, framealpha=0.92)


# ── PANEL C: 9 savunma mimarisi (Fed-MDBSCAN-G vurgulu) ───────────────
def draw_panel_C(ax):
    _panel_title(ax, 'C', 'Savunma Mimarisi ve Baseline Seti')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    _clean(ax)

    # Üst kısım: Önerilen Fed-MDBSCAN-G (4 katmanlı, vurgulu)
    main_box = FancyBboxPatch(
        (0.4, 6.4), 9.2, 3.0,
        boxstyle="round,pad=0.05,rounding_size=0.25",
        linewidth=2.4, edgecolor=COL_OURS, facecolor=COL_OURS + '15',
        zorder=2)
    ax.add_patch(main_box)
    ax.text(5.0, 9.05, 'Fed-MDBSCAN-G (önerilen)', ha='center',
            fontsize=11, fontweight='bold', color=COL_OURS)
    # 4 katman badges
    layers = [
        ('L0', 'Geom-Medyan\nTrust-Region', '#1d3557'),
        ('L1', 'Bimodal Gap\n+ xAI Alert',  '#457B9D'),
        ('L2', 'SNNC + Geom\nKonsensüs',    '#2A9D8F'),
        ('L3', 'Temporal\n+ FPR Vanası',    '#E9C46A'),
    ]
    for i, (lid, desc, col) in enumerate(layers):
        cx = 1.45 + i * 2.20
        box = FancyBboxPatch((cx - 0.95, 6.85), 1.90, 1.65,
                              boxstyle='round,pad=0.04,rounding_size=0.12',
                              linewidth=1.4, edgecolor=col, facecolor=col + '25',
                              zorder=3)
        ax.add_patch(box)
        ax.text(cx, 8.20, lid, ha='center', va='center',
                fontsize=10.5, fontweight='bold', color=col)
        ax.text(cx, 7.35, desc, ha='center', va='center',
                fontsize=7.6, color='#222')

    # 8 baseline alt blok
    ax.text(0.5, 5.7, '8 Baseline (karşılaştırma):', fontsize=9,
            fontweight='bold', color='#333')
    bases = [
        ('FLAME',    COL_FLAME),
        ('Fed-DBSCAN', COL_DENS),
        ('FedG2L',   '#E9C46A'),
        ('FedRRA',   '#2A9D8F'),
        ('FedAvg',   COL_STAT),
        ('Krum',     '#8338EC'),
        ('C-Median', '#FB8500'),
        ('FLTrust',  '#06A77D'),
    ]
    for i, (name, col) in enumerate(bases):
        r, c = i // 4, i % 4
        cx = 1.30 + c * 2.20
        cy = 4.4 - r * 1.40
        box = FancyBboxPatch((cx - 0.95, cy - 0.45), 1.90, 0.90,
                              boxstyle='round,pad=0.03,rounding_size=0.10',
                              linewidth=1.0, edgecolor=col, facecolor=col + '15',
                              zorder=2)
        ax.add_patch(box)
        ax.text(cx, cy, name, ha='center', va='center',
                fontsize=9, fontweight='bold', color=col)

    # Alt etiket
    ax.text(5.0, 1.35,
            'Yoğunluk-tabanlı aile: F-DBSCAN, FedRRA, FedG2L, FLAME, Fed-MDBSCAN-G\n'
            'İstatistiksel aile: FedAvg, Krum, Coord-Median, FLTrust',
            ha='center', va='center', fontsize=7.8, color='#555', style='italic')


# ── PANEL D: 3-dataset mean accuracy + saldırı-tipi TPR ───────────────
def draw_panel_D(ax):
    _panel_title(ax, 'D', 'Ana Bulgu: Accuracy ve Koşullu TPR')

    # Gridspec'e benzer manuel 2 alt panel
    # Üst: 9 yöntem × 3 dataset bar grouped
    methods_show = ['fed_mdbscan_g', 'flame', 'fedavg', 'fed_dbscan',
                    'fed_g2l', 'krum', 'fltrust']
    method_short = {
        'fed_mdbscan_g': 'Fed-\nMDBSCAN-G',
        'flame': 'FLAME', 'fedavg': 'FedAvg', 'fed_dbscan': 'F-DBS',
        'fed_g2l': 'F-G2L', 'krum': 'Krum', 'fltrust': 'FLTr',
    }
    x = np.arange(len(methods_show))
    bar_w = 0.27
    for di, (dk, dl) in enumerate(zip(DS_KEYS, DS_LABELS)):
        vals = [MEAN_ACC[m][di] for m in methods_show]
        ax.bar(x + (di - 1) * bar_w, vals, bar_w,
               color=DS_COLORS[dk], edgecolor='white', linewidth=0.8,
               label=dl, alpha=0.92, zorder=3)
    # Fed-MDBSCAN-G değer etiketi (üstüne)
    for di in range(3):
        v = MEAN_ACC['fed_mdbscan_g'][di]
        ax.text(0 + (di - 1) * bar_w, v + 0.02, f'{v:.2f}',
                ha='center', fontsize=8, fontweight='bold',
                color=DS_COLORS[DS_KEYS[di]])
    # Fed-MDBSCAN-G liderliğini vurgulayan altın yıldız
    ax.text(0, 1.07, '★', ha='center', fontsize=14, color='#F4A300', zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels([method_short[m] for m in methods_show],
                       fontsize=8.5, fontweight='bold')
    ax.set_ylabel('15-senaryo ortalama final accuracy', fontsize=8.5)
    ax.set_ylim(0, 1.15)
    ax.grid(axis='y', linestyle=':', alpha=0.35)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.legend(loc='upper right', fontsize=7.5, framealpha=0.92, ncol=3)

    # Alt yazı: Saldırı-tipi TPR satırı
    tpr_text = '   '.join(f'{k}={v:.2f}' for k, v in TPR_BY_ATTACK.items())
    ax.text(0.5, 0.035,
            f'Fed-MDBSCAN-G TPR (saldırı tipi başına):  {tpr_text}',
            ha='center', va='bottom', fontsize=7.6, color='#444',
            transform=ax.transAxes, style='italic',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.82, pad=2.0))


# ── Ana figür ─────────────────────────────────────────────────────────
def plot_graphical_abstract():
    fig = plt.figure(figsize=(14.5, 10.0), constrained_layout=False)
    gs = fig.add_gridspec(
        nrows=2, ncols=2,
        left=0.055, right=0.975, top=0.835, bottom=0.095,
        wspace=0.24, hspace=0.38,
        width_ratios=[1.02, 1.08],
        height_ratios=[1.0, 1.02],
    )
    axA = fig.add_subplot(gs[0, 0]); draw_panel_A(axA)
    axB = fig.add_subplot(gs[0, 1]); draw_panel_B(axB)
    axC = fig.add_subplot(gs[1, 0]); draw_panel_C(axC)
    axD = fig.add_subplot(gs[1, 1]); draw_panel_D(axD)

    # Akış okları
    _flow_arrow(fig, 0.482, 0.512, y=0.615)
    _flow_arrow(fig, 0.482, 0.512, y=0.255)

    fig.suptitle(
        'Fed-MDBSCAN-G: Heterojen IoT Ağlarında Zehirlenme Saldırılarına Karşı '
        'Çok-Yoğunluklu Federe Öğrenme Savunması',
        fontsize=13.0, fontweight='bold', y=0.965,
    )
    fig.text(
        0.5, 0.918,
        'Faz 2b doğrulaması: 3 dataset (MNIST, Fashion-MNIST, UCI HAR) × '
        '15 senaryo × 9 method × 3 tohum = 1 215 birim.',
        ha='center', va='center', fontsize=9.2, style='italic', color='#333',
    )
    fig.text(
        0.5, 0.888,
        'Alert özeti: 3 780 saldırı round\'unda FP=0; tüm 4 050 round\'da clean HAR FP=21/270, precision=0.993.',
        ha='center', va='center', fontsize=8.9, style='italic', color='#333',
    )
    fig.text(
        0.5, 0.035,
        'Saldırı yakalama davranışı koşulludur: Loud/Stealth-Gauss\'ta TPR≈1; '
        'LabelFlip ve Adaptive-Gauss\'ta detection-incomplete fakat utility-preserving rejim.',
        ha='center', va='center', fontsize=8.5, color='#555',
    )

    out_png = OUT_DIR / 'fig_graphical_abstract.png'
    out_pdf = OUT_DIR / 'fig_graphical_abstract.pdf'
    plt.savefig(out_png, dpi=200, bbox_inches='tight')
    plt.savefig(out_pdf, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'✓ {out_png}')
    print(f'✓ {out_pdf}')


if __name__ == '__main__':
    print('Graphical Abstract (Faz 2b) üretiliyor...')
    plot_graphical_abstract()
    print('Bitti.')
