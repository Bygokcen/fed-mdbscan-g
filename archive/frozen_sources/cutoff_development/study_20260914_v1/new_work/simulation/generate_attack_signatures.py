"""
Saldırı Anatomi Figürü — Dört saldırı tipinin gradyan uzayındaki sezgisel imzası.

§2.4 (Zehirlenme Saldırı Aileleri) sonuna yerleştirilir; okur §5.5 mekanik
analizine girmeden önce her saldırı tipinin neden farklı TPR örüntüsü
ürettiğini görsel olarak anlar.

5 panel (2D sentetik gradyan uzayı temsili):
  (A) Clean             — sadece heterojen benign kümeler
  (B) Loud-Gaussian     — saldırganlar L0 trust-region'ın çok dışında
  (C) LabelFlip         — norm normal, yön kaymış (kısmi tespit zoru)
  (D) Stealth-Gaussian  — norm benign dağılıma kalibre, ayrı mikro-mod
  (E) Adaptive-Gaussian — saldırgan benign konsensüse yakın, detection-incomplete

Çıktı: new_work/FED-MDBSCAN_Paper/figures/fig_attack_signatures.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT_DIR = Path(__file__).resolve().parents[1] / 'FED-MDBSCAN_Paper' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'axes.titlesize': 11,
    'figure.dpi': 130,
    'savefig.dpi': 240,
    'savefig.bbox': 'tight',
})

# Renk paleti (paper genelinde tutarlı)
COL_BENIGN = '#2E86AB'   # mavi — dürüst gradyanlar
COL_MAL    = '#D62828'   # kırmızı — saldırgan gradyanlar
COL_GM     = '#1A1A1A'   # siyah — geometrik medyan
COL_TR     = '#888888'   # gri — L0 trust-region


def _benign_cluster(rng, n_per=10):
    """İki heterojen benign cluster üret (Non-IID temsilî)."""
    a = rng.randn(n_per, 2) * 0.32 + np.array([-0.85, 0.35])
    b = rng.randn(n_per, 2) * 0.30 + np.array([0.75, -0.25])
    return np.vstack([a, b])


def _draw_trust_region(ax, center=(0, 0), radius=1.6):
    """L0 trust-region (1.5×median dist) referansını dashed çember olarak çiz."""
    circle = plt.Circle(center, radius, fill=False, edgecolor=COL_TR,
                         linestyle='--', linewidth=1.2, alpha=0.8, zorder=1)
    ax.add_patch(circle)
    ax.text(center[0] + radius * 0.05, center[1] + radius - 0.10,
            r'L0 trust-region',
            fontsize=7.5, color=COL_TR, ha='left', va='top', alpha=0.85)


def _setup_axes(ax, title_letter, title_text):
    ax.set_xlim(-3.2, 3.2)
    ax.set_ylim(-3.2, 3.2)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ('top', 'right', 'left', 'bottom'):
        ax.spines[s].set_alpha(0.3)
    ax.set_title(f'({title_letter}) {title_text}',
                 fontsize=10.5, loc='left', pad=6, fontweight='bold')
    ax.set_xlabel('gradyan ekseni 1', fontsize=8.5, color='#666')
    ax.set_ylabel('gradyan ekseni 2', fontsize=8.5, color='#666')


# ──────────────────────────────────────────────────────────────────────
# PANELLER
# ──────────────────────────────────────────────────────────────────────
def panel_clean(ax):
    rng = np.random.RandomState(42)
    benign = _benign_cluster(rng)
    ax.scatter(benign[:, 0], benign[:, 1], s=72, c=COL_BENIGN,
               edgecolor='white', linewidth=0.8, zorder=3, label='Benign')
    ax.scatter([0], [0], s=140, c=COL_GM, marker='x', linewidth=2.4,
               zorder=4, label=r'$\mu_{\mathrm{GM}}$')
    _draw_trust_region(ax)
    _setup_axes(ax, 'A', 'Clean (saldırı yok)')
    ax.text(0, -2.85, 'Sadece heterojen benign kümeler',
            ha='center', fontsize=8.5, style='italic', color='#444')


def panel_loud(ax):
    rng = np.random.RandomState(7)
    benign = _benign_cluster(rng)
    mal = rng.randn(6, 2) * 0.5 + np.array([0.0, 2.6])  # uzakta saçılma
    ax.scatter(benign[:, 0], benign[:, 1], s=72, c=COL_BENIGN,
               edgecolor='white', linewidth=0.8, zorder=3)
    ax.scatter(mal[:, 0], mal[:, 1], s=180, c=COL_MAL, marker='*',
               edgecolor='white', linewidth=0.8, zorder=4)
    ax.scatter([0], [0], s=140, c=COL_GM, marker='x', linewidth=2.4, zorder=5)
    _draw_trust_region(ax)
    # Saldırı yönü oku
    ax.annotate('', xy=(0, 2.4), xytext=(0, 0.6),
                arrowprops=dict(arrowstyle='->', color=COL_MAL,
                                lw=1.6, alpha=0.7))
    _setup_axes(ax, 'B', 'Loud-Gaussian')
    ax.text(0, -2.85, 'L0 sınırının çok ötesinde — kolay tespit',
            ha='center', fontsize=8.5, style='italic', color='#444')


def panel_labelflip(ax):
    rng = np.random.RandomState(11)
    benign = _benign_cluster(rng)
    # LabelFlip: gradyan normu normal ama YÖNÜ farklı (benign cluster'ların
    # dışında ama L0 sınırı içinde, yana kaymış küme)
    mal = rng.randn(6, 2) * 0.30 + np.array([-0.05, -1.55])
    ax.scatter(benign[:, 0], benign[:, 1], s=72, c=COL_BENIGN,
               edgecolor='white', linewidth=0.8, zorder=3)
    ax.scatter(mal[:, 0], mal[:, 1], s=180, c=COL_MAL, marker='*',
               edgecolor='white', linewidth=0.8, zorder=4)
    ax.scatter([0], [0], s=140, c=COL_GM, marker='x', linewidth=2.4, zorder=5)
    _draw_trust_region(ax)
    # "yön kaydı" işareti
    ax.annotate('yön\nkayması', xy=(0, -1.5), xytext=(1.7, -1.2),
                fontsize=8, color=COL_MAL, ha='center',
                arrowprops=dict(arrowstyle='->', color=COL_MAL,
                                lw=1.2, alpha=0.6))
    _setup_axes(ax, 'C', 'LabelFlip')
    ax.text(0, -2.85, 'Norm normal, yön kaymış — kısmi tespit',
            ha='center', fontsize=8.5, style='italic', color='#444')


def panel_stealth(ax):
    rng = np.random.RandomState(19)
    benign = _benign_cluster(rng)
    # Stealth: norm benign dağılıma kalibre (L0 trust-region İÇİNDE) ama
    # AYRI bir mikro-mod oluşturuyor (yoğunluk uzayında ayırt edilebilir)
    mal = rng.randn(6, 2) * 0.18 + np.array([0.05, 1.20])
    ax.scatter(benign[:, 0], benign[:, 1], s=72, c=COL_BENIGN,
               edgecolor='white', linewidth=0.8, zorder=3)
    ax.scatter(mal[:, 0], mal[:, 1], s=180, c=COL_MAL, marker='*',
               edgecolor='white', linewidth=0.8, zorder=4)
    ax.scatter([0], [0], s=140, c=COL_GM, marker='x', linewidth=2.4, zorder=5)
    _draw_trust_region(ax)
    # Mikro-mod elipsi
    ax.add_patch(mpatches.Ellipse((0.05, 1.20), width=0.95, height=0.65,
                                   facecolor=COL_MAL, alpha=0.15,
                                   edgecolor=COL_MAL, linestyle=':',
                                   linewidth=1.4, zorder=2))
    ax.text(1.45, 1.20, 'ayrı\nmikro-mod', fontsize=8, color=COL_MAL,
            ha='left', va='center')
    _setup_axes(ax, 'D', 'Stealth-Gaussian (ours)')
    ax.text(0, -2.85, 'Norm gizli, yoğunlukta ayrı mod — yakalanır',
            ha='center', fontsize=8.5, style='italic', color='#444')


def panel_adaptive(ax):
    rng = np.random.RandomState(23)
    benign = _benign_cluster(rng)
    # Adaptive: saldırgan benign konsensüse YAKIN; gradyan benign cluster
    # içinde dağılır, ayırt edilemez
    mal = rng.randn(6, 2) * 0.42 + np.array([-0.40, 0.20])
    ax.scatter(benign[:, 0], benign[:, 1], s=72, c=COL_BENIGN,
               edgecolor='white', linewidth=0.8, zorder=3)
    ax.scatter(mal[:, 0], mal[:, 1], s=180, c=COL_MAL, marker='*',
               edgecolor='white', linewidth=0.8, zorder=4)
    ax.scatter([0], [0], s=140, c=COL_GM, marker='x', linewidth=2.4, zorder=5)
    _draw_trust_region(ax)
    ax.text(2.2, 0.4, 'benign\nyönü\ntaklit', fontsize=8, color=COL_MAL,
            ha='center', va='center')
    ax.annotate('', xy=(-0.3, 0.2), xytext=(1.6, 0.4),
                arrowprops=dict(arrowstyle='->', color=COL_MAL,
                                lw=1.2, alpha=0.6))
    _setup_axes(ax, 'E', 'Adaptive-Gaussian (ours)')
    ax.text(0, -2.85, 'Konsensüse yakın — detection-incomplete',
            ha='center', fontsize=8.5, style='italic', color='#444')


def panel_legend(ax):
    """6. panel: legend + saldırı imza özet metni."""
    ax.axis('off')
    # Legend handles
    handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=COL_BENIGN,
                   markersize=11, markeredgecolor='white', label='Benign gradyan'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor=COL_MAL,
                   markersize=15, markeredgecolor='white', label='Saldırgan gradyan'),
        plt.Line2D([0], [0], marker='x', color=COL_GM, markersize=11,
                   linestyle='None', markeredgewidth=2,
                   label=r'$\mu_{\mathrm{GM}}$ (geometrik medyan)'),
        plt.Line2D([0], [0], color=COL_TR, linestyle='--', linewidth=1.5,
                   label=r'L0 trust-region ($1.5\!\times\!$median)'),
    ]
    ax.legend(handles=handles, loc='upper center',
              fontsize=9.5, frameon=True, framealpha=0.9,
              bbox_to_anchor=(0.5, 0.95))
    # Özet tablo metni
    summary = (
        r'$\bf{Beklenen\ tespit\ \ddot{o}r\ddot{u}nt\ddot{u}s\ddot{u}}$' '\n'
        '─────────────────\n'
        'B. Loud-Gauss   →  TPR ≈ 1.00\n'
        'C. LabelFlip    →  TPR koşullu\n'
        'D. Stealth-G    →  TPR ≈ 0.99\n'
        'E. Adaptive-G   →  detection-\n'
        '                  incomplete'
    )
    ax.text(0.5, 0.42, summary, ha='center', va='center',
            fontsize=8.7, family='monospace',
            transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=0.5',
                      facecolor='#f5f5f5', edgecolor='#ccc'))


# ──────────────────────────────────────────────────────────────────────
def main():
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 10.0))

    panel_clean(axes[0, 0])
    panel_loud(axes[0, 1])
    panel_labelflip(axes[0, 2])
    panel_stealth(axes[1, 0])
    panel_adaptive(axes[1, 1])
    panel_legend(axes[1, 2])

    fig.suptitle(
        'Şekil — Saldırı Anatomileri: Dört Saldırı Tipinin Gradyan Uzayındaki Sezgisel İmzası',
        fontsize=12.5, fontweight='bold', y=0.99,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.96])

    pdf = OUT_DIR / 'fig_attack_signatures.pdf'
    png = OUT_DIR / 'fig_attack_signatures.png'
    plt.savefig(pdf, dpi=200)
    plt.savefig(png, dpi=200)
    plt.close(fig)
    print(f'✓ {png}')
    print(f'✓ {pdf}')


if __name__ == '__main__':
    print('Saldırı Anatomi figürü üretiliyor...')
    main()
    print('Bitti.')
