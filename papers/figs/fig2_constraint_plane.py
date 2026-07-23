"""Fig 2: constraint planes for an omega Cen installation.

Panel (a): the (P_comp, 1 - f_sink) plane -- JWST waste-heat exclusion for a
warm (inner-envelope) swarm, transport floor on 1 - f_sink, ambient Bondi fuel
ceiling, Eddington reference.  Matches sections 2.7 and 3.1 of the paper.

Panel (b) (referee M3): the (r, L_waste) plane.  A swarm of radius r
re-radiates its waste luminosity at T_eff = (L / 4 pi r^2 sigma_SB)^{1/4};
which instrument bounds it depends on where that blackbody peaks.  Wedges:
JWST/MIRI (warm, inner), WISE W3/W4 + Spitzer/MIPS 24 um (cool, mid), and
Spitzer/MIPS 70 um (cold, outer) with limits degraded for confusion/crowding
in the omega Cen core (limits from common.L_lim_mir).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import LSUN, AU, C, mdot_bondi, L_EDD, t_eff, L_lim_mir, STYLE

plt.rcParams.update(STYLE)

L_LIM = 1.0 * LSUN          # JWST MIR point-source limit at the kinematic centre (Paper C)
LEAK_FLOOR = 1e-4           # transport bound on 1 - f_sink (Appendix A.3)
P_FUEL = mdot_bondi() * C**2 / LSUN     # ambient Bondi ceiling in Lsun, MAD efficiency ~ 1

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0))

# ---------------- panel (a): (P_comp, 1 - f_sink), warm swarm ----------------
P = np.logspace(0, 10, 400)             # P_comp in Lsun
leak = np.logspace(-6, 0, 400)
PP, LK = np.meshgrid(P, leak)

ax.set_xscale("log"); ax.set_yscale("log")
ax.contourf(PP, LK, (PP * LK > L_LIM / LSUN).astype(int),
            levels=[0.5, 1.5], colors=["#c65b5b"], alpha=0.35)
ax.plot(P, np.clip((L_LIM / LSUN) / P, 1e-6, 1), color="#c65b5b", lw=1.5)
ax.text(2e7, 1.5e-2, "excluded by JWST waste heat\n(warm swarm, $r\\lesssim$ 3 AU)",
        fontsize=7.5, color="#8a3030", ha="center")

ax.axhspan(1e-6, LEAK_FLOOR, facecolor="none", edgecolor="0.75", hatch="//", lw=0.0, alpha=0.7)
ax.axhline(LEAK_FLOOR, color="0.35", lw=1.2, ls="--")
ax.text(3e0, 1.35e-4, "adopted transport floor $1-f_{\\rm sink}=10^{-4}$",
        fontsize=7, color="0.3")
ax.text(3e0, 2.2e-5, "below the floor: disfavoured by the A.3\naccounting, not excluded by data",
        fontsize=6.8, color="0.45")

ax.axvline(P_FUEL, color="#3b4d8f", lw=1.5, ls="--")
ax.text(P_FUEL * 0.5, 5e-1, "ambient Bondi ceiling\n($8\\times10^{5}\\,L_\\odot$)",
        fontsize=7.5, color="#2c3a6b", ha="right")
ax.axvline(L_EDD / LSUN, color="0.5", lw=1, ls="-.")
ax.text(L_EDD / LSUN * 1.3, 5e-1, "$L_{\\rm Edd}$", fontsize=7.5, color="0.4")

ax.text(1.1e2, 1.1e-3, "allowed today:\ndormant / low-power,\ndeep envelope", fontsize=7.5,
        color="#1c4d2e", ha="left",
        bbox=dict(fc="#e4efe6", ec="#1c4d2e", lw=0.8, alpha=0.9))

ax.set_xlabel("processed power  $P_{\\rm comp}$  [$L_\\odot$]")
ax.set_ylabel("radiated fraction  $1-f_{\\rm sink}$")
ax.set_xlim(1e0, 1e10); ax.set_ylim(1e-6, 1)
ax.set_title("(a)  warm-swarm plane", fontsize=9)

# ---------------- panel (b): (r, L_waste) with temperature axis --------------
r_AU = np.logspace(np.log10(2e-2), np.log10(4e3), 400)
L_grid = np.logspace(-2, 7, 500)        # L_waste in Lsun
RR, LL = np.meshgrid(r_AU * AU, L_grid * LSUN)
TT = t_eff(LL, RR)
excluded = LL > L_lim_mir(TT)

ax2.set_xscale("log"); ax2.set_yscale("log")
ax2.contourf(RR / AU, LL / LSUN, excluded.astype(int),
             levels=[0.5, 1.5], colors=["#c65b5b"], alpha=0.35)

# instrument wedge boundaries: minimum excluded L at each r
L_bound = np.array([L_grid[np.argmax(excluded[:, i])] if excluded[:, i].any()
                    else np.nan for i in range(len(r_AU))])
ax2.plot(r_AU, L_bound, color="#c65b5b", lw=1.5)

# temperature contours
cs = ax2.contour(RR / AU, LL / LSUN, TT, levels=[50, 150, 300, 1000],
                 colors="0.45", linewidths=0.8, linestyles=":")
ax2.clabel(cs, fmt=lambda v: f"{v:.0f} K", fontsize=6.5)

ax2.axhline(P_FUEL, color="#3b4d8f", lw=1.2, ls="--")
ax2.text(3e-2, P_FUEL * 2, "fuel ceiling ($L_{\\rm waste}$ if fully radiated)",
         fontsize=6.8, color="#2c3a6b")

ax2.text(2e-1, 3e2, "JWST/MIRI\n(warm, inner)", fontsize=7, color="#8a3030", ha="center")
ax2.text(6e1, 2e4, "WISE W3/W4,\nSpitzer/MIPS 24 $\\mu$m\n(confusion-limited)",
         fontsize=6.6, color="#8a3030", ha="center")
ax2.text(1.5e3, 3e6, "MIPS 70 $\\mu$m\nonly", fontsize=6.6, color="#8a3030", ha="center")
ax2.text(2.5e2, 3e0, "allowed: cool outer swarms\nevade the MIR bound", fontsize=7,
         color="#1c4d2e", ha="center",
         bbox=dict(fc="#e4efe6", ec="#1c4d2e", lw=0.8, alpha=0.9))

ax2.set_xlabel("swarm radius  $r$  [AU]")
ax2.set_ylabel("radiated waste luminosity  $L_{\\rm waste}$  [$L_\\odot$]")
ax2.set_xlim(2e-2, 4e3); ax2.set_ylim(1e-2, 1e7)
ax2.set_title("(b)  temperature-resolved plane", fontsize=9)

fig.tight_layout()
fig.savefig("fig2_constraint_plane.pdf"); fig.savefig("fig2_constraint_plane.png", dpi=110)
print("P_fuel_Lsun", P_FUEL, "L_edd_Lsun", L_EDD / LSUN)
