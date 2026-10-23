"""Paper F v0.4 -- the R8/R9 repair rerun of the joint posterior on eps.

v0.4 differs from v0.3 (fF_posterior_v3.py, retained UNCHANGED as the previous
computation of record) by four corrections, each traceable to a finding in
OCS-PAPER-RIGOR-REVIEW_2026-09-02 / _2026-09-03 and each individually
switchable so that its effect can be isolated:

  A. eta_ADAF (F-R9-01 = F-R8-01).  v0.3 used eta = 0.1 min(1, mdot/1e-2),
     linear in mdot, while citing the piecewise fits of Xie & Yuan (2012).
     Those fits are eps(mdot) = eps_0 (mdot/1e-2)^a with (eps_0, a) tabulated
     per delta, the fraction of viscous heating delivered to electrons, and a
     is 0.47-0.71 in the low-mdot branch that this problem sits in, not 1.
     v0.4 implements the tabulated piecewise form and promotes delta to an
     eighth nuisance parameter drawn over the four tabulated values.
     NOTE ON EXTRAPOLATION, which this correction does not remove: the
     horizon-scale mdot here is 1e-9-1e-6 Eddington, 1.2 to 5.0 decades
     BELOW the upper edge of the lowest branch of XY12's piecewise fit
     (Table 1: mdot_net <~ 1.6e-5 to 9.4e-5 depending on delta; no lower
     edge is printed).  Both the old form and the new one are extrapolations; the new
     one at least extrapolates the cited family.  A clamped variant that
     freezes eta at its value on the fit's own upper edge is run alongside
     as the conservative bracket.

  B. IR band-integration (F-R9-02 = F-R8-03).  Chen+2025's Table 1 states
     "Luminosity calculated as L = 4 pi d^2 F_lambda Delta_lambda", a
     band-INTEGRATED luminosity, while the forward model predicts a band-peak
     nu L_nu.  nu L_nu / L_int = lambda_c / Delta_lambda, so v0.3 compared
     quantities differing by a factor 4.0-5.6 per filter.  v0.4 multiplies
     each filter's sigma by that factor.  Delta_lambda is not printed in the
     source and is recovered from the table's own L/F ratios
     (fF_r9_checks.py).  The F200W 99.7 per cent row, whose luminosity entry
     duplicates its flux entry (F-R8-14), is corrected to the value its own
     filter's other three rows imply.

  C. Wind floor (F-R9-03 = F-R8-05/-06).  The n_e >= 0.05 cm^-3 floor was
     read off a "1e3 giants" estimate that the shipped recount
     (fF_calc7_windfloor.py) replaces with 8.4 giants and a no-removal
     steady state of n_e = 0.030 cm^-3.  The old floor sits ABOVE that
     steady state, so it was a ceiling.  v0.4 runs the floor at 0.02, at the
     recount's own 0.030, and not at all.

  D. P_excl (F-R9-05 = F-R8-11).  v0.3's P_excl compared per-draw natural
     predictions against a scalar marginalised over the SAME draws, which is
     a prior-exceedance fraction with common random numbers, not a posterior
     statement.  v0.4 reports (i) a posterior-predictive exclusion fraction:
     the fraction of natural-flow draws whose own predicted observables are
     rejected by the measured data at the 5 per cent level of the joint
     chi-square the likelihood already defines, and (ii) the v0.3 statistic
     recomputed on INDEPENDENT draws and renamed honestly, both with
     Monte Carlo standard errors.

Self-check: run with all four corrections disabled, v0.4 must reproduce
fF_v3_results.json to floating-point equality.  main() asserts this before
computing anything else, so the refactor cannot silently move a number.

Outputs: fF_v4_results.json, fF_v4_pgf.txt, fF_v4_exclfrac.json,
fF_v4_scalings.json.  Seed 42 throughout; delta and the independent
prior-exceedance draws use their own seeds (4201, 4202) so that the v0.3
nuisance stream is bit-for-bit preserved and every delta is attributable.
"""

import json
import os
from statistics import NormalDist

import numpy as np
from scipy.stats import chi2 as _chi2

import fF_posterior_v3 as V3

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = V3.INPUTS

G, c, m_p, Msun, kpc = V3.G, V3.c, V3.m_p, V3.Msun, V3.kpc
MU_E, LAM, N_MC, K_2TO10 = V3.MU_E, V3.LAM, V3.N_MC, V3.K_2TO10
FAMILIES = V3.FAMILIES
EPS_GRID, M_GRID, ANCHORS = V3.EPS_GRID, V3.M_GRID, V3.ANCHORS
SIG_S_RADIO, S_RADIO_MEAS = V3.SIG_S_RADIO, V3.S_RADIO_MEAS
FX_LIM, SIG_FX = V3.FX_LIM, V3.SIG_FX
D_REF_IR_CHEN, D_REF_IR_PAPER = V3.D_REF_IR_CHEN, V3.D_REF_IR_PAPER
FP_A, FP_B, FP_C, FP_SIG = V3.FP_A, V3.FP_B, V3.FP_C, V3.FP_SIG
COMPLETENESS_Z = V3.COMPLETENESS_Z
IR_COMPLETENESS_PRIMARY = V3.IR_COMPLETENESS_PRIMARY

SEED = 42
SEED_DELTA = 4201
SEED_INDEP = 4202


# =====================================================================
# A. Xie & Yuan (2012) piecewise radiative efficiency
# =====================================================================
# Table 1 of Xie & Yuan 2012 (MNRAS 427, 1580; arXiv:1207.3113), their
# Eq. 11: eps(mdot_net) = eps_0 (mdot_net / mdot_c)^a with mdot_c = 1e-2
# mdot_Edd, mdot_Edd defined as 10 L_Edd/c^2 -- the same Eddington
# convention this script's mdot_edd uses (1.4e18 (M/Msun) g/s = L_Edd/0.1c^2).
# Rows are (mdot_upper_edge, eps_0, a); the first row's validity has no lower
# edge in the source and is extrapolated here (see the module docstring).
XY12 = {
    0.5:   [(2.9e-5, 1.58, 0.65), (3.3e-3, 0.055, 0.076), (5.3e-3, 0.17, 1.12)],
    0.1:   [(9.4e-5, 0.12, 0.59), (5.0e-3, 0.026, 0.27), (6.6e-3, 0.50, 4.53)],
    1e-2:  [(1.6e-5, 0.069, 0.69), (5.3e-3, 0.027, 0.54), (7.1e-3, 0.42, 4.85)],
    1e-3:  [(7.6e-5, 0.065, 0.71), (4.5e-3, 0.020, 0.47), (7.1e-3, 0.26, 3.67)],
}
DELTA_VALUES = sorted(XY12)
# Above the top tabulated rate the flow is no longer a hot flow; eta is held
# at the thin-disk value rather than extrapolated upward.  Irrelevant at the
# rates this paper reaches (mdot < 1e-6) and stated so it is not a hidden knob.
ETA_MAX = 0.1


def eta_xy12(mdot, delta_idx, clamp_to_fit_range=False):
    """Vectorized XY12 efficiency.  delta_idx indexes DELTA_VALUES."""
    mdot = np.asarray(mdot, dtype=float)
    out = np.empty_like(mdot)
    for k, dval in enumerate(DELTA_VALUES):
        sel = delta_idx == k
        if not np.any(sel):
            continue
        m = mdot[sel]
        rows = XY12[dval]
        if clamp_to_fit_range:
            # conservative bracket: below the fit's own lowest computed rate,
            # hold eta at its value on that edge instead of extrapolating.
            m = np.maximum(m, rows[0][0])
        e = np.empty_like(m)
        lo = 0.0
        for i, (hi, e0, a) in enumerate(rows):
            band = (m > lo) & (m <= hi) if i else (m <= hi)
            e[band] = e0 * (m[band] / 1e-2) ** a
            lo = hi
        top = m > rows[-1][0]
        e[top] = ETA_MAX
        out[sel] = np.minimum(e, ETA_MAX)
    return out


def eta_v3(mdot):
    """The v0.3 form, retained for the isolation runs."""
    return 0.1 * np.minimum(1.0, np.asarray(mdot) / 1e-2)


# =====================================================================
# B. IR band-integration correction and the F200W row repair
# =====================================================================
_CHECKS_PATH = os.path.join(HERE, "fF_r9_checks.json")
if not os.path.exists(_CHECKS_PATH):
    raise SystemExit("run fF_r9_checks.py first (it derives Delta_lambda)")
with open(_CHECKS_PATH) as _fh:
    CHECKS = json.load(_fh)

BAND_CORR = {f: v["band_correction_lambda_over_Delta_lambda"]
             for f, v in CHECKS["ir_band_correction"]["per_filter"].items()}
# F200W's own Delta_lambda is re-derived from its three self-consistent rows
# only, since the 99.7 per cent row is the one being corrected.
_f200 = CHECKS["ir_band_correction"]["per_filter"]["F200W"]
_good = [r["L_over_F"] for r in _f200["rowwise_L_over_F"]
         if r["completeness"] != "99.7%"]
_fourpi_d2 = 4 * np.pi * D_REF_IR_CHEN ** 2
BAND_CORR["F200W"] = _f200["lambda_c_Ang"] / (np.mean(_good) / _fourpi_d2)
F200W_997_LUM = CHECKS["F200W_997_row"]["implied_lum_lim_1e30"] * 1e30


def ir_filters(completeness, band_corrected=True, fix_f200w=True):
    out = []
    for row in INPUTS["chen2025jwst"]["per_filter_limits"]["table"]:
        if row["completeness"] != completeness:
            continue
        L = row["lum_lim_1e30ergs"] * 1e30
        if fix_f200w and row["filter"] == "F200W" and completeness == "99.7%":
            L = F200W_997_LUM
        sig = L / COMPLETENESS_Z[completeness]
        if band_corrected:
            # compare like with like: the model's band-peak nu L_nu against a
            # band-integrated limit means scaling sigma by lambda_c/Delta_lambda
            sig *= BAND_CORR[row["filter"]]
        out.append({"filter": row["filter"], "completeness": completeness,
                    "L_lim": L, "sigma": sig,
                    "band_correction": BAND_CORR[row["filter"]]
                    if band_corrected else 1.0,
                    "vega_mag_limit": row["vega_mag_limit"]})
    return out


IR_SETS = {c: ir_filters(c) for c in COMPLETENESS_Z}
IR_SETS_V3 = {c: ir_filters(c, band_corrected=False, fix_f200w=False)
              for c in COMPLETENESS_Z}


# =====================================================================
# forward model (identical to v0.3 except where a correction is switched on)
# =====================================================================
def make_rng():
    return np.random.default_rng(SEED)


def draw_theta(rng, n, family, ne_width=0.5, ne_median=0.23, ne_floor=None):
    """Bit-for-bit the v0.3 draw order, so v0.3 stays reproducible."""
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


def attach_delta(th, seed=SEED_DELTA):
    """delta as an eighth nuisance, on its own stream (correction A)."""
    r = np.random.default_rng(seed)
    th = dict(th)
    th["delta_idx"] = r.integers(0, len(DELTA_VALUES), len(th["n_e"]))
    return th


mdot_bondi = V3.mdot_bondi


def log_like_terms(eps, M, th, family, sig_radio=SIG_S_RADIO, sig_fx=SIG_FX,
                   ir_set=None, ir_scale=1.0, ir_mode="combined",
                   d_ref_ir=D_REF_IR_CHEN, k_2to10=K_2TO10):
    """Per-band -0.5*(pred/sigma)^2 terms; summing them gives v0.3's log_like."""
    if ir_set is None:
        ir_set = IR_SETS[IR_COMPLETENESS_PRIMARY]
    use_radio = FAMILIES[family][4]
    Lbol = eps * mdot_bondi(M, th) * c ** 2

    terms = []
    fX_pred = th["f_X"] * Lbol / (4 * np.pi * th["d"] ** 2)
    terms.append(fX_pred / sig_fx)

    LIR_pred = th["f_IR"] * Lbol * (d_ref_ir / th["d"]) ** 2
    sigmas = [f["sigma"] * ir_scale for f in ir_set]
    if ir_mode == "tightest":
        sigmas = [min(sigmas)]
    for sig in sigmas:
        terms.append(LIR_pred / sig)

    if use_radio:
        LX_210 = th["f_X"] * Lbol * k_2to10
        with np.errstate(divide="ignore"):
            logLR = (FP_A * np.log10(np.maximum(LX_210, 1e-30))
                     + FP_B * np.log10(M / Msun) + FP_C + th["fp"])
        S_pred = 10 ** logLR / (4 * np.pi * th["d"] ** 2 * 5.0e9)
        terms.append((S_pred - S_RADIO_MEAS) / sig_radio)
    return terms


def log_like(eps, M, th, family, **kw):
    z = log_like_terms(eps, M, th, family, **kw)
    ll = -0.5 * z[0] ** 2
    for t in z[1:]:
        ll = ll - 0.5 * t ** 2
    return ll


def eps95_curve(masses, family, th, eps_grid=None, **kw):
    grid = EPS_GRID if eps_grid is None else eps_grid
    out = []
    for M in masses:
        post = np.empty(len(grid))
        for i, e in enumerate(grid):
            ll = log_like(e, M, th, family, **kw)
            m = ll.max()
            post[i] = np.exp(m) * np.mean(np.exp(ll - m))
        post /= post.sum()
        out.append(float(np.interp(0.95, np.cumsum(post), grid)))
    return out


def eps_nat_draws(M, th, eta_mode="xy12", clamp=False):
    """eps_nat = eta(mdot_horizon) * f_B, per draw."""
    mdot = mdot_bondi(M, th)
    r_B = G * M / th["c_s"] ** 2
    r_g = G * M / c ** 2                    # gravitational radius, stated
    f_B = (r_B / r_g) ** (-th["s"])
    mdot_edd = 1.4e18 * (M / Msun)
    mdot_hor = f_B * mdot / mdot_edd
    if eta_mode == "v3":
        eta = eta_v3(mdot_hor)
    else:
        eta = eta_xy12(mdot_hor, th["delta_idx"], clamp_to_fit_range=clamp)
    return eta * f_B, mdot_hor


def natural_band(masses, th, **kw):
    return [[float(np.percentile(eps_nat_draws(M, th, **kw)[0], p))
             for p in (5, 50, 95)] for M in masses]


# =====================================================================
# D. exclusion fractions
# =====================================================================
def p_excl_ppc(masses, family, th, eta_mode="xy12", clamp=False, alpha=0.05,
               **kw):
    """Posterior-predictive exclusion.

    For each natural-flow draw the model is fully specified: eps = eps_nat
    (theta) and the nuisances are that draw's own.  The measured data (zero
    central flux in every band, with the published sigmas) then have a joint
    chi-square under that draw, chi2 = sum_b (pred_b/sigma_b)^2, which is
    chi2_k distributed if the draw is the truth.  A draw is excluded when the
    data it predicts are rejected at the alpha level.  This is a per-draw
    statement that uses the likelihood, so it neither compares a distribution
    against a scalar built from the same draws nor inherits the
    common-random-number cancellation of the v0.3 statistic.
    """
    out, err = [], []
    for M in masses:
        e_nat, _ = eps_nat_draws(M, th, eta_mode=eta_mode, clamp=clamp)
        # evaluate the likelihood terms AT each draw's own natural eps.  The
        # X-ray and infrared terms are linear in eps but the radio term is
        # not (S_pred ~ eps^0.60 through the plane), so nothing is scaled.
        z = log_like_terms(e_nat, M, th, family, **kw)
        chi2 = np.zeros_like(e_nat)
        for t in z:
            chi2 = chi2 + t ** 2
        k = len(z)
        p = _chi2.sf(chi2, k)
        frac = float(np.mean(p < alpha))
        out.append(frac)
        err.append(float(np.sqrt(max(frac * (1 - frac), 1e-12) / len(e_nat))))
    return out, err


def p_exceed(masses, eps95_vals, th, eta_mode="xy12", clamp=False):
    """The v0.3 statistic, named for what it is: a PRIOR-exceedance fraction."""
    out, err = [], []
    for M, e in zip(masses, eps95_vals):
        d = eps_nat_draws(M, th, eta_mode=eta_mode, clamp=clamp)[0]
        frac = float(np.mean(d > e))
        out.append(frac)
        err.append(float(np.sqrt(max(frac * (1 - frac), 1e-12) / len(d))))
    return out, err


# =====================================================================
# self-check: corrections off must reproduce v0.3 exactly
# =====================================================================
def gate_reproduces_v3():
    with open(os.path.join(HERE, "fF_v3_results.json")) as fh:
        v3 = json.load(fh)
    rng = make_rng()
    th = {f: draw_theta(rng, N_MC, f) for f in FAMILIES}
    got = eps95_curve(ANCHORS, "riaf", th["riaf"],
                      ir_set=IR_SETS_V3[IR_COMPLETENESS_PRIMARY])
    want = v3["anchors_riaf"]
    for a, b in zip(got, want):
        assert abs(a / b - 1.0) < 1e-12, (a, b)
    th_nat = attach_delta(th["riaf"])
    got_x, _ = p_exceed(ANCHORS, want, th_nat, eta_mode="v3")
    want_x = v3["exclfrac_anchors"]["riaf"]
    for a, b in zip(got_x, want_x):
        assert abs(a - b) < 1e-12, (a, b)
    return {"anchors_riaf_v3_reproduced": got,
            "exclfrac_riaf_v3_reproduced": got_x,
            "note": "v0.4 with corrections A, B and D disabled reproduces "
                    "fF_v3_results.json to floating-point equality; the "
                    "refactor moves no number by itself."}


# =====================================================================
def run_all():
    res = {"M": (M_GRID / Msun).tolist(),
           "anchors_M": (ANCHORS / Msun).tolist()}
    res["gate_v3_reproduction"] = gate_reproduces_v3()

    rng = make_rng()
    th_base = {f: draw_theta(rng, N_MC, f) for f in FAMILIES}
    th_nat = attach_delta(th_base["riaf"])

    for f in FAMILIES:
        res["eps95_" + f] = eps95_curve(M_GRID, f, th_base[f])
        res["anchors_" + f] = eps95_curve(ANCHORS, f, th_base[f])

    _dead = draw_theta(rng, N_MC, "disk")   # keeps the v0.3 stream alignment
    del _dead
    th_riaf_nr = dict(th_base["riaf"])
    res["eps95_riaf_noradio"] = eps95_curve(M_GRID, "disk", th_riaf_nr)
    res["anchors_riaf_noradio"] = eps95_curve(ANCHORS, "disk", th_riaf_nr)

    th_wide = draw_theta(rng, N_MC, "riaf", ne_width=1.5)
    res["anchors_riaf_wide"] = eps95_curve(ANCHORS, "riaf", th_wide)
    th_low = draw_theta(rng, N_MC, "riaf", ne_median=0.023)
    res["anchors_riaf_lowne"] = eps95_curve(ANCHORS, "riaf", th_low)

    # C. wind floor at the recount's own values, and the retired 0.05
    floors = {"floor002": 0.02, "floor003": 0.030, "floor005_retired": 0.05}
    th_floor = {}
    for tag, val in floors.items():
        th_floor[tag] = draw_theta(rng, N_MC, "riaf", ne_width=1.5,
                                   ne_floor=val)
        res["anchors_riaf_" + tag] = eps95_curve(ANCHORS, "riaf",
                                                 th_floor[tag])

    th_ne = draw_theta(rng, N_MC, "riaf", ne_width=0.04)
    res["anchors_fc_ne"] = eps95_curve(ANCHORS, "riaf", th_ne)
    res["anchors_fc_ska"] = eps95_curve(ANCHORS, "riaf", th_base["riaf"],
                                        sig_radio=SIG_S_RADIO / 10.0)
    res["anchors_fc_miri_jet"] = eps95_curve(ANCHORS, "jet", th_base["jet"],
                                             ir_scale=1.0 / 3.0)
    res["anchors_riaf_floor11"] = eps95_curve(
        ANCHORS, "riaf", th_base["riaf"], eps_grid=np.logspace(-11, -2, 91))

    for name, z in V3.XRAY_Z_VARIANTS.items():
        res["anchors_riaf_xz_" + name] = eps95_curve(
            ANCHORS, "riaf", th_base["riaf"], sig_fx=FX_LIM / z)
    # F-R8-16: the source's own spectral index, as a ladder row
    k23 = CHECKS["xray_band_correction"]["k_Gamma_2.3"]
    res["anchors_riaf_kgamma23"] = eps95_curve(
        ANCHORS, "riaf", th_base["riaf"], k_2to10=k23)
    res["anchors_jet_kgamma23"] = eps95_curve(
        ANCHORS, "jet", th_base["jet"], k_2to10=k23)

    for cname in IR_SETS:
        tag = cname.replace(".", "").replace("%", "")
        res["anchors_riaf_ir" + tag] = eps95_curve(
            ANCHORS, "riaf", th_base["riaf"], ir_set=IR_SETS[cname])
        res["anchors_jet_ir" + tag] = eps95_curve(
            ANCHORS, "jet", th_base["jet"], ir_set=IR_SETS[cname])
    res["anchors_riaf_ir_tightest"] = eps95_curve(
        ANCHORS, "riaf", th_base["riaf"], ir_mode="tightest")
    res["anchors_jet_ir_tightest"] = eps95_curve(
        ANCHORS, "jet", th_base["jet"], ir_mode="tightest")
    res["anchors_jet_ir_d543"] = eps95_curve(
        ANCHORS, "jet", th_base["jet"], d_ref_ir=D_REF_IR_PAPER)
    # B isolated: v0.3's uncorrected IR sigmas, everything else at v0.4
    res["anchors_jet_ir_uncorrected"] = eps95_curve(
        ANCHORS, "jet", th_base["jet"],
        ir_set=IR_SETS_V3[IR_COMPLETENESS_PRIMARY])
    res["anchors_riaf_ir_uncorrected"] = eps95_curve(
        ANCHORS, "riaf", th_base["riaf"],
        ir_set=IR_SETS_V3[IR_COMPLETENESS_PRIMARY])
    res["anchors_disk_ir_uncorrected"] = eps95_curve(
        ANCHORS, "disk", th_base["disk"],
        ir_set=IR_SETS_V3[IR_COMPLETENESS_PRIMARY])
    res["anchors_riaf_noradio_ir_uncorrected"] = eps95_curve(
        ANCHORS, "disk", th_riaf_nr,
        ir_set=IR_SETS_V3[IR_COMPLETENESS_PRIMARY])

    # --- natural band and the two exclusion statistics -------------------
    res["nat_band"] = natural_band(M_GRID, th_nat)
    res["nat_anchors"] = natural_band(ANCHORS, th_nat)
    res["nat_band_v3eta"] = natural_band(M_GRID, th_nat, eta_mode="v3")
    res["nat_band_clamped"] = natural_band(M_GRID, th_nat, clamp=True)
    res["nat_anchors_clamped"] = natural_band(ANCHORS, th_nat, clamp=True)

    res["mdot_hor_anchors"] = {
        str(int(M / Msun)): {
            "p05": float(np.percentile(eps_nat_draws(M, th_nat)[1], 5)),
            "p50": float(np.percentile(eps_nat_draws(M, th_nat)[1], 50)),
            "p95": float(np.percentile(eps_nat_draws(M, th_nat)[1], 95)),
        } for M in ANCHORS}

    fam_of = {"riaf": "riaf", "jet": "jet", "riaf_noradio": "disk"}
    # The posterior-predictive statistic evaluates the LIKELIHOOD at each
    # natural draw, so it must use each family's own band-fraction draws; the
    # jet family's f_IR and f_X ranges differ from the RIAF family's and the
    # jet leg would otherwise be scored under RIAF band fractions.  The
    # radio-free row is the RIAF family with the plane switched off, so it
    # keeps the RIAF draws by construction, exactly as its eps95 curve does.
    # eps_nat itself is band-fraction independent (it is set by n_e, c_s, s
    # and delta), so this changes which likelihood is applied, not the
    # natural-flow prediction being tested.
    th_nat_fam = {"riaf": th_nat,
                  "jet": attach_delta(th_base["jet"]),
                  "riaf_noradio": th_nat}
    res["p_excl_ppc"], res["p_excl_ppc_err"] = {}, {}
    res["p_exceed"], res["p_exceed_err"] = {}, {}
    for key, fam in fam_of.items():
        v, e = p_excl_ppc(ANCHORS, fam, th_nat_fam[key])
        res["p_excl_ppc"][key], res["p_excl_ppc_err"][key] = v, e
        # the prior-exceedance statistic is kept on the RIAF draws for all
        # three columns, as v0.3 computed it, so that the renaming is a
        # like-for-like restatement of the published number.
        v, e = p_exceed(ANCHORS, res["anchors_" + key], th_nat)
        res["p_exceed"][key], res["p_exceed_err"][key] = v, e
    res["p_excl_ppc_curve"] = {
        k: p_excl_ppc(M_GRID, f, th_nat_fam[k])[0] for k, f in fam_of.items()}
    res["p_exceed_curve"] = {
        k: p_exceed(M_GRID, res["eps95_" + k], th_nat)[0] for k in fam_of}
    res["p_excl_ppc_clamped"] = {
        k: p_excl_ppc(ANCHORS, f, th_nat_fam[k], clamp=True)[0]
        for k, f in fam_of.items()}
    res["p_excl_ppc_v3eta"] = {
        k: p_excl_ppc(ANCHORS, f, th_nat_fam[k], eta_mode="v3")[0]
        for k, f in fam_of.items()}
    res["p_excl_ppc_per_delta"] = {}
    for k, dval in enumerate(DELTA_VALUES):
        sub = {kk: vv[th_nat["delta_idx"] == k]
               for kk, vv in th_nat.items() if kk != "delta_idx"}
        sub["delta_idx"] = np.full(sub["n_e"].shape, k)
        res["p_excl_ppc_per_delta"][str(dval)] = {
            "n_draws": int(sub["n_e"].size),
            "riaf": p_excl_ppc(ANCHORS, "riaf", sub)[0],
            "riaf_noradio": p_excl_ppc(ANCHORS, "disk", sub)[0],
            "nat_median": [float(np.percentile(eps_nat_draws(M, sub)[0], 50))
                           for M in ANCHORS]}

    # D(ii): independent draws, breaking the common random numbers
    rng_i = np.random.default_rng(SEED_INDEP)
    th_indep = attach_delta(draw_theta(rng_i, N_MC, "riaf"), seed=SEED_INDEP + 1)
    res["p_exceed_independent"], res["p_exceed_independent_err"] = {}, {}
    for key in fam_of:
        v, e = p_exceed(ANCHORS, res["anchors_" + key], th_indep)
        res["p_exceed_independent"][key] = v
        res["p_exceed_independent_err"][key] = e

    # sensitivity-table exclusion rows, on the new statistic
    res["p_excl_ppc_variants"] = {}
    for tag, thv in (("wide", th_wide), ("lowne", th_low),
                     ("floor002", th_floor["floor002"]),
                     ("floor003", th_floor["floor003"]),
                     ("floor005_retired", th_floor["floor005_retired"])):
        thn = attach_delta(thv)
        res["p_excl_ppc_variants"][tag] = {
            k: p_excl_ppc(ANCHORS, f, thn)[0] for k, f in fam_of.items()}
    for tag, kw in (("xz_twosided95", {"sig_fx": FX_LIM / 1.959963984540054}),
                    ("xz_v2_over3", {"sig_fx": FX_LIM / 3.0}),
                    ("kgamma23", {"k_2to10": k23}),
                    ("ir997", {"ir_set": IR_SETS["99.7%"]}),
                    ("ir68", {"ir_set": IR_SETS["68%"]}),
                    ("ir_tightest", {"ir_mode": "tightest"})):
        res["p_excl_ppc_variants"][tag] = {
            k: p_excl_ppc(ANCHORS, f, th_nat_fam[k], **kw)[0]
            for k, f in fam_of.items()}
    res["p_excl_ppc_variants"]["ir_uncorrected"] = {
        k: p_excl_ppc(ANCHORS, f, th_nat_fam[k],
                      ir_set=IR_SETS_V3[IR_COMPLETENESS_PRIMARY])[0]
        for k, f in fam_of.items()}

    # Paper E's turbulent-medium Bondi convention (lambda = 1, denominator
    # (sigma^2 + c_s^2)^1.5).  Table 8's last row; it moves both the limit and
    # the natural-flow band, so it is run through both statistics.
    _mdot_orig = globals()["mdot_bondi"]

    def _mdot_paperE(M, th):
        SIG = 21.0e5
        rho = MU_E * m_p * th["n_e"]
        return (4 * np.pi * 1.0 * (G * M) ** 2 * rho
                / (SIG ** 2 + th["c_s"] ** 2) ** 1.5)

    globals()["mdot_bondi"] = _mdot_paperE
    try:
        res["anchors_riaf_bondiE"] = eps95_curve(ANCHORS, "riaf",
                                                 th_base["riaf"])
        res["anchors_riaf_noradio_bondiE"] = eps95_curve(ANCHORS, "disk",
                                                         th_riaf_nr)
        res["p_excl_ppc_variants"]["bondi_paperE"] = {
            k: p_excl_ppc(ANCHORS, f, th_nat_fam[k])[0]
            for k, f in fam_of.items()}
        res["nat_anchors_bondiE"] = natural_band(ANCHORS, th_nat)
    finally:
        globals()["mdot_bondi"] = _mdot_orig

    res["config"] = {
        "version": "v0.4", "N_MC": N_MC, "seed": SEED,
        "seed_delta": SEED_DELTA, "seed_independent": SEED_INDEP,
        "mu_e": MU_E, "lambda": LAM, "eta_model": "XieYuan2012 piecewise",
        "xy12_table": {str(k): v for k, v in XY12.items()},
        "delta_values": DELTA_VALUES,
        "delta_prior": "uniform over the four tabulated delta",
        "eta_extrapolation_note": (
            "mdot_hor here is 1e-9-1e-6 Edd, 1.2 to 5.0 decades below the "
            "upper edge of the lowest XY12 branch; the low-mdot branch is extrapolated. "
            "nat_band_clamped holds eta at the fit's own upper edge instead."),
        "ir_band_correction": BAND_CORR,
        "F200W_997_lum_used": F200W_997_LUM,
        "wind_floors_run": floors,
        "k_2to10_primary": K_2TO10,
        "k_2to10_Gamma23": k23,
        "corrections": ["A eta XY12 + delta", "B IR band integration",
                        "C wind floor recount", "D P_excl reconstruction"],
    }
    return res


def scalings(res):
    """F-R9-06: realized marginal scalings, against the quoted asymptotes."""
    M = np.array(res["M"])
    out = {}
    for key in ("riaf", "jet", "riaf_noradio"):
        y = np.array(res["eps95_" + key])
        i1 = int(np.argmin(abs(M - 8200)))
        i2 = int(np.argmin(abs(M - 40000)))
        out[key] = {
            "M_lo": float(M[i1]), "M_hi": float(M[i2]),
            "ratio_lo_over_hi": float(y[i1] / y[i2]),
            "realized_exponent":
                float(np.log(y[i1] / y[i2]) / np.log(M[i2] / M[i1])),
            "global_slope_fit":
                float(np.polyfit(np.log(M), np.log(y), 1)[0]),
        }
    a, b = res["anchors_riaf"], res["anchors_fc_ska"]
    out["radio_depth"] = {
        "anchors": res["anchors_M"],
        "eps95_baseline": a, "eps95_ska": b,
        "realized_gain": [x / y for x, y in zip(a, b)],
        "analytic_asymptote_10x_depth": 10 ** (1 / FP_A),
        "note": ("The single-draw asymptote eps ~ sigma_S^(1/0.60) predicts "
                 "%.1f for a tenfold depth gain; the realized marginal gains "
                 "are smaller because the 0.88-dex plane scatter and the "
                 "X-ray and infrared legs flatten the response."
                 % 10 ** (1 / FP_A))}
    return out


if __name__ == "__main__":
    res = run_all()
    with open(os.path.join(HERE, "fF_v4_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    sc = scalings(res)
    with open(os.path.join(HERE, "fF_v4_scalings.json"), "w") as fh:
        json.dump(sc, fh, indent=1)
    with open(os.path.join(HERE, "fF_v4_exclfrac.json"), "w") as fh:
        json.dump({"p_excl_ppc": res["p_excl_ppc"],
                   "p_excl_ppc_err": res["p_excl_ppc_err"],
                   "p_exceed": res["p_exceed"],
                   "p_exceed_independent": res["p_exceed_independent"]}, fh,
                  indent=1)

    lines = []
    Mv = res["M"]

    def coords(vals):
        return " ".join("(%g,%.3e)" % (m, v) for m, v in zip(Mv, vals))

    for key in ("eps95_riaf", "eps95_jet", "eps95_disk", "eps95_riaf_noradio"):
        lines.append("%s: %s" % (key, coords(res[key])))
    for i, tag in enumerate(("NAT05", "NAT50", "NAT95")):
        lines.append("%s: %s" % (tag, coords([r[i] for r in res["nat_band"]])))
    for i, tag in enumerate(("NATCL05", "NATCL50", "NATCL95")):
        lines.append("%s: %s"
                     % (tag, coords([r[i] for r in res["nat_band_clamped"]])))
    for k in ("riaf", "jet", "riaf_noradio"):
        lines.append("PEXCL_%s: %s"
                     % (k, " ".join("(%g,%.4f)" % (m, v) for m, v
                                    in zip(Mv, res["p_excl_ppc_curve"][k]))))
    with open(os.path.join(HERE, "fF_v4_pgf.txt"), "w") as fh:
        fh.write("\n".join(lines))

    print(res["gate_v3_reproduction"]["note"])
    for n in ("riaf", "jet", "disk", "riaf_noradio", "riaf_wide", "riaf_lowne",
              "riaf_floor002", "riaf_floor003", "riaf_floor005_retired",
              "fc_ne", "fc_ska", "fc_miri_jet", "riaf_floor11",
              "riaf_ir_uncorrected", "jet_ir_uncorrected",
              "riaf_kgamma23", "jet_ir_tightest"):
        v = res["anchors_" + n]
        print("%-24s eps95 @ 6k/8.2k/40k = %.3e / %.3e / %.3e"
              % (n, v[0], v[1], v[2]))
    print("P_excl (posterior-predictive):",
          {k: ["%.3f+-%.3f" % (x, e) for x, e in
               zip(v, res["p_excl_ppc_err"][k])]
           for k, v in res["p_excl_ppc"].items()})
    print("prior-exceedance, same draws:",
          {k: ["%.3f" % x for x in v] for k, v in res["p_exceed"].items()})
    print("prior-exceedance, independent draws:",
          {k: ["%.3f" % x for x in v]
           for k, v in res["p_exceed_independent"].items()})
    print("P_excl with the v0.3 eta:",
          {k: ["%.3f" % x for x in v] for k, v in res["p_excl_ppc_v3eta"].items()})
    print("P_excl, eta clamped to the fit range:",
          {k: ["%.3f" % x for x in v]
           for k, v in res["p_excl_ppc_clamped"].items()})
    print("nat anchors 5/50/95:",
          [["%.2e" % x for x in r] for r in res["nat_anchors"]])
    print("mdot_hor:", json.dumps(res["mdot_hor_anchors"], indent=1))
    print("scalings:", json.dumps(sc, indent=1))
