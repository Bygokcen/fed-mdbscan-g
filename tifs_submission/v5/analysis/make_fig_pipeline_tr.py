"""Fig.: Fed-MDBSCAN-G decision path (a) and an illustrative 2-D example (b).

Panel (b) runs the deployed stage functions from new_work/simulation/mdbscan.py
on synthetic 2-D points; it is a schematic, not experimental data.
"""
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon
from scipy.spatial import ConvexHull

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "new_work"))
from simulation import mdbscan as MD

C_S1 = "#2C6FAC"    # Stage 1 (geometric-median anchor)
C_S3 = "#C9791A"    # Stages 2-3 (MDBSCAN adaptation)
C_ACC = "#3A3A3A"   # accepted
C_BOX = "#F2F2F2"
LBL = dict(boxstyle="square,pad=0.1", fc="white", ec="none")  # label backing over circle lines


def scene(seed=3):
    rng = np.random.default_rng(seed)
    core = rng.normal([0, 0], 0.55, (44, 2))
    hA = rng.normal([1.9, 1.2], 0.35, (6, 2))
    hB = rng.normal([-1.6, 1.5], 0.35, (5, 2))
    adv = rng.normal([4.6, -2.2], 0.12, (8, 2))
    X = np.vstack([core, hA, hB, adv])
    lab = np.array([0] * 44 + [1] * 6 + [2] * 5 + [3] * 8)
    return X, lab


def run_stages(X, k=5):
    n = len(X)
    B0, dist = MD._geometric_trust_region_filter(X, 2.5)
    m = MD._weiszfeld_geometric_median(X)
    rd = MD.compute_relative_density(X, k)
    t, gap, _ = MD._auto_estimate_t(rd, 10.0)
    gate = gap and (n - len(B0)) >= max(2, int(np.ceil(0.05 * n)))
    assert gate, "toy scene must open the gate"
    L = np.where(rd < t)[0]
    eps = MD._auto_estimate_eps(X, k, exclude_indices=set(L.tolist()))
    clusters, _ = MD.snnc(X[L], k, eps=eps, original_indices=L)
    m0 = MD._weiszfeld_geometric_median(X[B0])
    R0 = max(1e-10, float(np.median(np.linalg.norm(X[B0] - m0, axis=1))))
    groups = []
    for c in clusters:
        ok = MD._geometric_consensus_validation(X, c, B0, 2.0)
        groups.append((np.asarray(c), ok, np.linalg.norm(X[c].mean(0) - m0) / (2 * R0)))
    rej = set(i for c, ok, _ in groups if not ok for i in c)
    B = sorted(set(B0) - rej)
    if len(B) < n / 2:
        B = sorted(B0)
    return dict(B0=B0, m=m, r_s1=2.5 * float(np.median(dist)), m0=m0, R0=R0, groups=groups, B=B)


def box(ax, x, y, w, h, title, body, color, fs_t, fs_b):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                                fc=C_BOX if color is None else mpl.colors.to_rgba(color, 0.10),
                                ec="0.45" if color is None else color, lw=0.9))
    ax.text(x + 0.012, y + h - 0.012, title, ha="left", va="top", fontsize=fs_t, weight="bold",
            color="0.2" if color is None else color)
    if body:
        ax.text(x + 0.012, y + h - 0.012 - 0.052, body, ha="left", va="top", fontsize=fs_b, linespacing=1.25)


def arrow(ax, p0, p1, color="0.35", text=None, tx=None, fs=6):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", lw=0.8, color=color,
                                                      shrinkA=0, shrinkB=0, mutation_scale=7))
    if text:
        ax.text(*tx, text, fontsize=fs, color=color, ha="left", va="center")


def draw(out_stem, apply_style):
    apply_style(sizes=(8, 7, 6))
    fig = plt.figure(figsize=(7.16, 3.35))
    axA = fig.add_axes([0.005, 0.01, 0.555, 0.95]); axA.set_axis_off()
    axA.set_xlim(0, 1); axA.set_ylim(0, 1)
    axB = fig.add_axes([0.605, 0.17, 0.39, 0.74])

    # ---------------- (a) decision path ----------------
    X0, W = 0.035, 0.70
    rows = [  # (y, h, title, body, color)
        (0.905, 0.075, r"$r$ turundaki istemci güncellemeleri $u_1,\dots,u_n$", None, None),
        (0.690, 0.175, "Aşama 1: geometrik medyan kabul bölgesi",
         "$m$ = tüm güncellemelerin geometrik medyanı (Weiszfeld)\n"
         r"$B_0=\{i:\ \|u_i-m\|\leq 2.5\times$ medyan uzaklık$\}$" "\n"
         r"$|B_0|<n/2$ ise $B_0=U$ olarak sıfırla", C_S1),
        (0.455, 0.195, "Aşama 2: göreli yoğunluk kapısı",
         r"$\mathrm{rd}_i=k'/\sum$ ($k'$ en yakın komşu uzaklığı), $k'=5$" "\n"
         r"en büyük rd boşluğu $>10\times$ medyan boşluk ve" "\n"
         r"$\geq\max(2,\lceil 0.05n\rceil)$ Aşama-1 reddi varsa açılır; 3 turluk bellek", C_S3),
        (0.225, 0.190, "Aşama 3: küme doğrulama",
         r"düşük yoğunluklu $L=\{i:\mathrm{rd}_i<t\}$ kümesinde SNN kümeleme" "\n"
         r"$\|c_S-m_{B_0}\|>\tau R_0$ ise $S$ grubunu reddet, $\tau=2$" "\n"
         r"$R_0$ = $B_0$ içinde $m_{B_0}$ noktasına medyan uzaklık", C_S3),
        (0.085, 0.105, r"Birleştir: $B=B_0\setminus$(reddedilen gruplar)",
         r"valf: $|B|<n/2$ ise $B=B_0$ geri yüklenir", None),
    ]
    for y, h, t_, b_, c_ in rows:
        box(axA, X0, y, W, h, t_, b_, c_, 7, 6)
    xc = X0 + 0.30
    for (y1, h1, *_), (y2, h2, *_) in zip(rows[:-1], rows[1:]):
        arrow(axA, (xc, y1), (xc, y2 + h2))
    axA.text(xc + 0.012, (rows[2][0] + rows[3][0] + rows[3][1]) / 2, "kapı açık", fontsize=6, color=C_S3, va="center")
    # aggregate + bypass
    axA.text(xc, 0.012, r"birleştirme: $w_{r+1}=w_r+$ ($i\in B$ için $u_i$ ortalaması)", fontsize=7, ha="center", va="bottom")
    arrow(axA, (xc, rows[4][0]), (xc, 0.050))
    xr = X0 + W
    ymid = rows[2][0] + rows[2][1] / 2
    axA.plot([xr, xr + 0.06, xr + 0.06], [ymid, ymid, rows[4][0] + rows[4][1] / 2], color="0.35", lw=0.8)
    arrow(axA, (xr + 0.06, rows[4][0] + rows[4][1] / 2), (xr, rows[4][0] + rows[4][1] / 2))
    axA.text(xr + 0.07, ymid - 0.10, "kapı\nkapalı:\n$B=B_0$", fontsize=6, color="0.35", va="top")
    # provenance brackets (left margin)
    for (ya, yb, txt, col) in [(rows[1][0], rows[1][0] + rows[1][1], "geometrik medyan\nçapası", C_S1),
                               (rows[3][0], rows[2][0] + rows[2][1], "MDBSCAN'den\nuyarlandı", C_S3)]:
        axA.plot([X0 - 0.012] * 2, [ya, yb], color=col, lw=1.6, solid_capstyle="butt")
        axA.text(X0 - 0.022, (ya + yb) / 2, txt, rotation=90, fontsize=6, color=col, ha="right", va="center",
                 linespacing=1.1)
    axA.text(-0.005, 0.995, "a", fontsize=9, weight="bold", ha="left", va="top", transform=axA.transAxes)

    # ---------------- (b) illustrative example ----------------
    X, lab = scene(3)
    S = run_stages(X)
    inB = np.isin(np.arange(len(X)), S["B"])
    hon = lab != 3
    for mask, mk, label in [(hon, "o", None), (~hon, "^", None)]:
        acc, rej = mask & inB, mask & ~inB
        axB.scatter(*X[acc].T, s=11, marker=mk, c=C_ACC, lw=0, zorder=3)
        axB.scatter(*X[rej].T, s=13, marker=mk, facecolors="white", edgecolors=C_S1, lw=0.8, zorder=3)
    axB.add_patch(Circle(S["m"], S["r_s1"], fill=False, ls="--", lw=0.9, ec=C_S1, zorder=1))
    axB.add_patch(Circle(S["m0"], 2 * S["R0"], fill=False, ls=":", lw=1.0, ec=C_S3, zorder=1))
    axB.scatter(*S["m"], marker="*", s=55, c=C_S1, zorder=4, lw=0)
    for c, ok, ratio in S["groups"]:
        if ok or len(c) < 3:
            continue
        P = X[c]
        hull = P[ConvexHull(P).vertices]
        cen = P.mean(0)
        hull = cen + (hull - cen) * 1.0 + np.sign(hull - cen) * 0.18
        axB.add_patch(Polygon(hull, closed=True, fill=False, ec=C_S3, lw=0.9, zorder=2))
    # direct labels
    axB.text(S["m"][0] + S["r_s1"] * 0.78, S["m"][1] + S["r_s1"] * 0.80, "Aşama-1\nsınırı", color=C_S1, fontsize=6,
             ha="left", va="bottom")
    axB.text(S["m0"][0], S["m0"][1] - 2 * S["R0"] - 0.10, r"uzlaşma yarıçapı $\tau R_0$",
             color=C_S3, fontsize=6, ha="center", va="top", bbox=LBL, zorder=2.5)
    advc = X[lab == 3].mean(0)
    axB.text(advc[0], advc[1] + 0.50, "saldırganlar", fontsize=6, ha="center", va="bottom", color="0.2")
    hBc = X[lab == 2].mean(0)
    axB.text(hBc[0], hBc[1] - 0.55, "seyrek dürüst\ngrup", fontsize=6, ha="center", va="top", color="0.2", bbox=LBL, zorder=2.5)
    pts = np.vstack([X, S["m"] + S["r_s1"] * np.array([[1, 1], [-1, -1]])])
    lo, hi = pts.min(0) - 0.45, pts.max(0) + 0.45
    axB.set_xlim(lo[0], hi[0]); axB.set_ylim(lo[1] - 0.35, hi[1] + 0.25)
    axB.set_aspect("equal"); axB.set_xticks([]); axB.set_yticks([])
    for s in axB.spines.values():
        s.set_visible(True); s.set_color("0.6"); s.set_linewidth(0.6)
    axB.set_title("Açıklayıcı 2 boyutlu örnek (sentetik noktalar)", fontsize=7, loc="left", pad=3)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", ms=3.5, mfc=C_ACC, mec=C_ACC, label="dürüst, kabul"),
         Line2D([], [], marker="o", ls="", ms=3.5, mfc="white", mec=C_S1, label="dürüst, dışlandı"),
         Line2D([], [], marker="^", ls="", ms=3.8, mfc="white", mec=C_S1, label="saldırgan, dışlandı"),
         Line2D([], [], marker="*", ls="", ms=6, mfc=C_S1, mec=C_S1, label=r"geometrik medyan $m$"),
         Polygon([[0, 0]], closed=True, fill=False, ec=C_S3, lw=0.9, label="Aşama 3'ün reddettiği grup")]
    axB.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=6, handlelength=1.2,
               handletextpad=0.3, columnspacing=0.8, frameon=False)
    fig.text(0.585, 0.955, "b", fontsize=9, weight="bold", ha="left", va="top")
    for ext in ("pdf", "png"):
        fig.savefig(f"{out_stem}.{ext}", dpi=300)
    return fig, S, X, lab


def apply_style(sizes=(8, 7, 6)):
    base, mid, small = sizes
    mpl.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.size": base,
                         "axes.titlesize": mid, "legend.fontsize": small,
                         "savefig.bbox": "tight", "savefig.pad_inches": 0.1})


if __name__ == "__main__":
    mpl.use("Agg")
    out = REPO / "tifs_submission" / "v5" / "manuscript" / "figures" / "fed_mdbscan_g_pipeline_tr"
    draw(str(out), apply_style)
