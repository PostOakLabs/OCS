"""Fig 4: schematic power spectra defining the MAD-regulation statistic R.

Illustrative (no data): red-noise continuum plus the flux-eruption band that
GRMHD baselines predict for a natural MAD at the fiducial mass (1e-3 to 1e-1 Hz
for M = 2e4 Msun), and the regulated spectrum with the band suppressed.
R = integrated band power / GRMHD expectation at matched mean luminosity.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import STYLE

plt.rcParams.update(STYLE)
f = np.logspace(-5, 1, 500)

continuum = f ** -1.2
bump = 8.0 * np.exp(-0.5 * ((np.log10(f) + 2.0) / 0.45) ** 2)   # eruption band at ~1e-2 Hz
natural = continuum * (1 + bump)
regulated = continuum * (1 + 0.03 * bump)

fig, ax = plt.subplots(figsize=(6.0, 3.6))
ax.loglog(f, natural, color="#c65b5b", lw=2, label="natural MAD (GRMHD baseline): $R \\sim 1$")
ax.loglog(f, regulated, color="#3b4d8f", lw=2, label="regulated inflow: $R \\ll 10^{-1}$")
ax.loglog(f, continuum, color="0.6", lw=1, ls=":", label="red-noise continuum")
ax.axvspan(1e-3, 1e-1, color="#b98a2e", alpha=0.12)
ax.text(1e-2, 2e4, "flux-eruption band\n($10^{2}$--$10^{3}\\,r_{\\rm g}/c$;\n"
                   "$10^{-3}$--$10^{-1}$ Hz at $2\\times10^{4}\\,M_\\odot$)",
        ha="center", fontsize=8, color="#7a5a1d")
ax.set_xlabel("frequency  [Hz]")
ax.set_ylabel("power spectral density  [arb.]")
ax.set_xlim(1e-5, 1e1); ax.set_ylim(1e-2, 1e6)
ax.legend(loc="lower left", fontsize=8)
fig.savefig("fig4_r_statistic.pdf"); fig.savefig("fig4_r_statistic.png", dpi=110)
print("fig4 done")
