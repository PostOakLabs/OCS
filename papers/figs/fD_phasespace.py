"""Figure: phase-space diagram of the migration decision for Paper D
(economics-paper.tex, Fig.~\ref{fig:phasespace}, placed in Section sec:hybrid
after the paragraph containing Eq. eq:hybrid).

Plane: destination multiplier G (log, 1e3-1e12) against the combined
discount-plus-hazard rate rho+lambda (log, 1e-6-1e-2 /yr), at the fiducials
p_s = 0.5 and tau = 1e5 yr (Table 2).

Boundaries (exact curves, transcribed from the paper):

  migration threshold (Eq. eq:threshold):
      rho* (G)      = ln(G p_s)/tau        = ln(0.5 G)/1e5
  hybrid breakeven (Eq. eq:hybrid at f = 1e-6):
      rho_hyb (G)   = ln(G p_s / f)/tau    = ln(5e5 G)/1e5
    (= 1.7 rho* at the fiducial G = 1e9; the paper quotes ln(5e14)/1e5 = 34)

Regions (dominance structure of Sections sec:crossover and sec:hybrid):

  green  below rho*:    migration clears (M > S); the hybrid weakly dominates
                         pure M there under the seed-fidelity assumption
  orange between lines:  the hybrid band - H > S while M < S; seed-and-stay
                         dominates to 1.7 rho* at f = 1e-6
  blue   above rho_hyb:  S dominates; neither migration nor seeding pays

Fiducial star: (G = 1e9, rho+lambda = 2e-4 /yr), which sits on the migration
threshold (Section sec:crossover: rho* = 2.0e-4 /yr at the fiducials).

Colours: blue = S (conservative/stay), green = M (migration), orange = H
(hybrid) - matching the series palette used in the Paper A flowchart.

Run:  python fD_phasespace.py
Writes fD_phasespace.pdf / .png / .json next to this script.
"""

from __future__ import annotations

import json
import os

import numpy as np                      # noqa: E402
import matplotlib                       # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

TAU = 1e5          # yr, fiducial transit + construction (Table 2)
P_S = 0.5          # transit survival fiducial (Table 2)
F_SEED = 1e-6      # fiducial seed cost (Section sec:hybrid)

BLUE_D, BLUE_F = "#1a5276", "#d6eaf8"
GREEN_D, GREEN_F = "#1e8449", "#d5f5e3"
ORANGE_D, ORANGE_F = "#b9770e", "#fdebd0"
GOLD = "#f1c40f"

plt.rcParams.update({
    "figure.figsize": (6.6, 4.7),
    "font.size": 9.5,
    "font.family": "serif",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

G = np.logspace(3, 12, 600)
rho_M = np.log(P_S * G) / TAU          # migration threshold (Eq. eq:threshold)
rho_H = np.log(P_S * G / F_SEED) / TAU  # hybrid breakeven (Eq. eq:hybrid)

fig, ax = plt.subplots()

# Regions (bottom to top): M clears / hybrid band / S dominates.
ax.fill_between(G, 1e-6, rho_M, color=GREEN_F, alpha=0.55, lw=0, zorder=0)
ax.fill_between(G, rho_M, rho_H, color=ORANGE_F, alpha=0.65, lw=0, zorder=0)
ax.fill_between(G, rho_H, 1e-2, color=BLUE_F, alpha=0.55, lw=0, zorder=0)

ax.plot(G, rho_M, color=GREEN_D, lw=1.9, zorder=3)
ax.plot(G, rho_H, color=ORANGE_D, lw=1.9, zorder=3)

# Boundary labels.
ax.text(1.1e11, 2.16e-4, r"migration threshold  $\rho^{*} = \ln(G\,p_{s})/\tau$",
        fontsize=7.8, color=GREEN_D, ha="center", va="top", zorder=4)
ax.text(1.6e3, 3.15e-4, r"hybrid breakeven  $\rho+\lambda = \ln(G\,p_{s}/f)/\tau$",
        fontsize=7.8, color=ORANGE_D, ha="left", va="bottom", zorder=4)

# Region labels.
ax.text(1.15e3, 1.5e-3, "S region:\nstay and densify\ndominates",
        fontsize=8.2, color=BLUE_D, ha="left", va="top", zorder=4)
ax.text(10**4.9, 1.35e-3, "hybrid band:\nseed-and-stay dominates\nto $1.7\\,\\rho^{*}$  ($f = 10^{-6}$)",
        fontsize=8.2, color=ORANGE_D, ha="left", va="top", zorder=4)
ax.annotate("", xy=(10**6.3, 1.9e-4), xytext=(10**5.6, 1.02e-3),
            arrowprops=dict(arrowstyle="->", color=ORANGE_D, lw=1.0), zorder=4)
ax.text(10**8, 4.2e-5, "M region:\nmigration clears\n($\\rho+\\lambda < \\rho^{*}$);\nhybrid $H \\geq M$",
        fontsize=8.2, color=GREEN_D, ha="center", va="center", zorder=4)

# Fiducial star: on the migration threshold at G = 1e9.
ax.plot([1e9], [2.0e-4], marker="*", markersize=17, mfc=GOLD, mec="k",
        mew=1.1, zorder=6)
ax.annotate("fiducial\n$G = 10^{9}$, $\\rho+\\lambda = 2{\\times}10^{-4}\\,\\mathrm{yr}^{-1}$",
            xy=(1e9, 2.0e-4), xytext=(2.5e9, 1.02e-4), fontsize=8,
            color="#333333", ha="left", va="top", zorder=6,
            arrowprops=dict(arrowstyle="->", color="#333333", lw=0.9))

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(1e3, 1e12)
ax.set_ylim(1e-6, 1e-2)
ax.set_xlabel(r"destination multiplier $G$")
ax.set_ylabel(r"combined discount-plus-hazard rate $\rho+\lambda$ [yr$^{-1}$]")

fig.savefig(os.path.join(HERE, "fD_phasespace.pdf"))
fig.savefig(os.path.join(HERE, "fD_phasespace.png"))

record = {
    "tau_yr": TAU,
    "p_s": P_S,
    "f_seed": F_SEED,
    "migration_threshold": "rho* = ln(0.5 G)/1e5  (Eq. eq:threshold)",
    "hybrid_breakeven": "rho+lambda = ln(5e5 G)/1e5 at f=1e-6  (Eq. eq:hybrid); "
                        "= 1.7 rho* at G=1e9",
    "fiducial_star": {"G": 1e9, "rho_plus_lambda_per_yr": 2.0e-4},
    "regions": {
        "green_below_threshold": "migration clears (M > S); hybrid H >= M",
        "orange_band": "hybrid band: H > S, M < S (to 1.7 rho* at f=1e-6)",
        "blue_above": "S dominates",
    },
    "G_range": [1e3, 1e12],
    "rho_range_per_yr": [1e-6, 1e-2],
}
with open(os.path.join(HERE, "fD_phasespace.json"), "w", encoding="utf-8") as fh:
    json.dump(record, fh, indent=2)
print("wrote fD_phasespace.pdf / .png / .json")
