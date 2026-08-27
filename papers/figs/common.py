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

# Mass-segregated heavy-remnant extension (referee M1): stellar-mass BHs and
# neutron stars (1.4 Msun) as extra number-fraction components inside r_infl.
# The Gonzalez Prieto et al. (2025) growth models retain a core BH population whose
# global number fraction is ~0.1-1 per cent; mass segregation enhances the central
# value, so 1 per cent is the fiducial and 0.1 / 3 per cent bracket it.
#
# Referee-5 update (2026-07-30): the perturber BH mass is now 31 Msun, the mean mass
# of black holes inspiraling into the IMBH in the Gonzalez Prieto et al. (2025)
# models, which name 10 Msun as the assumption they are correcting.  Kick variance
# scales as <m^2>, so this raises <m^2> by a factor 8.0 at fixed f_BH.  M_BH_PERT_OLD
# reproduces the pre-R5 curves for comparison.
F_NS = 0.02            # neutron-star number fraction (all remnant variants)
F_BH_FID = 0.01        # fiducial segregated BH number fraction
F_BH_GRID = (0.001, 0.01, 0.03)
M_BH_PERT = 31.0       # Msun, GP2025 mean inspiraling BH mass
M_BH_PERT_OLD = 10.0   # Msun, pre-R5 assumption, retained for the comparison curve

def remnant_mf(f_bh, f_ns=F_NS, m_bh=M_BH_PERT):
    """Return (masses, weights) for the stellar MF + NS + BH remnant components."""
    masses = np.concatenate([MF_MASSES, np.array([1.4, m_bh]) * MSUN])
    weights = np.concatenate([MF_WEIGHTS * (1.0 - f_bh - f_ns),
                              np.array([f_ns, f_bh])])
    return masses, weights / weights.sum()

# --- adiabatic suppression of impulsive kicks (referee M5 / R5-O2) --------------
# For a bound orbit of semi-major axis a perturbed by a star passing at impact
# parameter b with speed v, the adiabatic parameter is x = omega_orb * tau_enc =
# (b/a)(v_orb/v).  The impulsive estimate holds only for x << 1; across the whole
# feasibility envelope x runs from 2.2 at the cluster stripping radius to 4.1e3 at
# the ISCO, so unbound cluster stars are adiabatically decoupled from every orbit
# in the envelope.  We use the Gnedin & Ostriker (1999) power-law correction rather
# than the Spitzer (1987) exp(-x^2) form, which over-suppresses; the power law is
# the conservative (less suppressing) choice and is calibrated against N-body.
# A(x) multiplies the second-order quantity, i.e. <delta^2> directly.
GAMMA_AD = 2.5

def adiabatic_factor(x, gamma_ad=GAMMA_AD):
    """Gnedin & Ostriker (1999) adiabatic correction A(x) = (1 + x^2)^(-gamma_ad)."""
    return (1.0 + np.asarray(x, dtype=float) ** 2) ** (-gamma_ad)

# Radius-dependent mid-infrared detection limit (referee M3): a swarm of radius r
# re-radiating L_waste does so at T_eff = (L / 4 pi r^2 sigma_SB)^{1/4}; which
# instrument bounds it depends on where that blackbody peaks.  Order-of-magnitude
# point-source limits at 5.43 kpc, degraded for crowding in the omega Cen core:
#   T >= 150 K  (peak < ~20 um) : JWST/MIRI, sub-arcsec PSF        ~ 1    Lsun
#   50-150 K    (peak 20-60 um) : WISE W3/W4, Spitzer/MIPS 24 um,
#                                 6-18 arcsec PSF, confusion-limited ~ 1e2 Lsun
#   T < 50 K    (peak > 60 um)  : Spitzer/MIPS 70 um only, heavily
#                                 confused in the core               ~ 2e4 Lsun
SIGMA_SB = 5.670e-8     # W m^-2 K^-4

def t_eff(L_W, r_m):
    """Effective re-radiation temperature of a swarm of radius r intercepting L."""
    return (L_W / (4 * np.pi * r_m**2 * SIGMA_SB)) ** 0.25

def L_lim_mir(T):
    """Piecewise instrument limit in W as a function of swarm T_eff (K)."""
    T = np.asarray(T, dtype=float)
    import numpy as _np
    LSUN_ = 3.828e26
    return _np.where(T >= 150.0, 1.0 * LSUN_,
                     _np.where(T >= 50.0, 1e2 * LSUN_, 2e4 * LSUN_))

L_EDD  = 1.26e31 * (M_BH / MSUN)         # W
MDOT_EDD = L_EDD / (0.1 * C**2)          # kg/s

def mdot_bondi():
    return 4 * np.pi * GM**2 * RHO_GAS / (SIGMA**2 + CS_GAS**2) ** 1.5

def v_orb(a_m):
    return np.sqrt(GM / a_m)

# --- D1: bound-cusp perturber model (OCS-MC-PHYSICS, sec:D1-MODEL, 2026-07-30) ---
# Sources: Gonzalez Prieto, Rodriguez & Cabrera 2025 (arXiv:2507.06316) for the
# cusp slopes and the perturber mass; Banares-Hernandez et al. 2025 for the
# extended dark component; Gnedin & Ostriker 1999 for the adiabatic kernel
# (already defined above as adiabatic_factor, shared with the unbound channel).
GAMMA_STAR = 1.3   # GP2025 measured (stellar cusp), main sequence + WD tail
GAMMA_NS   = 1.5   # interpolated (Alexander & Hopman strong-segregation value
                    # at m = 1.4, m_max = 31 Msun), D1.1.3; immaterial to <m^2>
GAMMA_BH   = 2.0   # GP2025 measured, gamma = 1.97-2.1

M_DARK_FID = 2.5e5      # Msun, extended dark component (Banares-Hernandez 2025)
M_DARK_LO  = 2.0e5
M_DARK_HI  = 3.0e5
M_BH_PERT_LO = 15.0     # Msun, lower joint anchor: ~half the GP2025 inspiraling
                        # mean, standing in for the segregation bias in that mean
N_STAR_CLUSTER = 7.0e6  # cluster-wide star count, D1.5
SEG_ENHANCE = 10.0      # x10 central segregation enhancement, D1.5.2 -- the
                        # model's one stipulated (not derived) free normalization
P_KOZAI_INCL = 0.775    # P(mutual inclination in (39.2 deg, 140.8 deg)) for an
                        # isotropic cusp = [cos(39.2deg) - cos(140.8deg)] / 2

def f_bh_global(m_dark_msun, m_bh_msun):
    """Cluster-wide black-hole number fraction from the dark-mass anchor."""
    n_bh = m_dark_msun / m_bh_msun
    return n_bh / N_STAR_CLUSTER

def f_bh_central(m_dark_msun=M_DARK_FID, m_bh_msun=M_BH_PERT, seg=SEG_ENHANCE):
    """Central (segregation-enhanced) black-hole number fraction, D1.5."""
    return seg * f_bh_global(m_dark_msun, m_bh_msun)

def species_table(f_bh, m_bh_msun=M_BH_PERT, f_ns=F_NS):
    """Bound-cusp species: list of (name, mass_kg, gamma_s, f_s).

    f_s is each species' share of the core-average number density N_STAR at
    r_infl; the light-species 0.70/0.30 MS/WD split matches the unbound
    channel's stellar mass function (MF_WEIGHTS).
    """
    f_light = 1.0 - f_bh - f_ns
    return [
        ("ms", 0.35 * MSUN, GAMMA_STAR, 0.70 * f_light),
        ("wd", 0.60 * MSUN, GAMMA_STAR, 0.30 * f_light),
        ("ns", 1.4 * MSUN, GAMMA_NS, f_ns),
        ("bh", m_bh_msun * MSUN, GAMMA_BH, f_bh),
    ]

def N_enclosed(r_m, gamma_s, f_s):
    """N_s(<r) for a species of density power law gamma_s and density
    fraction f_s of N_STAR at r_infl (D1.1)."""
    n_s0 = f_s * N_STAR
    return (4 * np.pi * n_s0 * R_INFL ** 3 / (3.0 - gamma_s)) * (r_m / R_INFL) ** (3.0 - gamma_s)

def sigma_loc(r_m, gamma_s):
    """Local 1-D Keplerian velocity dispersion of a power-law cusp (D1.2.1)."""
    return np.sqrt(GM / ((1.0 + gamma_s) * r_m))

def P_orb(a_m):
    return 2 * np.pi * np.sqrt(a_m ** 3 / GM)

STYLE = {
    "figure.figsize": (6.0, 4.2),
    "font.size": 9.5,
    "font.family": "serif",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
}
