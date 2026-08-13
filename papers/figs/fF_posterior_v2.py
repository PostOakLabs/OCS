"""
Paper F v0.2 — likelihood-based joint posterior on the Bondi radiative
efficiency eps for a central IMBH in omega Cen.  Supersedes the
min-over-draws construction of fF_joint_bound.py (retained as an appendix
cross-check; that script is unchanged).

Referee-driven design (memos of 2026-08-13, VM Part C + Okafor A/B):
  - Forward model per (eps, M, theta): predicted radio / IR / X-ray
    observables; Gaussian/threshold likelihoods on the MEASURED values
    (radio central pixel 0 +/- 1.1 uJy; Chandra flux 0 +/- limit/3;
    JWST erf-threshold), not 3-sigma cliff inversions.
  - FP scatter is a LATENT variable used in the forward direction only
    (dissolves the inverse-regression objection, VM F5).
  - Bondi rate: c_s-only denominator with lambda(gamma=5/3)=0.25
    (comparison-literature convention; Okafor F1) and mu_e=1.17
    (Okafor F3 / VM F8).  The Paper E turbulent-denominator variant is
    computed alongside for the appendix.
  - r_B = GM/c_s^2 (Paper E convention; Okafor F5); s in [0.3, 0.5].
  - c_s bracket 11.7-16.6 km/s (mu=0.6 isothermal .. pure-H adiabatic;
    Okafor F2).
  - Three SED families with distinct (f_X, f_IR) priors (VM F3 / exp.1):
    RIAF, jet-dominated (IR-bright: JWST binds), thin-disk.
  - Natural-flow expectation band eps_nat = eta_ADAF(mdot) * f_B
    (Okafor F6 / B3).
  - Distance rescales ALL bands (VM F7); band conversion 0.5-7 keV ->
    2-10 keV for the FP leg at Gamma=2 (VM F10).
  - Anchor rows evaluated at the exact anchor masses (VM F6).
  - Output: eps95(M) credible curves per family (with and without the
    radio leg), eps-prior-floor sensitivity, wide-n_e variant,
    wind-floor-truncated variant, forecasts (n_e known; SKA-era radio
    depth; deeper MIRI), and the natural-expectation band.
"""

import json
import numpy as np

rng = np.random.default_rng(42)

# ----- constants (cgs) -----
G, c, m_p, Msun, kpc = 6.674e-8, 2.998e10, 1.673e-24, 1.989e33, 3.086e21

# ----- fixed choices -----
MU_E = 1.17            # g per electron / m_p, ionized X~0.7 plasma
LAM = 0.25             # Bondi eigenvalue, gamma = 5/3
N_MC = 40000
D_REF_X = 4.8 * kpc    # distance at which Haggard+13 luminosity was quoted
D_REF_IR = 5.43 * kpc  # Chen+25 adopt ~5.43 kpc (oMEGACat); flag if not

# ----- measurements (as likelihood inputs) -----
SIG_S_RADIO = 1.1e-29        # erg/s/cm^2/Hz  (ATCA rms at 7.25 GHz)
S_RADIO_MEAS = 0.0           # central-pixel value taken as 0 +/- rms
FX_LIM_3SIG = 5.0e-16        # erg/cm^2/s, 0.5-7 keV, absorption-corrected
SIG_FX = FX_LIM_3SIG / 3.0
LIR_LIM = 3.0e31             # erg/s band-peak nuLnu proxy (Chen+25)
SIG_LIR = LIR_LIM / 3.0
K_2TO10 = 0.61               # F(2-10)/F(0.5-7) for Gamma = 2 power law

# Fundamental plane (forward direction only)
FP_A, FP_B, FP_C, FP_SIG = 0.60, 0.78, 7.33, 0.88

EPS_GRID = np.logspace(-14, -2, 121)
M_GRID = np.logspace(3, 5, 41) * Msun
ANCHORS = np.array([6.0e3, 8.2e3, 4.0e4]) * Msun

FAMILIES = {
    # (fX_lo, fX_hi, fIR_lo, fIR_hi, use_radio)
    "riaf": (0.03, 0.3, 0.03, 0.3, True),
    "jet":  (0.01, 0.1, 0.1, 0.5, True),
    "disk": (0.05, 0.2, 0.05, 0.3, False),
}


def draw_theta(n, family, ne_width=0.5, ne_median=0.23, ne_floor=None):
    fx_lo, fx_hi, fir_lo, fir_hi, _ = FAMILIES[family]
    n_e = ne_median * 10 ** rng.normal(0.0, ne_width, n)
    if ne_floor is not None:
        n_e = np.maximum(n_e, ne_floor)
    return {
        "n_e": n_e,
        "c_s": rng.uniform(11.7e5, 16.6e5, n),
        "d": rng.normal(5.43, 0.05, n) * kpc,
        "f_X": 10 ** rng.uniform(np.log10(fx_lo), np.log10(fx_hi), n),
        "f_IR": 10 ** rng.uniform(np.log10(fir_lo), np.log10(fir_hi), n),
        "fp": rng.normal(0.0, FP_SIG, n),
        "s": rng.uniform(0.3, 0.5, n),
    }


def mdot_bondi(M, th):
    rho = MU_E * m_p * th["n_e"]
    return 4 * np.pi * LAM * (G * M) ** 2 * rho / th["c_s"] ** 3


def log_like(eps, M, th, family, sig_radio=SIG_S_RADIO, sig_lir=SIG_LIR):
    """Vectorized over draws for one (eps, M)."""
    use_radio = FAMILIES[family][4]
    mdot = mdot_bondi(M, th)
    Lbol = eps * mdot * c ** 2

    # X-ray leg: Gaussian in measured 0.5-7 keV flux
    fX_pred = th["f_X"] * Lbol / (4 * np.pi * th["d"] ** 2)
    ll = -0.5 * (fX_pred / SIG_FX) ** 2

    # IR leg: Gaussian in band-peak luminosity at the source
    # (limit quoted at D_REF_IR; rescale to drawn distance)
    LIR_pred = th["f_IR"] * Lbol
    ll += -0.5 * (LIR_pred * (D_REF_IR / th["d"]) ** 2 / sig_lir) ** 2

    # Radio leg: forward FP with latent scatter -> predicted flux density
    if use_radio:
        LX_210 = th["f_X"] * Lbol * K_2TO10
        with np.errstate(divide="ignore"):
            logLR = (FP_A * np.log10(np.maximum(LX_210, 1e-30))
                     + FP_B * np.log10(M / Msun) + FP_C + th["fp"])
        S_pred = 10 ** logLR / (4 * np.pi * th["d"] ** 2 * 5.0e9)
        ll += -0.5 * ((S_pred - S_RADIO_MEAS) / sig_radio) ** 2
    return ll


def eps95_curve(masses, family, th, **kw):
    """95% credible upper limit on eps (log-uniform prior on the grid)."""
    out = []
    for M in masses:
        post = np.empty(len(EPS_GRID))
        for i, e in enumerate(EPS_GRID):
            ll = log_like(e, M, th, family, **kw)
            m = ll.max()
            post[i] = np.exp(m) * np.mean(np.exp(ll - m))
        post /= post.sum()
        cdf = np.cumsum(post)
        out.append(float(np.interp(0.95, cdf, EPS_GRID)))
    return out


def natural_band(masses, th):
    """eps_nat = eta_ADAF(mdot_horizon) * f_B, percentiles per mass."""
    rows = []
    for M in masses:
        mdot = mdot_bondi(M, th)
        r_B = G * M / th["c_s"] ** 2
        r_g = G * M / c ** 2
        f_B = (r_B / r_g) ** (-th["s"])
        mdot_edd = 1.4e18 * (M / Msun)          # g/s (10% efficiency conv.)
        mdot_hor = f_B * mdot / mdot_edd        # Eddington units
        eta = 0.1 * np.minimum(1.0, mdot_hor / 1e-2)
        eps_nat = eta * f_B
        rows.append([float(np.percentile(eps_nat, p)) for p in (5, 50, 95)])
    return rows


def run_all():
    res = {"M": (M_GRID / Msun).tolist(),
           "anchors_M": (ANCHORS / Msun).tolist()}

    th_base = {f: draw_theta(N_MC, f) for f in FAMILIES}

    # headline curves per family
    for f in FAMILIES:
        res[f"eps95_{f}"] = eps95_curve(M_GRID, f, th_base[f])
        res[f"anchors_{f}"] = eps95_curve(ANCHORS, f, th_base[f])

    # radio-free variant of the riaf family (FP-independent curve)
    th_norad = draw_theta(N_MC, "disk")     # disk = no radio leg, but use riaf f's
    th_riaf_nr = dict(th_base["riaf"])
    res["eps95_riaf_noradio"] = eps95_curve(M_GRID, "disk", th_riaf_nr)
    res["anchors_riaf_noradio"] = eps95_curve(ANCHORS, "disk", th_riaf_nr)

    # prior-median and width sensitivity (riaf)
    th_wide = draw_theta(N_MC, "riaf", ne_width=1.5)
    res["anchors_riaf_wide"] = eps95_curve(ANCHORS, "riaf", th_wide)
    th_low = draw_theta(N_MC, "riaf", ne_median=0.023)
    res["anchors_riaf_lowne"] = eps95_curve(ANCHORS, "riaf", th_low)

    # wind-floor truncation (n_e >= 0.05 cm^-3)
    th_floor = draw_theta(N_MC, "riaf", ne_width=1.5, ne_floor=0.05)
    res["anchors_riaf_floor"] = eps95_curve(ANCHORS, "riaf", th_floor)

    # forecasts (riaf): n_e measured; SKA-era radio; deeper MIRI
    th_ne = draw_theta(N_MC, "riaf", ne_width=0.04)     # +/-10% measured
    res["anchors_fc_ne"] = eps95_curve(ANCHORS, "riaf", th_ne)
    res["anchors_fc_ska"] = eps95_curve(ANCHORS, "riaf", th_base["riaf"],
                                        sig_radio=1.1e-30)
    res["anchors_fc_miri_jet"] = eps95_curve(ANCHORS, "jet", th_base["jet"],
                                             sig_lir=SIG_LIR / 3.0)

    # eps-prior floor sensitivity: refit riaf anchors with grid floored higher
    global EPS_GRID
    saved = EPS_GRID
    EPS_GRID = np.logspace(-11, -2, 91)
    res["anchors_riaf_floor11"] = eps95_curve(ANCHORS, "riaf", th_base["riaf"])
    EPS_GRID = saved

    # natural-expectation band
    res["nat_band"] = natural_band(M_GRID, th_base["riaf"])
    res["nat_anchors"] = natural_band(ANCHORS, th_base["riaf"])

    res["config"] = {"N_MC": N_MC, "mu_e": MU_E, "lambda": LAM,
                     "c_s_kms": [11.7, 16.6], "s": [0.3, 0.5],
                     "ne_median": 0.23, "ne_width_dex": 0.5,
                     "families": {k: v for k, v in FAMILIES.items()},
                     "seed": 42}
    return res


res = run_all()
with open("fF_v2_results.json", "w") as fh:
    json.dump(res, fh, indent=1)

names = ["riaf", "jet", "riaf_noradio", "riaf_wide", "riaf_lowne",
         "riaf_floor", "fc_ne", "fc_ska", "fc_miri_jet", "riaf_floor11"]
for n in names:
    key = f"anchors_{n}" if f"anchors_{n}" in res else n
    if key in res:
        v = res[key]
        print(f"{n:16s} eps95 @ 6k/8.2k/40k = "
              f"{v[0]:.2e} / {v[1]:.2e} / {v[2]:.2e}")
print("disk           ", ["%.2e" % v for v in res["anchors_disk"]])
print("nat band @40k 5/50/95:", ["%.2e" % v for v in res["nat_anchors"][2]])
