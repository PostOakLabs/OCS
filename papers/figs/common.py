"""Shared constants for Paper E figures.

Fiducial system: M = 2e4 Msun Kerr IMBH in the omega Cen core.
All values match the text of engineered-imbh-paper.tex; change here, re-run all figs.
"""
import numpy as np

G      = 6.674e-11          # m^3 kg^-1 s^-2
C      = 2.998e8            # m s^-1
MSUN   = 1.989e30           # kg
AU     = 1.496e11           # m
PC     = 3.086e16           # m
YR     = 3.156e7            # s
LSUN   = 3.828e26           # W
MP     = 1.673e-27          # kg

M_BH    = 2.0e4 * MSUN
GM      = G * M_BH
RG      = GM / C**2                      # 3.0e9 cm = 3.0e7 m
SIGMA   = 21e3                           # m/s, 1-D dispersion near centre
V_REL   = np.sqrt(2.0) * SIGMA           # typical relative velocity
N_STAR  = 1.0e4 / PC**3                  # stars m^-3 (rho0 ~ 3e3 Msun/pc^3, <m> ~ 0.3)
R_INFL  = GM / SIGMA**2                  # ~0.2 pc
N_E     = 0.23e6                         # electrons m^-3 (oMEGACat VII)
RHO_GAS = 1.2 * N_E * MP                 # kg m^-3, He-corrected
CS_GAS  = 1.0e4                          # m/s sound speed (1e4 K ionized)

# Two-component stellar mass function: main sequence + white-dwarf tail
MF_MASSES = np.array([0.35, 0.60]) * MSUN
MF_WEIGHTS = np.array([0.70, 0.30])

L_EDD  = 1.26e31 * (M_BH / MSUN)         # W
MDOT_EDD = L_EDD / (0.1 * C**2)          # kg/s

def mdot_bondi():
    return 4 * np.pi * GM**2 * RHO_GAS / (SIGMA**2 + CS_GAS**2) ** 1.5

def v_orb(a_m):
    return np.sqrt(GM / a_m)

STYLE = {
    "figure.figsize": (6.0, 4.2),
    "font.size": 9.5,
    "font.family": "serif",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
}
