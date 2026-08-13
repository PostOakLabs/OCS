"""
Paper F — joint (M, epsilon) accretion-bound Monte Carlo.

Computes per-band and joint upper limits on the Bondi radiative efficiency
    epsilon = L_bol / (Mdot_Bondi c^2)
for a putative central IMBH in omega Cen, from three non-detections:
  - radio: Mahida et al. 2026 (ATCA, 1.1 uJy rms at 7.25 GHz), via the
    fundamental plane of black-hole activity (Merloni et al. 2003) with its
    intrinsic scatter carried as a nuisance;
  - infrared: Chen et al. 2025 (JWST NIRCam/MIRI point-source limits);
  - X-ray: Haggard et al. 2013 (Chandra 291 ks, L_X <= 1.6e30 erg/s).

Shared nuisance parameters (gas density, sound speed, distance, SED
fractions, fundamental-plane scatter, ADIOS index) are sampled ONCE per MC
draw and propagated to all bands, so the joint bound honestly inherits
their correlations.  Outputs percentile curves for the paper's pgfplots
figures and a table at the three contested mass anchors.

Conventions follow Paper E Sec. "fuel budget": sigma = 21 km/s (paper
fiducial), n_e median 0.23 cm^-3 by 47 Tuc analogy (Freire 2001; Abbate
2018), Bondi normalization reproducing E's 3e18 g/s at 2e4 Msun.
"""

import json
import numpy as np

rng = np.random.default_rng(42)

# ----- constants (cgs) -----
G = 6.674e-8
c = 2.998e10
m_p = 1.673e-24
Msun = 1.989e33
kpc = 3.086e21
Lsun = 3.828e33

# ----- fixed fiducials -----
SIGMA = 21e5          # cm/s, paper-set fiducial (NOT the tools' 18.2)
MU_E = 1.5            # g per electron / m_p; matches Paper E normalization
N_MC = 40000

# ----- observational inputs -----
# Radio: ATCA 7.25 GHz, rms 1.1 uJy -> 3 sigma point-source limit 3.3 uJy
S_RADIO_3SIG = 3.3e-29          # erg/s/cm^2/Hz
NU_RADIO = 7.25e9               # Hz
# X-ray: Chandra 0.5-7 keV upper limit (Haggard et al. 2013)
LX_LIM = 1.6e30                 # erg/s
# IR: JWST NIRCam/MIRI point-source luminosity limit at the center
# (Chen et al. 2025: no accretion-like SED; nuLnu limits a few x 1e31)
LIR_LIM = 3.0e31                # erg/s  (band-peak nuLnu proxy)

# Fundamental plane (Merloni, Heinz & Di Matteo 2003):
# log L_R(5GHz) = 0.60 log L_X(2-10keV) + 0.78 log M + 7.33, scatter 0.88 dex
FP_A, FP_B, FP_C, FP_SIG = 0.60, 0.78, 7.33, 0.88


def sample_nuisances(n, wide_gas=False):
    """One draw of every shared nuisance, used by all bands."""
    width = 1.5 if wide_gas else 0.5        # dex; 'wide' = x10 range check
    n_e = 0.23 * 10 ** rng.normal(0.0, width, n)          # cm^-3
    c_s = rng.uniform(10e5, 15e5, n)                      # cm/s, 1e4 K gas
    d = rng.normal(5.43, 0.05, n) * kpc                   # cm
    # SED fractions for a quiescent hot flow (bracket over ADAF/jet families)
    f_X = 10 ** rng.uniform(np.log10(0.03), np.log10(0.3), n)
    f_IR = 10 ** rng.uniform(np.log10(0.03), np.log10(0.3), n)
    fp_scatter = rng.normal(0.0, FP_SIG, n)               # dex
    s_adios = rng.uniform(0.2, 0.5, n)                    # inflow index
    return n_e, c_s, d, f_X, f_IR, fp_scatter, s_adios


def mdot_bondi(M, n_e, c_s):
    rho = MU_E * m_p * n_e
    return 4 * np.pi * (G * M) ** 2 * rho / (SIGMA ** 2 + c_s ** 2) ** 1.5


def eps_limits(M, nu):
    """Per-band epsilon upper limits for one mass, vectorized over MC draws."""
    n_e, c_s, d, f_X, f_IR, fp_sc, s_adios = nu
    mdot = mdot_bondi(M, n_e, c_s)          # g/s
    mdot_c2 = mdot * c ** 2                 # erg/s

    # X-ray leg: L_bol <= LX_LIM / f_X
    eps_x = (LX_LIM / f_X) / mdot_c2

    # IR leg: L_bol <= LIR_LIM / f_IR
    eps_ir = (LIR_LIM / f_IR) / mdot_c2

    # Radio leg: invert the fundamental plane with scatter.
    # L_R(5GHz) ~ nu L_nu; take the flat-spectrum conversion from 7.25 GHz.
    L_R = 4 * np.pi * d ** 2 * S_RADIO_3SIG * 5.0e9      # erg/s at 5 GHz
    logLx_fp = (np.log10(L_R) - FP_B * np.log10(M / Msun)
                - FP_C - fp_sc) / FP_A
    eps_r = (10 ** logLx_fp / f_X) / mdot_c2

    eps_joint = np.minimum(np.minimum(eps_x, eps_ir), eps_r)
    eps_xir = np.minimum(eps_x, eps_ir)      # fundamental-plane-independent
    # ADIOS translation: horizon-side efficiency eta = eps / f_B,
    # f_B = (r_B / r_g)^(-s)
    r_B = G * M / (SIGMA ** 2 + c_s ** 2)
    r_g = G * M / c ** 2
    f_B = (r_B / r_g) ** (-s_adios)
    eta_joint = eps_joint / f_B
    return eps_x, eps_ir, eps_r, eps_joint, eps_xir, eta_joint


def pct(a):
    return [float(np.percentile(a, p)) for p in (5, 50, 95)]


def run(wide_gas=False):
    nu = sample_nuisances(N_MC, wide_gas)
    Ms = np.logspace(3, 5, 41)
    out = {"M": Ms.tolist(), "x": [], "ir": [], "r": [], "joint": [],
           "xir": [], "eta": []}
    for M in Ms * Msun:
        ex, ei, er, ej, exir, eta = eps_limits(M, nu)
        out["x"].append(pct(ex))
        out["ir"].append(pct(ei))
        out["r"].append(pct(er))
        out["joint"].append(pct(ej))
        out["xir"].append(pct(exir))
        out["eta"].append(pct(eta))
    return out


def anchors(res):
    rows = []
    for M0 in (6.0e3, 8.2e3, 4.0e4):
        i = int(np.argmin(np.abs(np.array(res["M"]) - M0)))
        rows.append({"M": res["M"][i],
                     "eps_joint": res["joint"][i], "eps_xir": res["xir"][i],
                     "eps_x": res["x"][i], "eps_ir": res["ir"][i],
                     "eps_r": res["r"][i], "eta": res["eta"][i]})
    return rows


base = run(wide_gas=False)
wide = run(wide_gas=True)

result = {
    "base": base,
    "wide_gas": {"joint": wide["joint"], "M": wide["M"]},
    "anchors_base": anchors(base),
    "anchors_wide": anchors(wide),
    "config": {"N_MC": N_MC, "sigma_kms": 21, "n_e_median": 0.23,
               "n_e_width_dex": 0.5, "wide_width_dex": 1.5,
               "fp_scatter_dex": FP_SIG, "s_adios": [0.2, 0.5],
               "f_band_range": [0.03, 0.3], "seed": 42},
}

with open("fF_results.json", "w") as f:
    json.dump(result, f, indent=1)

# console summary
for tag, rows in (("base", result["anchors_base"]),
                  ("wide", result["anchors_wide"])):
    print(f"--- {tag} ---")
    for r in rows:
        j = r["eps_joint"]
        print(f"M={r['M']:.3g}: eps_joint 5/50/95 = "
              f"{j[0]:.2e} / {j[1]:.2e} / {j[2]:.2e}")
        if tag == "base":
            print(f"   per-band medians: X {r['eps_x'][1]:.2e}  "
                  f"IR {r['eps_ir'][1]:.2e}  R {r['eps_r'][1]:.2e}  "
                  f"eta_median {r['eta'][1]:.2e}")
