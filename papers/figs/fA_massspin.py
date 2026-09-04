"""Figure: mass-spin plane for Paper A (mth-paper.tex, Fig.~\ref{fig:massspin}).

Black-hole mass (log axis, 10-10^7 Msun) against dimensionless spin, showing:

  * stellar-mass holes with continuum-fitting spin measurements (blue, the
    series' compact-object colour), representative values as compiled in
    Reynolds 2021 (cited in the paper's Section 7):
      Cyg X-1      M = 21.2 +- 2.2 Msun,  a* = 0.95 +- 0.06
      GRS 1915+05  M = 12.4 +- 1.9 Msun,  a* = 0.98 +- 0.01
      LMC X-3      M = 7.0  +- 0.6 Msun,  a* = 0.84 +- 0.12
  * the omega Cen contested band, 8e3-5e4 Msun (Table 3 / Section 9 text),
    spin unknown (red hatch, the series' extended/contested colour);
  * IMBH candidates with mass upper limits only, spin unconstrained:
    47 Tuc <~2.3e3 Msun (Kiziltan+ 2017; not required by Mann+ 2019) and
    M15 <~1e3-1e4 Msun model-dependent (Greene 2020) - grey left-arrows;
  * Sgr A*, 4.3e6 Msun, spin inferred high (grey open symbol);
  * the P2 selection region, 1e3-1e5 Msun at a* > 0.9 (green, the series'
    safe/selected colour; Section 3.1 criteria 1-2);
  * the Thorne 1974 spin-equilibrium limit a* = 0.998;
  * a schematic LISA EMRI mass-reach curve at 5.49 kpc, anchored at the T4
    threshold (a clean chirp measures M down to 5e3 Msun; Table 4), drawn
    slightly deeper at high spin where the inspiral spends more cycles in
    band.  Schematic: the paper quotes the threshold, not a curve.

Run:  python fA_massspin.py
Writes fA_massspin.pdf / .png / .json next to this script.
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Series colours: blue = compact, red = extended/contested, green = selected.
BLUE, RED, GREEN = "#1a5276", "#922b21", "#1e8449"
GREY = "#666666"
PURPLE = "#6c3483"

plt.rcParams.update({
    "figure.figsize": (6.4, 4.4),
    "font.size": 9.5,
    "font.family": "serif",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Representative continuum-fitting values (compilation: Reynolds 2021).
STELLAR = {
    "Cyg X-1":     (21.2, 2.2, 0.95, 0.06),
    "GRS 1915+05": (12.4, 1.9, 0.98, 0.01),
    "LMC X-3":     (7.0, 0.6, 0.84, 0.12),
}

fig, ax = plt.subplots()

# P2 selection region: 1e3-1e5 Msun at a* > 0.9.
ax.axvspan(1e3, 1e5, ymin=0.90, ymax=1.0, facecolor=GREEN, alpha=0.16,
           edgecolor=GREEN, linewidth=0.8, zorder=0)
ax.text(6e3, 0.945, "P2 selection region\n$10^{3}$--$10^{5}\\,M_\\odot$, $a_\\star \\gtrsim 0.9$",
        ha="center", va="center", fontsize=8, color=GREEN, zorder=3)

# Thorne limit.
ax.axhline(0.998, color="k", lw=1.0, ls="-.", zorder=2)
ax.text(3e5, 0.978, "Thorne limit $a_\\star = 0.998$", fontsize=7.6,
        ha="center", va="top", color="k")

# Stellar-mass holes with measured spins.
for name, (m, me, s, se) in STELLAR.items():
    ax.errorbar(m, s, xerr=me, yerr=se, fmt="o", color=BLUE,
                markersize=5.5, capsize=2.5, elinewidth=1.0, zorder=4)
    ax.annotate(name, (m, s), xytext=(4, -11), textcoords="offset points",
                fontsize=7.6, color=BLUE)

# omega Cen contested band, spin unknown.
ax.axvspan(8e3, 5e4, facecolor=RED, alpha=0.10, hatch="///", edgecolor=RED,
           linewidth=0.8, zorder=1)
ax.text(2.0e4, 0.30, "$\\omega$ Cen\n$8{\\times}10^{3}$--$5{\\times}10^{4}\\,M_\\odot$\n(contested; spin unknown)",
        ha="center", va="center", fontsize=8, color=RED, zorder=3)

# IMBH candidates with mass upper limits only, spin unconstrained:
# left-pointing arrows at a representative height.
ax.annotate("", xy=(1.3e3, 0.80), xytext=(2.3e3, 0.80),
            arrowprops=dict(arrowstyle="->", color=GREY, lw=1.1))
ax.text(2.45e3, 0.815, "47 Tuc ($\\lesssim 2.3{\\times}10^{3}\\,M_\\odot$)",
        fontsize=7.2, color=GREY, ha="left", va="bottom")
ax.annotate("", xy=(5.6e3, 0.66), xytext=(1.0e4, 0.66),
            arrowprops=dict(arrowstyle="->", color=GREY, lw=1.1))
ax.text(1.15e4, 0.675, "M15 ($\\lesssim 10^{3\\text{--}4}\\,M_\\odot$, model-dep.)",
        fontsize=7.2, color=GREY, ha="left", va="bottom")

# Sgr A*.
ax.errorbar(4.3e6, 0.90, yerr=0.10, fmt="o", color=GREY, markersize=6,
            mfc="none", capsize=2.5, elinewidth=1.0, zorder=4)
ax.annotate("Sgr A*", (4.3e6, 0.90), xytext=(5, 7), textcoords="offset points",
            fontsize=7.6, color=GREY)

# Schematic LISA EMRI mass reach at 5.49 kpc, anchored at the T4 threshold:
# minimum detectable mass (x) as a function of spin (y).
spins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
reach = [5e3 * (0.70 + 0.30 * (1.0 - s)) for s in spins]
ax.plot(reach, spins, ls="--", lw=1.3, color=PURPLE, zorder=2)
ax.text(5.35e3, 0.42, "LISA EMRI reach at 5.49 kpc (schematic; T4: clean chirp to $5{\\times}10^{3}\\,M_\\odot$)",
        rotation=90, fontsize=7.2, color=PURPLE, ha="left", va="center",
        zorder=3)

ax.set_xscale("log")
ax.set_xlim(10, 1e7)
ax.set_ylim(0, 1.02)
ax.set_xlabel(r"$M_{\rm BH}\ (M_\odot)$")
ax.set_ylabel(r"dimensionless spin $a_\star$")

fig.savefig(os.path.join(HERE, "fA_massspin.pdf"))
fig.savefig(os.path.join(HERE, "fA_massspin.png"))

record = {
    "stellar_mass_bh": {k: {"M_msun": v[0], "M_err": v[1], "a_star": v[2],
                            "a_err": v[3]} for k, v in STELLAR.items()},
    "omega_cen_band_msun": [8e3, 5e4],
    "omega_cen_source": "Section 9 / Table 3 of mth-paper.tex (contested range)",
    "selection_region": {"M_msun": [1e3, 1e5], "a_star_min": 0.9},
    "thorne_limit": 0.998,
    "sgr_a_star": {"M_msun": 4.3e6, "a_star": 0.90, "a_err": 0.10},
    "imbh_upper_limits": {"47Tuc_msun": 2.3e3, "M15_msun": "1e3-1e4 model-dependent"},
    "lisa_curve": "schematic, anchored at T4 threshold 5e3 Msun (Table 4)",
    "spin_sources": "stellar spins: continuum fitting, compiled in Reynolds 2021",
}
with open(os.path.join(HERE, "fA_massspin.json"), "w", encoding="utf-8") as fh:
    json.dump(record, fh, indent=2)
print("wrote fA_massspin.pdf / .png / .json")
