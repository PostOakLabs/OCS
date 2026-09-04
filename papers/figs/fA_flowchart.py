"""Figure: argument flowchart for Paper A (mth-paper.tex, Fig.~\ref{fig:flowchart}).

The paper's argument chain as a left-to-right cascade, coloured by the
epistemic register of Section 1.1 (Claims):

  green  = speculative postulates (P1 optimization pressure, P3 quiet migration)
  blue   = established physics (P2 thermodynamic gradient, Section 4 numbers)
  orange = selection theory (Section 3.1 criteria, applied to omega Cen in Section 5)
  red    = falsification framework (Section 7, T1-T6, decision tree Fig. 8)

Every quantitative anchor is transcribed from the paper's own text:
  P2  accretion 5.7-42 per cent vs fusion 0.7 per cent  (Sec. 4.1, Eq. 1)
      entropy sink ~10^12 vs the CMB                    (Sec. 4.2, Fig. 5)
      storage ~10^86 bits at 2e4 Msun                   (Sec. 4.3 / abstract)
  Sel.  omega Cen: 4e6 Msun, 12.08 Gyr, 5.49 kpc, rho_c 3e3 Msun/pc^3
                                                        (Table 2)
  Fals. T1-T6 with thresholds and timelines              (Table 4)

Branches: P4 -> the omega Cen application (Section 5); falsification
framework -> the decision tree (Fig. 8, fig:tree).

Run:  python fA_flowchart.py
Writes fA_flowchart.pdf / .png next to this script.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Series/epistemic colours: blue = established, green = speculative,
# orange = selection theory, red = falsification.
C = {
    "blue":  ("#1a5276", "#d6e4f0"),
    "green": ("#1e8449", "#d5f5e3"),
    "orange": ("#b9770e", "#fdebd0"),
    "red":   ("#922b21", "#fadbd8"),
}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

fig, ax = plt.subplots(figsize=(10.6, 4.9))
ax.set_xlim(0, 10.6)
ax.set_ylim(0, 4.9)
ax.axis("off")

BOX_W, BOX_H = 1.52, 1.62
ROW_Y = 2.55          # bottom of the main row
BRANCH_Y = 0.35       # bottom of the branch boxes


def box(x_center, y_bottom, w, h, edge, face, title, anchor, title_fs=8.6,
        anchor_fs=7.2):
    ax.add_patch(FancyBboxPatch(
        (x_center - w / 2, y_bottom), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.3, edgecolor=edge, facecolor=face, zorder=2))
    ax.text(x_center, y_bottom + h - 0.16, title, ha="center", va="top",
            fontsize=title_fs, fontweight="bold", color=edge, zorder=3)
    ax.text(x_center, y_bottom + h - 0.52, anchor, ha="center", va="top",
            fontsize=anchor_fs, color="#222222", zorder=3, linespacing=1.45)


def arrow(x0, y0, x1, y1, color="#555555"):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=13,
        linewidth=1.4, color=color, zorder=1,
        shrinkA=1, shrinkB=1))


# --- main cascade ----------------------------------------------------------
xs = [0.95, 2.72, 4.49, 6.26, 8.03, 9.80]
box(xs[0], ROW_Y, BOX_W, BOX_H, *C["green"],
    "P1  Optimization\npressure",
    "computation is the\nuniversal currency")
box(xs[1], ROW_Y, BOX_W, BOX_H, *C["blue"],
    "P2  Thermo.\ngradient",
    "accretion 5.7\u201342%\nvs fusion 0.7%\nentropy sink $10^{12}$\nstorage $10^{86}$ bits")
box(xs[2], ROW_Y, BOX_W, BOX_H, *C["green"],
    "P3  Quiet\nmigration",
    "electromagnetic\nquietness is a\nselection effect")
box(xs[3], ROW_Y, BOX_W, BOX_H, *C["green"],
    "P4  Observable\nresidue",
    "spin, depletion,\nneutrino bursts")
box(xs[4], ROW_Y, BOX_W, BOX_H, *C["orange"],
    "Selection\ncriteria",
    "\u03c9 Cen: $4{\\times}10^{6}\\,M_\\odot$\n12 Gyr, 5.49 kpc\n$\\rho_c$ $3{\\times}10^{3}\\,M_\\odot$/pc$^3$")
box(xs[5], ROW_Y, BOX_W, BOX_H, *C["red"],
    "Falsification\nframework",
    "T1\u2013T6 with\nthresholds and\ntimelines")

for i in range(5):
    arrow(xs[i] + BOX_W / 2, ROW_Y + BOX_H / 2,
          xs[i + 1] - BOX_W / 2, ROW_Y + BOX_H / 2)

# --- branches --------------------------------------------------------------
box(xs[3] + 0.35, BRANCH_Y, 2.05, 0.95, *C["orange"],
    "\u03c9 Cen application",
    "Section 5: the optimal\ntarget (Table 2)")
box(xs[5] - 0.35, BRANCH_Y, 2.05, 0.95, *C["red"],
    "decision tree",
    "Figure 8: LISA branch,\nT3\u2013T5 kills")

arrow(xs[3] + 0.25, ROW_Y, xs[3] + 0.35, BRANCH_Y + 0.95)
arrow(xs[5], ROW_Y, xs[5] - 0.35, BRANCH_Y + 0.95)

# --- legend ----------------------------------------------------------------
handles = [
    FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                   facecolor=C["green"][1], edgecolor=C["green"][0]),
    FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                   facecolor=C["blue"][1], edgecolor=C["blue"][0]),
    FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                   facecolor=C["orange"][1], edgecolor=C["orange"][0]),
    FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                   facecolor=C["red"][1], edgecolor=C["red"][0]),
]
ax.legend(handles,
          ["speculative postulate (P1, P3, P4)",
           "established physics (P2)",
           "selection theory",
           "falsification framework"],
          loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=4,
          frameon=False, fontsize=7.6, handlelength=1.1, handleheight=0.9,
          columnspacing=1.3)

fig.savefig(os.path.join(HERE, "fA_flowchart.pdf"))
fig.savefig(os.path.join(HERE, "fA_flowchart.png"))
print("wrote fA_flowchart.pdf / .png")
