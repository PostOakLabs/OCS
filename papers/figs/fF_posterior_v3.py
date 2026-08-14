"""
Paper F v0.3 -- likelihood-based joint posterior on the Bondi radiative
efficiency eps for a central IMBH in omega Cen.

v0.3 differs from v0.2 (fF_posterior_v2.py, retained UNCHANGED for the
appendix cross-check chain) only by ingesting the verified measured inputs
extracted in WU OCS-F-DATA-1 (figs/fF_measured_inputs.json).  The forward
model, priors, families, natural-flow band, seed (42) and draw count are
identical to v0.2.  Six changes, all traceable to that extraction:

  1. D_REF_X: 4.8 -> 5.2 kpc.  Haggard+2013's own adopted distance is
     5.2 kpc (Harris 1996); 4.8 appears nowhere in that paper.  See the
     X-ray leg comments for why this does NOT move the likelihood.
  2. The Chandra flux limit is a 95 per cent confidence upper limit, not
     a "3 sigma" limit.  sigma_FX is derived from that statement instead
     of from lim/3.
  3. The untraceable LIR_LIM = 3e31 erg/s proxy is replaced by a
     per-filter likelihood built from Chen+2025's Table 1.
  4. Mahida+2026's Table 1 observing blocks are exported for the
     duty-cycle section (fF_epochs.json).
  5. Everything is rerun and every headline number is diffed against
     v0.2 in fF_v3_DELTA.md.
  6. Tremou+2018 (MAVERIC) anchor values are exported as
     fF_maveric_context.json for the future context figure.

Nothing else is re-derived.  Items that look wrong but fall outside that
list are flagged in fF_v3_DELTA.md rather than silently changed.

Outputs: fF_v3_results.json, fF_v3_pgf.txt, fF_v3_exclfrac.json,
fF_epochs.json, fF_maveric_context.json.  fF_v3_DELTA.md is written by
fF_v3_delta.py, which consumes this script's JSON and v0.2's.
"""

import json
import os
from statistics import NormalDist

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "fF_measured_inputs.json")) as _fh:
    INPUTS = json.load(_fh)

rng = np.random.default_rng(42)

# ----- constants (cgs) -----
G, c, m_p, Msun, kpc = 6.674e-8, 2.998e10, 1.673e-24, 1.989e33, 3.086e21

# ----- fixed choices (unchanged from v0.2) -----
MU_E = 1.17            # g per electron / m_p, ionized X~0.7 plasma
LAM = 0.25             # Bondi eigenvalue, gamma = 5/3
N_MC = 40000
K_2TO10 = 0.61         # F(2-10)/F(0.5-7) for Gamma = 2 power law

# ----- distances, each source at ITS OWN adopted value -----
# CHANGE 1.  Haggard+2013 state 5.2 kpc (Harris 1996) in their abstract and
# Table 1; v0.2 hardcoded 4.8 kpc with the comment "distance at which
# Haggard+13 luminosity was quoted", which is not that paper's number.
D_REF_X = 5.2 * kpc
# Chen+2025 Table 1 luminosities are computed at 5.49 kpc (their stated
# distance), not at the 5.43 kpc Paper F uses for its own cluster-distance
# prior.  Referencing Chen's limits at Chen's own distance is transcription,
# not harmonization; the 5.43-kpc variant is computed below and differs by
# (5.49/5.43)^2 = 1.022.  The 5.43 +/- 0.05 kpc DRAW prior is left untouched
# (Mahida+2026's measured 5.494 +/- 0.061 kpc is flagged in the DELTA, not
# applied -- outside the six items).
D_REF_IR_PAPER = 5.43 * kpc
D_REF_IR_CHEN = INPUTS["chen2025jwst"]["distance"]["value"] * kpc

# ----- radio (Mahida+2026, unchanged values, now read from the extraction) ----
SIG_S_RADIO = INPUTS["mahida2026"]["rms_noise_combined"]["value"] * 1e-29
S_RADIO_MEAS = 0.0           # central-pixel value taken as 0 +/- rms

# ----- X-ray (Haggard+2013) -----
_hag = INPUTS["haggard2013"]["flux_limit_0.5_7keV"]
FX_LIM = _hag["value"]        # erg/cm^2/s, 0.5-7 keV, absorption-corrected
# CHANGE 2.  Haggard+2013 never call this "3 sigma".  Their stated quantity is
# an aprates 95 per cent confidence upper limit on a non-negative count rate,
# i.e. a ONE-SIDED 95 per cent bound: P(F < F_lim) = 0.95.  For a Gaussian
# centred on the measured value (taken as 0) that gives F_lim = 1.645 sigma.
# The one-sided reading is the one the source's own method supports; the
# two-sided 1.96 convention and v0.2's /3 are carried as sensitivity rows
# (XRAY_Z_VARIANTS) rather than assumed away.  Note the direction: sigma_FX
# grows from lim/3 to lim/1.645, so the X-ray leg gets WEAKER, not tighter.
XRAY_Z = NormalDist().inv_cdf(0.95)          # 1.6449, one-sided 95%
XRAY_Z_VARIANTS = {"onesided95": XRAY_Z,
                   "twosided95": NormalDist().inv_cdf(0.975),   # 1.9600
                   "v2_over3": 3.0}
SIG_FX = FX_LIM / XRAY_Z

# Consistency check of the source's own pair: L_X = 4 pi D^2 F_X at 5.2 kpc.
_LX_implied = 4 * np.pi * D_REF_X ** 2 * FX_LIM
_LX_stated = INPUTS["haggard2013"]["luminosity_limit_0.5_7keV"]["value"]
assert abs(_LX_implied / _LX_stated - 1.0) < 0.02, (_LX_implied, _LX_stated)
# The pair is self-consistent at 5.2 kpc (1.62e30 vs the stated 1.6e30) and
# would NOT be at 4.8 kpc (1.38e30).  This is what fixes the distance.
# The X-ray likelihood itself is evaluated on FLUX, the distance-independent
# observable: predicted flux at the DRAWN distance against the measured flux
# limit.  D_REF_X therefore enters only this conversion check, and change 1
# moves no posterior number.  The tex appendix's anticipated "4.8 vs 5.43 kpc
# mismatch shifts the X-ray leg by 28 per cent" does not materialise; see the
# DELTA.

# ----- infrared (Chen+2025 JWST), CHANGE 3 -----
# v0.2 used a single LIR_LIM = 3.0e31 erg/s "band-peak nuLnu proxy (Chen+25)".
# No such number appears in Chen+2025.  Their Table 1 gives per-filter
# luminosity limits at four stated completeness levels.  Each filter now
# enters as its own independent Gaussian term on the predicted band-peak
# nuLnu, with sigma_j = L_lim,j / z(completeness) under the SAME one-sided
# convention used for the X-ray leg above.
#
# Two caveats, both quantified rather than buried:
#   (a) "Completeness" is a detection-recovery fraction, not a confidence
#       level.  Mapping it through the normal quantile is a convention.  It
#       is a defensible one because the three completeness rows then give
#       mutually consistent sigmas (~1.0-1.6e30 for F770W), which they would
#       not if the mapping were badly wrong.  All three rows are run.
#   (b) Combining four filters as independent terms treats one predicted
#       band-peak luminosity as constrained four times.  The filters observe
#       the same source, so the terms are correlated and the combination is
#       optimistic.  The tightest-single-filter variant is run alongside and
#       is the conservative reading.
COMPLETENESS_Z = {"99.7%": NormalDist().inv_cdf(0.997),   # 2.7478
                  "95%": NormalDist().inv_cdf(0.95),      # 1.6449
                  "68%": NormalDist().inv_cdf(0.68)}      # 0.4677
IR_COMPLETENESS_PRIMARY = "95%"     # matches the X-ray leg's stated CL


def ir_filters(completeness):
    """Per-filter (name, L_lim erg/s, sigma erg/s) at one completeness row."""
    out = []
    for row in INPUTS["chen2025jwst"]["per_filter_limits"]["table"]:
        if row["completeness"] != completeness:
            continue
        L = row["lum_lim_1e30ergs"] * 1e30
        out.append({"filter": row["filter"], "completeness": completeness,
                    "L_lim": L, "sigma": L / COMPLETENESS_Z[completeness],
                    "vega_mag_limit": row["vega_mag_limit"]})
    return out


IR_SETS = {cname: ir_filters(cname) for cname in COMPLETENESS_Z}
# Chen's "delta_color=1" row is a colour-selection depth, not a completeness
# fraction; it has no normal-quantile reading and is carried as metadata only.
IR_DELTACOLOR_ROWS = [r for r in
                      INPUTS["chen2025jwst"]["per_filter_limits"]["table"]
                      if r["completeness"] == "delta_color=1"]

# Mass-validity flag (metadata, carried with every IR-bearing number).
# Chen+2025's own stated accretion-constraint mass threshold is 1e4 Msun
# (Conclusions).  Paper F's tex currently says "~2e4 Msun", which is not
# their figure; flagged for the editorial session, not changed here.
IR_MASS_VALIDITY_MSUN = INPUTS["chen2025jwst"][
    "bh_mass_considered_for_own_constraint"]["value"]

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


def log_like(eps, M, th, family, sig_radio=SIG_S_RADIO, sig_fx=SIG_FX,
             ir_set=None, ir_scale=1.0, ir_mode="combined",
             d_ref_ir=D_REF_IR_CHEN):
    """Vectorized over draws for one (eps, M)."""
    if ir_set is None:
        ir_set = IR_SETS[IR_COMPLETENESS_PRIMARY]
    use_radio = FAMILIES[family][4]
    mdot = mdot_bondi(M, th)
    Lbol = eps * mdot * c ** 2

    # X-ray leg: Gaussian in measured 0.5-7 keV FLUX (distance-independent
    # observable; the drawn distance enters the prediction, not the limit).
    fX_pred = th["f_X"] * Lbol / (4 * np.pi * th["d"] ** 2)
    ll = -0.5 * (fX_pred / sig_fx) ** 2

    # IR leg: one Gaussian per JWST filter on the band-peak luminosity,
    # each limit quoted at its source distance and rescaled to the drawn one
    # (same convention as v0.2, now applied per filter).
    LIR_pred = th["f_IR"] * Lbol * (d_ref_ir / th["d"]) ** 2
    sigmas = [f["sigma"] * ir_scale for f in ir_set]
    if ir_mode == "tightest":
        sigmas = [min(sigmas)]
    for sig in sigmas:
        ll += -0.5 * (LIR_pred / sig) ** 2

    # Radio leg: forward FP with latent scatter -> predicted flux density
    if use_radio:
        LX_210 = th["f_X"] * Lbol * K_2TO10
        with np.errstate(divide="ignore"):
            logLR = (FP_A * np.log10(np.maximum(LX_210, 1e-30))
                     + FP_B * np.log10(M / Msun) + FP_C + th["fp"])
        S_pred = 10 ** logLR / (4 * np.pi * th["d"] ** 2 * 5.0e9)
        ll += -0.5 * ((S_pred - S_RADIO_MEAS) / sig_radio) ** 2
    return ll


def eps95_curve(masses, family, th, eps_grid=None, **kw):
    """95% credible upper limit on eps (log-uniform prior on the grid)."""
    grid = EPS_GRID if eps_grid is None else eps_grid
    out = []
    for M in masses:
        post = np.empty(len(grid))
        for i, e in enumerate(grid):
            ll = log_like(e, M, th, family, **kw)
            m = ll.max()
            post[i] = np.exp(m) * np.mean(np.exp(ll - m))
        post /= post.sum()
        cdf = np.cumsum(post)
        out.append(float(np.interp(0.95, cdf, grid)))
    return out


def eps_nat_draws(M, th):
    """eps_nat = eta_ADAF(mdot_horizon) * f_B, per draw."""
    mdot = mdot_bondi(M, th)
    r_B = G * M / th["c_s"] ** 2
    r_g = G * M / c ** 2
    f_B = (r_B / r_g) ** (-th["s"])
    mdot_edd = 1.4e18 * (M / Msun)          # g/s (10% efficiency conv.)
    mdot_hor = f_B * mdot / mdot_edd        # Eddington units
    eta = 0.1 * np.minimum(1.0, mdot_hor / 1e-2)
    return eta * f_B


def natural_band(masses, th):
    return [[float(np.percentile(eps_nat_draws(M, th), p))
             for p in (5, 50, 95)] for M in masses]


def excl_fraction(masses, eps95_vals, th):
    """P_excl = P[eps_nat > eps95] on the same nuisance draws."""
    return [float(np.mean(eps_nat_draws(M, th) > e))
            for M, e in zip(masses, eps95_vals)]


def run_all():
    res = {"M": (M_GRID / Msun).tolist(),
           "anchors_M": (ANCHORS / Msun).tolist()}

    th_base = {f: draw_theta(N_MC, f) for f in FAMILIES}

    # headline curves per family
    for f in FAMILIES:
        res["eps95_" + f] = eps95_curve(M_GRID, f, th_base[f])
        res["anchors_" + f] = eps95_curve(ANCHORS, f, th_base[f])

    # radio-free variant of the riaf family (FP-independent curve)
    _dead_draw = draw_theta(N_MC, "disk")   # unused in v0.2 as well; retained
    del _dead_draw                          # so the RNG stream matches v0.2's
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
                                        sig_radio=SIG_S_RADIO / 10.0)
    res["anchors_fc_miri_jet"] = eps95_curve(ANCHORS, "jet", th_base["jet"],
                                             ir_scale=1.0 / 3.0)

    # eps-prior floor sensitivity: refit riaf anchors with grid floored higher
    res["anchors_riaf_floor11"] = eps95_curve(
        ANCHORS, "riaf", th_base["riaf"], eps_grid=np.logspace(-11, -2, 91))

    # --- v0.3-specific sensitivity rows ------------------------------------
    # X-ray confidence-convention ladder (change 2)
    for name, z in XRAY_Z_VARIANTS.items():
        res["anchors_riaf_xz_" + name] = eps95_curve(
            ANCHORS, "riaf", th_base["riaf"], sig_fx=FX_LIM / z)
    # IR completeness-row ladder and correlation-conservative variant (change 3)
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
    # IR reference-distance variant: Chen's 5.49 vs Paper F's 5.43 kpc
    res["anchors_jet_ir_d543"] = eps95_curve(
        ANCHORS, "jet", th_base["jet"], d_ref_ir=D_REF_IR_PAPER)
    # v0.2's single-proxy IR leg with everything else at v0.3, to isolate
    # change 3 from change 2 in the DELTA attribution.
    _v2_ir = [{"filter": "v2_proxy", "completeness": None,
               "L_lim": 3.0e31, "sigma": 1.0e31, "vega_mag_limit": None}]
    for fam in ("riaf", "jet", "disk"):
        res["anchors_" + fam + "_irv2proxy"] = eps95_curve(
            ANCHORS, fam, th_base[fam], ir_set=_v2_ir,
            d_ref_ir=D_REF_IR_PAPER)
    res["anchors_riaf_noradio_irv2proxy"] = eps95_curve(
        ANCHORS, "disk", th_riaf_nr, ir_set=_v2_ir, d_ref_ir=D_REF_IR_PAPER)
    res["exclfrac_anchors_irv2proxy"] = {
        k: excl_fraction(ANCHORS, res["anchors_" + k + "_irv2proxy"],
                         th_base["riaf"])
        for k in ("riaf", "jet", "riaf_noradio")}
    # v0.2's X-ray sigma AND v0.2's IR proxy, i.e. the v0.2 likelihood itself,
    # recomputed here as the DELTA's reproduction check.
    for fam in ("riaf", "jet", "disk"):
        res["anchors_" + fam + "_v2repro"] = eps95_curve(
            ANCHORS, fam, th_base[fam], sig_fx=FX_LIM / 3.0, ir_set=_v2_ir,
            d_ref_ir=D_REF_IR_PAPER)
    res["anchors_riaf_noradio_v2repro"] = eps95_curve(
        ANCHORS, "disk", th_riaf_nr, sig_fx=FX_LIM / 3.0, ir_set=_v2_ir,
        d_ref_ir=D_REF_IR_PAPER)

    # natural-expectation band + exclusion fractions
    res["nat_band"] = natural_band(M_GRID, th_base["riaf"])
    res["nat_anchors"] = natural_band(ANCHORS, th_base["riaf"])
    res["exclfrac_anchors"] = {
        k: excl_fraction(ANCHORS, res["anchors_" + k], th_base["riaf"])
        for k in ("riaf", "jet", "riaf_noradio")}
    res["exclfrac_curve"] = {
        k: excl_fraction(M_GRID, res["eps95_" + k], th_base["riaf"])
        for k in ("riaf", "jet", "riaf_noradio")}
    res["exclfrac_anchors_v2repro"] = {
        k: excl_fraction(ANCHORS, res["anchors_" + k + "_v2repro"],
                         th_base["riaf"])
        for k in ("riaf", "jet", "riaf_noradio")}

    res["config"] = {
        "version": "v0.3", "N_MC": N_MC, "mu_e": MU_E, "lambda": LAM,
        "c_s_kms": [11.7, 16.6], "s": [0.3, 0.5],
        "ne_median": 0.23, "ne_width_dex": 0.5,
        "families": {k: v for k, v in FAMILIES.items()},
        "seed": 42,
        "D_REF_X_kpc": D_REF_X / kpc,
        "D_REF_IR_kpc": D_REF_IR_CHEN / kpc,
        "D_REF_IR_paper_kpc": D_REF_IR_PAPER / kpc,
        "FX_lim": FX_LIM, "FX_confidence": _hag["confidence"],
        "FX_z_used": XRAY_Z, "FX_z_variants": XRAY_Z_VARIANTS,
        "sig_FX": SIG_FX, "sig_S_radio": SIG_S_RADIO,
        "ir_completeness_primary": IR_COMPLETENESS_PRIMARY,
        "ir_completeness_z": COMPLETENESS_Z,
        "ir_filters": IR_SETS,
        "ir_deltacolor_rows_metadata_only": IR_DELTACOLOR_ROWS,
        "ir_mass_validity_Msun": IR_MASS_VALIDITY_MSUN,
        "ir_mass_validity_note": (
            "Chen+2025 state their accretion constraint for M_BH <~ 1e4 Msun "
            "(Conclusions). The 4e4 Msun anchor extrapolates beyond that; "
            "the tex's '~2e4 Msun' is not Chen's figure."),
        "inputs_file": "fF_measured_inputs.json",
        "inputs_wu": INPUTS["_meta"]["wu"],
    }
    return res


def write_epochs():
    """CHANGE 4: Mahida+2026 Table 1 block list for the duty-cycle section."""
    blk = INPUTS["mahida2026"]["observing_blocks"]
    rows = blk["table"]
    total = round(sum(r["hours"] for r in rows), 2)
    by_project = {}
    for r in rows:
        by_project.setdefault(r["project"], {"blocks": 0, "hours": 0.0})
        by_project[r["project"]]["blocks"] += 1
        by_project[r["project"]]["hours"] += r["hours"]
    for v in by_project.values():
        v["hours"] = round(v["hours"], 2)
    out = {
        "source": "Mahida et al. 2026 (arXiv:2512.09649), Table 1",
        "extraction_wu": INPUTS["_meta"]["wu"],
        "blocks": rows,
        "n_blocks": len(rows),
        "total_hours_table": total,
        "by_project": by_project,
        "prose_totals_stated": {"abstract": "~170 hr",
                                "section_II.3": "172 hr"},
        "discrepancy_note": (
            "Three totals are in play and this export resolves none of "
            "them. (i) The 25 extracted Table 1 rows sum to %.2f hr. (ii) "
            "The paper's own prose says ~170 hr (Abstract) and 172 hr "
            "(Section II.3). (iii) The OCS-F-DATA-1 extraction report "
            "states the rows sum to ~148.1 hr and reads that as a shortfall "
            "against the prose; that figure is close to the CX556 project "
            "subtotal alone (%.2f hr) and does not match the full 25-row "
            "sum, so the report's '148 vs 170 hr' framing should be "
            "re-checked against Table 1 before it is repeated in the "
            "manuscript. Note the sign: the full sum EXCEEDS the prose "
            "total rather than falling short of it, which is the opposite "
            "of the discrepancy the report describes and is consistent with "
            "prose quoting post-flagging on-source time. The block list is "
            "reported as printed. If the duty-cycle argument counts "
            "independent epochs, the block list is the quantity to use."
            % (total, by_project["CX556"]["hours"])),
        "epoch_span": {"first": min(r["date"] for r in rows),
                       "last": max(r["date"] for r in rows)},
    }
    with open(os.path.join(HERE, "fF_epochs.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def write_maveric():
    """CHANGE 6: Tremou+2018 anchors staged for the future context figure."""
    t = INPUTS["tremou2018"]
    out = {
        "source": "Tremou et al. 2018 (arXiv:1806.00259), MAVERIC survey",
        "extraction_wu": INPUTS["_meta"]["wu"],
        "omega_cen": t["omega_cen_row"],
        "sample_context": t["sample_context"],
        "frequencies_and_rms": t.get("frequencies_and_rms"),
        "staging_note": (
            "Data staging only; no Tremou value enters the v0.3 posterior. "
            "Two internal ambiguities travel with these numbers: the omega "
            "Cen flux limit is 8.8 uJy in Table 2 and 8.9 uJy in Section "
            "V.2.1, and the VLA stack mass limit is given as both <800 and "
            "<730 Msun in one sentence. Both are reported unresolved. "
            "Tremou's adopted distance for omega Cen (4.9 kpc) is lower than "
            "Haggard's 5.2 and Chen/Mahida's ~5.49; any context figure must "
            "state which distance each point assumes."),
    }
    with open(os.path.join(HERE, "fF_maveric_context.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def write_pgf(res):
    """Figure coordinate table, same format as fF_v2_pgf.txt."""
    lines = []
    M = res["M"]

    def coords(vals):
        return " ".join("(%g,%.3e)" % (m, v) for m, v in zip(M, vals))

    for key in ("eps95_riaf", "eps95_jet", "eps95_disk", "eps95_riaf_noradio"):
        lines.append("%s: %s" % (key, coords(res[key])))
    for i, tag in enumerate(("NAT05", "NAT50", "NAT95")):
        lines.append("%s: %s" % (tag, coords([r[i] for r in res["nat_band"]])))
    with open(os.path.join(HERE, "fF_v3_pgf.txt"), "w") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    res = run_all()
    with open(os.path.join(HERE, "fF_v3_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    write_pgf(res)
    with open(os.path.join(HERE, "fF_v3_exclfrac.json"), "w") as fh:
        json.dump(res["exclfrac_anchors"], fh)
    ep = write_epochs()
    write_maveric()

    names = ["riaf", "jet", "disk", "riaf_noradio", "riaf_wide", "riaf_lowne",
             "riaf_floor", "fc_ne", "fc_ska", "fc_miri_jet", "riaf_floor11",
             "riaf_xz_onesided95", "riaf_xz_twosided95", "riaf_xz_v2_over3",
             "riaf_ir997", "riaf_ir95", "riaf_ir68", "riaf_ir_tightest",
             "jet_ir997", "jet_ir95", "jet_ir68", "jet_ir_tightest",
             "jet_ir_d543", "riaf_irv2proxy", "jet_irv2proxy",
             "disk_irv2proxy", "riaf_noradio_irv2proxy",
             "riaf_v2repro", "jet_v2repro", "disk_v2repro",
             "riaf_noradio_v2repro"]
    for n in names:
        v = res["anchors_" + n]
        print("%-22s eps95 @ 6k/8.2k/40k = %.3e / %.3e / %.3e"
              % (n, v[0], v[1], v[2]))
    print("exclfrac", {k: ["%.4f" % x for x in v]
                       for k, v in res["exclfrac_anchors"].items()})
    print("exclfrac v2repro", {k: ["%.4f" % x for x in v]
                               for k, v in
                               res["exclfrac_anchors_v2repro"].items()})
    print("nat anchors 5/50/95:",
          [["%.2e" % x for x in r] for r in res["nat_anchors"]])
    print("epochs: %d blocks, %.1f hr"
          % (ep["n_blocks"], ep["total_hours_table"]))
