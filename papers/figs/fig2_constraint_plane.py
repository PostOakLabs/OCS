"""Fig 2: the (P_comp, 1 - f_sink) constraint plane for an omega Cen installation.

Regions: JWST waste-heat exclusion (L_waste = (1-f_sink) P_comp > L_lim),
transport floor on 1 - f_sink, ambient Bondi fuel ceiling on P_comp,
Eddington reference. Matches sections 2.7 and 3.1 of the paper.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import LSUN, C, mdot_bondi, L_EDD, STYLE

plt.rcParams.update(STYLE)

L_LIM = 1.0 * LSUN          # JWST MIR point-source limit at the kinematic centre (Paper C)
LEAK_FLOOR = 1e-4           # transport bound on 1 - f_sink (Appendix A.3)
P_FUEL = mdot_bondi() * C**2 / LSUN     # ambient Bondi ceiling in Lsun, MAD efficiency ~ 1

P = np.logspace(0, 10, 400)             # P_comp in Lsun
leak = np.logspace(-6, 0, 400)
PP, LK = np.meshgrid(P, leak)

fig, ax = plt.subplots()
ax.set_xscale("log"); ax.set_yscale("log")

# JWST exclusion: L_waste = leak * P > L_lim
ax.contourf(PP, LK, (PP * LK > L_LIM / LSUN).astype(int),
            levels=[0.5, 1.5], colors=["#c65b5b"], alpha=0.35)
ax.plot(P, np.clip((L_LIM / LSUN) / P, 1e-6, 1), color="#c65b5b", lw=1.5)
ax.text(3e7, 1.5e-2, "excluded by JWST waste heat\n($L_{\\rm waste} > L_{\\rm lim}$)",
        fontsize=8, color="#8a3030", ha="center")

# transport floor: an adopted parameter (Appendix A.3 engineering estimate), drawn as
# a labelled line over light hatching rather than a hard boundary of the allowed region
ax.axhspan(1e-6, LEAK_FLOOR, facecolor="none", edgecolor="0.75", hatch="//", lw=0.0, alpha=0.7)
ax.axhline(LEAK_FLOOR, color="0.35", lw=1.2, ls="--")
ax.text(3e0, 1.35e-4, "adopted transport floor $1-f_{\\rm sink}=10^{-4}$ (see \\S6.1)",
        fontsize=8, color="0.3")
ax.text(3e0, 2.2e-5, "below the adopted floor: disfavoured by the A.3 accounting,\n"
                     "not excluded by data",
        fontsize=7.5, color="0.45")

# fuel ceiling and Eddington
ax.axvline(P_FUEL, color="#3b4d8f", lw=1.5, ls="--")
ax.text(P_FUEL * 0.5, 6e-1, "ambient Bondi ceiling\n($\\sim10^{6}\\,L_\\odot$; imports raise it)",
        fontsize=8, color="#2c3a6b", ha="right")
ax.axvline(L_EDD / LSUN, color="0.5", lw=1, ls="-.")
ax.text(L_EDD / LSUN * 1.3, 6e-1, "$L_{\\rm Edd}$", fontsize=8, color="0.4")

# allowed wedge annotation
ax.text(1.2e2, 1.1e-3, "allowed today:\ndormant / low-power,\ndeep envelope", fontsize=8.5,
        color="#1c4d2e", ha="left",
        bbox=dict(fc="#e4efe6", ec="#1c4d2e", lw=0.8, alpha=0.9))

ax.set_xlabel("processed power  $P_{\\rm comp}$  [$L_\\odot$]")
ax.set_ylabel("radiated fraction  $1-f_{\\rm sink}$")
ax.set_xlim(1e0, 1e10); ax.set_ylim(1e-6, 1)
fig.savefig("fig2_constraint_plane.pdf"); fig.savefig("fig2_constraint_plane.png", dpi=110)
print("P_fuel_Lsun", P_FUEL, "L_edd_Lsun", L_EDD / LSUN)
