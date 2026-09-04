"""R9-C-1: standalone recomputation of every non-Monte-Carlo Paper C finding.

Covers the merged R8 + R9 + Bob item set for the campaign paper:

  C-R9-01 / C-R8-01 / C-B1   astrometric estimator, the two epoch-count cases
  C-R9-02 / C-B1             5-sigma crossing baselines under each case
  C-R9-05 / C-R8-02 / C-B4   wander variance discrimination, degrees of freedom
  C-R9-06 / C-R8-03          positional wander r_bullet vs centre error
  C-R9-07 / C-B3             neutrino triplet, window by window
  C-R9-08 / C-R8-09 / C-B6   two-epoch variability floors
  C-R8-07                    timing N_eff
  C-R9-09 / C-R8-10          spectrometer data rate

Nothing here reads or writes the Monte Carlo forecast; that lives in
fC_calc7b_d2forecast_v2.py.  Output: paper/figs/fC_r9_checks.json
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

D_KPC = 5.49
G_PC = 4.30091e-3                          # pc Msun^-1 (km/s)^2
PC_M = 3.085677581e16
YEAR_S = 3.15576e7
MASYR_KMS = 4.74047 * D_KPC                # 1 mas/yr at 5.49 kpc, in km/s
ARCSEC_PC = D_KPC * 1000.0 / 206264.806    # pc per arcsec

out = {}

# ---------------------------------------------------------------------
# 1. Acceleration signal and the astrometric estimator (C-R9-01/02)
# ---------------------------------------------------------------------


def a_signal_masyr2(M, r_pc):
    """GM/r^2 expressed as a proper-motion acceleration in mas/yr^2."""
    a_kms2_pc = G_PC * M / r_pc ** 2       # (km/s)^2 / pc
    a_ms2 = a_kms2_pc * 1.0e6 / PC_M       # m/s^2
    a_kms_yr = a_ms2 * YEAR_S / 1.0e3      # km/s per yr
    return a_kms_yr / MASYR_KMS            # mas/yr^2


sig_nom = a_signal_masyr2(2.0e4, 0.08)
sig_hvy = a_signal_masyr2(4.9e4, 0.08)


def sigma_a(sig_pos_mas, N, T):
    return 26.83 * sig_pos_mas / (math.sqrt(N) * T ** 2)


HST_POS, ELT_POS = 0.020, 0.070

cases = {}
for label, N_of_T in (("uniform_N_eq_2T", lambda T: 2.0 * T),
                      ("sparse_N_eff_2", lambda T: 2.0)):
    rows = {}
    for T in (20.0, 26.0):
        s = sigma_a(HST_POS, N_of_T(T), T)
        rows["T%d" % int(T)] = {"sigma_a_masyr2": s,
                                "snr_nominal": sig_nom / s,
                                "snr_heavy": sig_hvy / s}

    def crossing(signal, sig_pos, N_of_T=N_of_T):
        lo, hi = 1.0, 400.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if 5.0 * sigma_a(sig_pos, N_of_T(mid), mid) > signal:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    rows["cross5sig_yr"] = {
        "hst_nominal": crossing(sig_nom, HST_POS),
        "hst_heavy": crossing(sig_hvy, HST_POS),
        "elt_nominal": crossing(sig_nom, ELT_POS),
        "elt_heavy": crossing(sig_hvy, ELT_POS)}
    cases[label] = rows

N_implied = (26.83 * HST_POS / (1.0e-3 * 400.0)) ** 2
pos_implied = 1.0e-3 * math.sqrt(40.0) * 400.0 / 26.83

# --- the calibrated chain: eliminate (sigma_pos, N) using the SAME fit's
# proper-motion precision.  For a least-squares fit of x = x0 + v t + a t^2/2
# to N epochs uniformly spread over T with per-epoch error sigma_pos,
#   sigma_v = sqrt(12) sigma_pos / (sqrt(N) T)      [Var(a1) = 12 s^2/(N T^2)]
#   sigma_a = 26.83  sigma_pos / (sqrt(N) T^2)      [Var(a2) = 180 s^2/(N T^4), a = 2 a2]
# so sigma_a / sigma_mu = 26.83/(sqrt(12) T) = 7.746/T, free of sigma_pos and N.
# Any epoch distribution sparser than uniform is worse, so this is a bound.
K_AMU = 26.83 / math.sqrt(12.0)          # 7.7457


def sigma_a_from_mu(sig_mu_masyr, T):
    return K_AMU * sig_mu_masyr / T


OMEGACAT_MU_CENTRAL = 0.0066     # mas/yr, r < 1.5 arcmin (Haberle 2024, abstract)
OMEGACAT_MU_MEDIAN = 0.011       # mas/yr, mF625W ~ 18 survey median
OMEGACAT_T = 20.0

calib = {}
for tag, mu in (("central_r_lt_1.5arcmin", OMEGACAT_MU_CENTRAL),
                ("survey_median", OMEGACAT_MU_MEDIAN)):
    s20 = sigma_a_from_mu(mu, OMEGACAT_T)
    rows = {"sigma_mu_masyr": mu, "sigma_a_at_T20": s20,
            "snr_nominal_T20": sig_nom / s20, "snr_heavy_T20": sig_hvy / s20,
            "equivalent_sigma_pos_over_sqrtN_mas": s20 * OMEGACAT_T ** 2 / 26.83}
    for T in (26.0, 38.0):
        s = s20 * (OMEGACAT_T / T) ** 2.5
        rows["T%d" % int(T)] = {"sigma_a_masyr2": s,
                                "snr_nominal": sig_nom / s,
                                "snr_heavy": sig_hvy / s}
    for nsig, sig, nm in ((1.0, sig_nom, "1sig_nominal"),
                          (5.0, sig_nom, "5sig_nominal"),
                          (5.0, sig_hvy, "5sig_heavy")):
        rows["cross_%s_yr" % nm] = OMEGACAT_T * (s20 * nsig / sig) ** 0.4
    # what a 5-sigma detection at T = 20 yr would need instead of time:
    # signal >= 5 sigma_a, with signal proportional to M/r^2
    need = 5.0 * s20
    rows["M_for_5sig_at_r0.08pc"] = 2.0e4 * need / sig_nom
    rows["r_for_5sig_at_M2e4_pc"] = 0.08 * math.sqrt(sig_nom / need)
    calib[tag] = rows

out["C-R9-01_02_astrometry"] = {
    "signal_masyr2": {"M2e4_r0.08pc": sig_nom, "M4.9e4_r0.08pc": sig_hvy},
    "printed_signal": {"nominal": 5.3e-4, "heavy": 1.3e-3},
    "cases": cases,
    "printed_1e-3_implies_N": N_implied,
    "printed_1e-3_at_N_eq_2T_implies_sigma_pos_mas": pos_implied,
    "k_sigma_a_over_sigma_mu_times_T": K_AMU,
    "calibrated_to_published_sigma_mu": calib,
    "elt_4yr_check_masyr2": sigma_a(ELT_POS, 8.0, 4.0),
    "elt_4yr_printed": 4.0e-2,
    "elt_equivalent_sigma_mu_masyr": math.sqrt(12.0) * ELT_POS
                                     / (math.sqrt(8.0) * 4.0)}

# ---------------------------------------------------------------------
# 2. Wander amplitudes and the variance-discrimination dof (C-R9-05)
# ---------------------------------------------------------------------
SIGMA_STAR = 21.0                          # km/s, the paper set's fiducial
M_EFF, M_BAR, M_BAR_EQ = 2.3, 0.54, 0.30


def wander_muasyr(M, m_eff):
    v = SIGMA_STAR * math.sqrt(m_eff / M)  # km/s
    return v / MASYR_KMS * 1.0e3           # muas/yr


amp = {}
for M in (6.0e3, 8.2e3, 4.9e4):
    for m in (M_EFF, M_BAR, M_BAR_EQ):
        amp["M%d_meff%s" % (int(M), m)] = wander_muasyr(M, m)

ratio_light = math.sqrt(8200.0 / 6000.0) - 1.0
ratio_lh = math.sqrt(4.9e4 / 8.2e3)


def dof_needed(amp_ratio, nsig):
    """Variance contrast f = ratio^2 - 1; the relative error of a variance
    estimate on N degrees of freedom is sqrt(2/N); require f >= nsig sqrt(2/N)."""
    f = amp_ratio ** 2 - 1.0
    return 2.0 * nsig ** 2 / f ** 2


out["C-R9-05_wander"] = {
    "sigma_star_kms": SIGMA_STAR,
    "amplitudes_muas_yr": amp,
    "light_split_fraction": ratio_light,
    "light_heavy_factor": ratio_lh,
    "dof_for_17pct_split": {"3sig": dof_needed(1.0 + ratio_light, 3.0),
                            "5sig": dof_needed(1.0 + ratio_light, 5.0)},
    "dof_for_factor2.4": {"3sig": dof_needed(ratio_lh, 3.0),
                          "5sig": dof_needed(ratio_lh, 5.0)},
    "epochs_available": 10,
    "rel_error_of_variance_at_10dof": math.sqrt(2.0 / 10.0),
    # the numeric pre-condition the factor-2.4 deliverable needs: the
    # light and heavy predictions are separated by |delta| muas/yr, so a
    # 3-sigma call requires every error, N-body scatter included, under
    # |delta|/3.
    "light_heavy_separation_muasyr": wander_muasyr(8.2e3, M_EFF)
                                     - wander_muasyr(4.9e4, M_EFF),
    "required_total_error_3sig_muasyr": (wander_muasyr(8.2e3, M_EFF)
                                         - wander_muasyr(4.9e4, M_EFF)) / 3.0,
    "required_total_error_5sig_muasyr": (wander_muasyr(8.2e3, M_EFF)
                                         - wander_muasyr(4.9e4, M_EFF)) / 5.0}

# ---------------------------------------------------------------------
# 2b. Two arithmetic LOWs (LISA confusion floor, cost total)
# ---------------------------------------------------------------------
out["LOW_arithmetic"] = {
    "lisa_sqrtSn_2mHz_with_78pct_power": 3.0e-20 * math.sqrt(1.78),
    "lisa_printed": 4.3e-20,
    "cost_subtotal_kUSD": 7249.0,
    "cost_with_20pct_kUSD": 7249.0 * 1.2}

# ---------------------------------------------------------------------
# 3. Positional wander (C-R9-06 / C-R8-03)
# ---------------------------------------------------------------------
RHO0 = 3.0e3                               # Msun/pc^3, the paper's own core density
omega = math.sqrt(4.0 * math.pi * G_PC * RHO0 / 3.0)   # (km/s)/pc


def r_wander(M, m_eff):
    v = SIGMA_STAR * math.sqrt(m_eff / M)
    r1d = v / omega                        # pc, 1-D rms
    return {"pc_1d": r1d, "arcsec_1d": r1d / ARCSEC_PC,
            "arcsec_proj2d": math.sqrt(2.0) * r1d / ARCSEC_PC}


rw = {}
for M in (6.0e3, 8.2e3, 4.9e4):
    for m in (M_EFF, M_BAR):
        rw["M%d_meff%s" % (int(M), m)] = r_wander(M, m)

out["C-R9-06_positional_wander"] = {
    "rho0_Msun_pc3": RHO0, "omega_kms_per_pc": omega,
    "centre_error_arcsec": 1.0, "search_radius_arcsec": 3.0,
    "fiducial_r_arcsec": 0.08 / ARCSEC_PC,
    "cases": rw}

# ---------------------------------------------------------------------
# 4. Neutrino triplet, window by window (C-R9-07 / C-B3)
# ---------------------------------------------------------------------


def p_ge_k(mu, k):
    """Poisson upper tail, summed FORWARD from j = k.

    The complement form 1 - sum_{j<k} works out to a difference of numbers
    near 1, so at mu ~ 1e-5 it loses every significant digit: the answer is
    ~1e-16, the same size as the rounding error, and at mu ~ 1e-4 with k = 4
    it can come out negative.  Summing the tail itself has no cancellation.
    """
    term = math.exp(-mu)
    for j in range(1, k + 1):
        term *= mu / j
    tail, j = term, k
    while term > 1e-18 * max(tail, 1e-300):
        j += 1
        term *= mu / j
        tail += term
    return tail


def z_of_p(p):
    """One-sided Gaussian equivalent significance."""
    if p <= 0.0:
        return float("inf")
    lo, hi = 0.0, 40.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if 0.5 * math.erfc(mid / math.sqrt(2.0)) > p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


DECADE_S = 10.0 * YEAR_S
P5 = 0.5 * math.erfc(5.0 / math.sqrt(2.0))
neut = {}
for rate_name, rate in (("envelope_1e-7", 1.0e-7),
                        ("realistic_4.75e-9", 4.75e-9)):
    rows = {}
    for W in (1.0e2, 1.0e3, 1.0e4):
        mu = rate * W
        ntrial = DECADE_S / W
        rows["W%d_n_windows" % int(W)] = ntrial
        for k in (3, 4):
            p1 = p_ge_k(mu, k)
            post = p1 * ntrial
            rows["W%d_k%d" % (int(W), k)] = {
                "mu": mu, "p_single": p1, "n_windows": ntrial,
                "p_posttrials": post, "sigma": z_of_p(post),
                "passes_5sigma": bool(post < P5)}
    neut[rate_name] = rows

# Where the printed 5e-7 comes from: the 1000-s expectation paired with the
# 100-s trials count.  Each window size carries its own count.
mismatch = p_ge_k(1.0e-7 * 1.0e3, 3) * (DECADE_S / 1.0e2)
out["C-R9-07_neutrino"] = {
    "p_threshold_5sigma": P5,
    "printed_posttrials": 5.0e-7,
    "printed_n_windows": 3.0e6,
    "n_windows_by_size": {"100s": DECADE_S / 1.0e2,
                          "1000s": DECADE_S / 1.0e3,
                          "10000s": DECADE_S / 1.0e4},
    "printed_5e-7_reproduced_by_mismatched_pairing": mismatch,
    "note": "the printed 3e6 windows is the count for 100-s windows; "
            "applying it to the 1000-s expectation is what gives 5e-7",
    "cases": neut}

# ---------------------------------------------------------------------
# 5. Two-epoch variability floors (C-R9-08 / C-B6)
# ---------------------------------------------------------------------
DEPTH3 = {"NIRCam_F444W": (10.0, 30.0),
          "MIRI_F1000W_post_crowding": (500.0, 500.0),
          "MIRI_F1000W_photon_only": (115.126, 500.0)}
var = {}
for band, (d3, printed) in DEPTH3.items():
    s1 = d3 / 3.0                          # 1-sigma, single epoch
    sdiff = math.sqrt(2.0) * s1            # 1-sigma on the epoch difference
    rows = {"depth3sig_nJy": d3, "sigma_single_nJy": s1,
            "sigma_diff_nJy": sdiff, "printed_floor_nJy": printed}
    for amp_pct in (20.0, 30.0):
        rows["floor_3sig_at_%dpct_nJy" % int(amp_pct)] = \
            3.0 * sdiff / (amp_pct / 100.0)
        rows["floor_5sig_at_%dpct_nJy" % int(amp_pct)] = \
            5.0 * sdiff / (amp_pct / 100.0)
        rows["sigma_of_printed_at_%dpct" % int(amp_pct)] = \
            (amp_pct / 100.0) * printed / sdiff
    var[band] = rows
out["C-R9-08_variability"] = var

# ---------------------------------------------------------------------
# 6. Timing N_eff (C-R8-07)
# ---------------------------------------------------------------------
psr_path = os.path.join(HERE, os.pardir, "h", "data", "pulsars.json")
with open(psr_path, encoding="utf-8") as f:
    psr = json.load(f)["pulsars"]


# The record's timing_baseline field is free text, so the baseline each
# solution actually spans is assigned here from that text, once, in the open:
#   Murriyang UWL full campaign  2020-04-01 -> 2025-05-20  = 5.13 yr
#   MeerKAT-only solutions       2021 -> 2025              = 4.0 yr
T_MURRIYANG_FULL, T_MEERKAT_ONLY = 5.13, 4.0
BASELINE_YR = {"A": T_MURRIYANG_FULL, "B": T_MURRIYANG_FULL,
               "C": T_MURRIYANG_FULL, "D": T_MURRIYANG_FULL,
               "E": T_MURRIYANG_FULL, "H": T_MURRIYANG_FULL,
               "K": T_MURRIYANG_FULL, "G": T_MEERKAT_ONLY,
               "I": T_MEERKAT_ONLY, "L": T_MEERKAT_ONLY,
               "N": T_MEERKAT_ONLY, "Q": T_MEERKAT_ONLY}
NO_SOLUTION = ["F", "J", "M", "O", "P", "R"]
SINGLE_EPOCH = ["S"]

timed = []
for p in psr:
    L = p.get("letter")
    if L in BASELINE_YR:
        timed.append({"name": p.get("name"), "letter": L,
                      "P_ms": p["P"]["value"], "T_yr": BASELINE_YR[L],
                      "baseline_source": p["timing_baseline"]["value"][:80]})

# sigma_a,i  ~  P_i sigma_t,i / T_i^2 ; weights w_i = 1/sigma_a,i.
w = [t["T_yr"] ** 2 / t["P_ms"] for t in timed]
neff = sum(w) ** 2 / sum(x * x for x in w)
w2 = [t["T_yr"] ** 2 for t in timed]                       # period-free reading
neff_noP = sum(w2) ** 2 / sum(x * x for x in w2)
neff_flat = float(len(timed))                              # equal-weight reading

# Does the common ToA-precision factor really cancel?  Scale every sigma_t by
# an arbitrary constant and recompute; N_eff is a ratio of weight moments, so
# it must be invariant.  This is the check C-R8-07 asks for.
w_scaled = [x / 3.7 for x in w]
neff_scaled = sum(w_scaled) ** 2 / sum(x * x for x in w_scaled)

out["C-R8-07_Neff"] = {"n_with_solution": len(timed), "n_total": len(psr),
                       "n_no_solution": len(NO_SOLUTION),
                       "n_single_epoch": len(SINGLE_EPOCH),
                       "printed": 9.8,
                       "Neff_with_period_weight": neff,
                       "Neff_baseline_only": neff_noP,
                       "Neff_equal_weight": neff_flat,
                       "Neff_after_common_sigma_t_rescale": neff_scaled,
                       "common_factor_cancels": abs(neff_scaled - neff) < 1e-9,
                       "baseline_assignment_yr": BASELINE_YR,
                       "pulsars": timed}

# ---------------------------------------------------------------------
# 7. Spectrometer data rate (C-R9-09 / C-R8-10)
# ---------------------------------------------------------------------
BW_HZ = 856.0e6                            # MeerKAT L band
CHAN_HZ = 1.0
POL = 2
rate_rows = {}
for nbytes, tag in ((4, "float32"), (2, "int16"), (1, "int8")):
    for dump in (1.0, 8.0, 60.0):
        tb_hr = BW_HZ / CHAN_HZ * POL * nbytes / dump * 3600.0 / 1.0e12
        rate_rows["%s_dump%ds" % (tag, int(dump))] = tb_hr
bits_per_sample = 0.7e12 / 3600.0 * 8.0 / (BW_HZ / CHAN_HZ * POL)
out["C-R9-09_datarate"] = {
    "printed_TB_per_hr": 0.7,
    "bits_per_spectral_sample_implied": bits_per_sample,
    "ladder_TB_per_hr": rate_rows,
    "note": "0.7 TB/hr requires stated averaging, not raw 1-s dumps"}

with open(os.path.join(HERE, "fC_r9_checks.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("written fC_r9_checks.json")
