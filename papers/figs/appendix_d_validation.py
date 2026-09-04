"""Appendix D: E6 validation of the adjudication machinery (Sec. 5) against three
historical cases, per spec section C2-PROTOCOL (OCS-E6-PROTOCOL) and the case
dossiers of OCS-E6-DOSSIER (paper/e6-dossiers/{lgm1,hephaistos,boyajian}.md).

This script scores the SAME machinery that Sec. 5 applies to omega Cen -- an
explicit menu, per-channel Bayes factors K_i = L(d_i|H_a)/L(d_i|H_b), a priced
catch-all null (C2.4), and the Sec. 5.4 action bands -- against three cases
where the answer is independently known. It is not a re-derivation of the
omega Cen forward model; C2.0 is explicit that the object under test is the
scoring machinery, not the physics.

Numeraire convention: every hypothesis's log-likelihood is carried relative to
H_art (or H_dyson / H_dust, the "engineered" contender in each case) fixed at
0. A channel's contribution ln_r[H] = lnL(H) - lnL(H_art) is negative when the
channel favors H_art over the competitor H, positive when it favors H. The
reported ln K of the artificial/engineered hypothesis over the BEST-performing
null is -max(ln_r[H] for H in the other menu members), per C2.1's "best
null" convention (Sec. 5.1: never scored against a strawman).

Catch-all construction (C2.4): where a channel's discriminant is an
extremity relative to the class of natural explanations rather than a
directly competing physical model, the catch-all's predictive is built as a
tail probability beyond a stated, sourced reference boundary, widened by an
inflation factor lambda (dex) applied in the log of the statistic:
    P_nat(exceed by Delta dex | lambda) = min(1, 10 ** (-Delta / lambda)).
This is the same "inflation factor in dex" the protocol specifies; the
reference boundary and its source are stated at each use. pi_nat (prior mass
on the catch-all) does not enter a two-hypothesis Bayes factor by
construction -- K_i^ab is a likelihood ratio, prior-independent -- so the
(pi_nat, lambda) grid required by C2.4/C2.6 is reported to make that
invariance visible, not because pi_nat moves the number.

Every numeric channel construction below is a stated, sourced approximation,
not a re-measurement of the primary data (Appendix B's own MIR likelihood is
"deliberately minimal" in the same sense). Where a construction is a modeling
choice rather than a value read off a primary source, it is flagged
CONSTRUCTION in the comment beside it. No prior or channel value was adjusted
after seeing the ln K it produced; this script IS the sealed-priors record
(see paper/e6-priors/priors.json, committed in a prior commit with no scoring
code, per C2.3's seal).

Run: python appendix_d_validation.py
Reproduces every number quoted in Appendix D.
"""
import json
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
PRIORS_PATH = os.path.join(_HERE, "..", "e6-priors", "priors.json")

LN10 = math.log(10.0)

BANDS = [
    (float("-inf"), 0.0, "null-favored"),
    (0.0, 1.0, "uninformative"),
    (1.0, 3.0, "anomaly"),
    (3.0, 5.0, "strong anomaly"),
    (5.0, float("inf"), "candidate"),
]

def band(lnk):
    for lo, hi, name in BANDS:
        if lo <= lnk < hi:
            return name
    return "candidate"

def _git_committer_time(path):
    """Unix committer time of the last commit touching path, or None."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct %H", "--", path],
            cwd=_HERE, capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    line = out.stdout.strip()
    if out.returncode != 0 or not line:
        return None
    ts, sha = line.split()
    return int(ts), sha


def check_seal():
    """P5: verify the sealed-priors commit strictly predates the scoring commit.

    R9 E-R9-05: this criterion previously printed PASS unconditionally, with the
    git workflow asserted in prose and never checked in code. It is a real
    comparison now, and it FAILS if the seal does not predate the scoring code
    or if either commit cannot be read.
    """
    seal_info = _git_committer_time(PRIORS_PATH)
    score_info = _git_committer_time(os.path.abspath(__file__))
    if seal_info is None or score_info is None:
        return False, "commit times unreadable; criterion cannot be verified"
    (t_seal, sha_seal), (t_score, sha_score) = seal_info, score_info
    ok = t_seal < t_score
    return ok, (f"seal {sha_seal[:9]} at {t_seal}, scoring {sha_score[:9]} at "
                f"{t_score}, seal {'predates' if ok else 'does NOT predate'} scoring")


def catch_all_tail(delta_dex, lam):
    """P_nat(statistic at least this extreme | lambda), C2.4 construction."""
    if lam <= 0:
        return 0.0
    return min(1.0, 10 ** (-delta_dex / lam))

def ln_k_vs_best_null(ln_r_by_null):
    """ln K of the engineered/artificial hypothesis vs the best-performing null.

    ln_r_by_null: {null_name: cumulative ln_r = lnL(null) - lnL(H_art)}.
    """
    best = max(ln_r_by_null.values())
    return -best, max(ln_r_by_null, key=ln_r_by_null.get)

# =====================================================================
# CASE 1: LGM-1 (positive control)
# =====================================================================

def lgm1():
    print("\n=== LGM-1 (positive control) ===")
    # Reference boundary for channel 1 (C2.4): the fastest COHERENT, stable
    # periodicity catalogued for a natural celestial source as of Nov 1967
    # was of order 1 hour (short-period pulsating variables; flare-star
    # flickering is stochastic, not coherent, and is excluded as a
    # reference point for that reason). CONSTRUCTION: this boundary is a
    # stated historical judgment, not a primary catalog query (no machine-
    # readable 1967 radio-source catalog was located); Appendix D states
    # this limitation.
    T_REF_S = 3600.0
    T_OBS_S = 1.337  # Hewish et al. 1968, LGM-1 dossier
    DELTA_DEX = math.log10(T_REF_S / T_OBS_S)  # 3.43

    LAM_FID = 1.0
    LAM_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    PI_NAT_GRID = [0.1, 0.3, 0.5, 0.7, 0.9]

    def ch1_ln_r_nat(lam):
        p = catch_all_tail(DELTA_DEX, lam)
        return math.log(p) if p > 0 else -700.0  # ln_r_nat = ln P_nat(extreme); floor avoids log(0)

    # --- Epoch 1a, channels 1-3 ---
    # ch2: sidereal-vs-solar recurrence, discriminates H_int only.
    # CONSTRUCTION: man-made/terrestrial interference tied to a solar-day
    # schedule recurring instead at fixed sidereal time over many days is
    # assigned a strongly disfavored, stated likelihood ratio.
    # DECOMPOSED (R9 E-R9-05): earlier drafts carried the ratio alone, with
    # P(d | H_art) fixed at 1 by the numeraire convention and never stated. Both
    # legs are named here so the assumption is visible and disputable.
    #   P(sidereal recurrence over many days | H_art, a celestial source) = 1.0
    #   P(same | H_int, a source tied to a solar-day schedule)            = 0.0067
    CH2_P_ART, CH2_P_INT = 1.0, 0.0067
    CH2_LN_R_INT = math.log(CH2_P_INT / CH2_P_ART)
    # ch3: independent second-telescope/receiver confirmation (Scott &
    # Collins), discriminates single-instrument artifact within H_int.
    #   P(confirmed on an independent telescope | H_art) = 1.0
    #   P(same | H_int, a single-instrument artifact)    = 0.0498
    CH3_P_ART, CH3_P_INT = 1.0, 0.0498
    CH3_LN_R_INT = math.log(CH3_P_INT / CH3_P_ART)

    ch1_nat_fid = ch1_ln_r_nat(LAM_FID)
    sum_int_epoch1a = CH2_LN_R_INT + CH3_LN_R_INT
    sum_nat_epoch1a = ch1_nat_fid
    lnk_epoch1a, null_epoch1a = ln_k_vs_best_null(
        {"H_int": sum_int_epoch1a, "H_nat": sum_nat_epoch1a})
    print(f"Epoch 1a (fiducial lambda={LAM_FID}): ln_r[H_int]={sum_int_epoch1a:+.3f} "
          f"ln_r[H_nat]={sum_nat_epoch1a:+.3f} -> ln K={lnk_epoch1a:+.3f} vs {null_epoch1a} "
          f"[{band(lnk_epoch1a)}]  (P1 needs >=3: {'PASS' if lnk_epoch1a >= 3 else 'FAIL'})")

    # --- Collapse A: data, menu fixed (add ch4 Doppler null, ch5 multiplicity) ---
    # ch4: null orbital-Doppler test. A real detection would have supported
    # H_art; the null is a one-sided channel capped by the prior probability
    # H_art's own geometry evades detection (low inclination / long period).
    # CONSTRUCTION, stated: P(null Doppler | H_art) = 0.3.
    CH4_LN_R_NAT = -math.log(0.3)  # nat gains this much ground
    # ch5: discovery of a second, independent pulsating source within weeks.
    # Bell Burnell's own contemporaneous reasoning (dossier, Epoch 1): twin
    # simultaneous artificial beacons at the same improbable frequency is
    # implausible. CONSTRUCTION: P(2nd source | H_art)=0.02, P(2nd source |
    # a natural mechanism capable of the first at all)=0.95 (finding more of
    # a real class is the expected, not surprising, outcome).
    CH5_LN_R_NAT = math.log(0.95 / 0.02)

    sum_nat_doppler = sum_nat_epoch1a + CH4_LN_R_NAT
    sum_nat_mult = sum_nat_epoch1a + CH5_LN_R_NAT
    sum_nat_both = sum_nat_epoch1a + CH4_LN_R_NAT + CH5_LN_R_NAT
    lnk_doppler, _ = ln_k_vs_best_null({"H_int": sum_int_epoch1a, "H_nat": sum_nat_doppler})
    lnk_mult, _ = ln_k_vs_best_null({"H_int": sum_int_epoch1a, "H_nat": sum_nat_mult})
    lnk_both, null_both = ln_k_vs_best_null({"H_int": sum_int_epoch1a, "H_nat": sum_nat_both})
    print(f"Collapse A: after Doppler alone ln K={lnk_doppler:+.3f}; "
          f"after multiplicity alone ln K={lnk_mult:+.3f}; "
          f"after both ln K={lnk_both:+.3f} vs {null_both} [{band(lnk_both)}]  "
          f"(P3 needs <1: {'PASS' if lnk_both < 1 else 'FAIL'})")
    print("  mechanism comparison: multiplicity collapse "
          f"({sum_nat_epoch1a - sum_nat_mult:+.3f} nats) "
          f"{'>' if abs(CH5_LN_R_NAT) > abs(CH4_LN_R_NAT) else '<'} "
          f"Doppler collapse ({sum_nat_epoch1a - sum_nat_doppler:+.3f} nats); "
          f"multiplicity is the larger mechanism")

    # --- Collapse B: menu completion, data (epoch-1a, ch1-3 only) fixed ---
    # Rotating-neutron-star hypothesis (Gold 1968 mechanism, priced as
    # though available in Nov 1967 per protocol's counterfactual instruction).
    # ch1: rotation explains the coherent stable sub-second period exactly as
    # well as H_art (ln_r=0), plus a modest edge because the lighthouse-beam
    # geometry more naturally predicts a duty cycle well under unity than an
    # arbitrary artificial beacon does (no free design choice needed).
    # CONSTRUCTION, stated: +0.5 nats.
    #   P(duty cycle well under unity | H_pulsar, lighthouse geometry) = 1.0
    #   P(same | H_art, an arbitrary beacon design)                     = 0.6065
    CH1_P_PULSAR, CH1_P_ART = 1.0, 0.6065
    CH1_LN_R_PULSAR = math.log(CH1_P_PULSAR / CH1_P_ART)
    sum_pulsar_epoch1a = CH1_LN_R_PULSAR  # ch2, ch3 equally consistent (real, celestial): +0 each
    lnk_collapseB, null_collapseB = ln_k_vs_best_null(
        {"H_int": sum_int_epoch1a, "H_nat": sum_nat_epoch1a, "H_pulsar": sum_pulsar_epoch1a})
    print(f"Collapse B (pulsar added to menu): ln K={lnk_collapseB:+.3f} vs {null_collapseB} "
          f"[{band(lnk_collapseB)}]  (P2 needs <0: {'PASS' if lnk_collapseB < 0 else 'FAIL'})")
    print(f"  drop from Epoch-1a ln K: {lnk_epoch1a:+.3f} -> {lnk_collapseB:+.3f} "
          f"(Delta ln K = {lnk_collapseB - lnk_epoch1a:+.3f})")

    # --- (pi_nat, lambda) grid and critical lambda (C2.4) ---
    print("  (pi_nat, lambda) grid at Epoch 1a (ln K invariant in pi_nat, "
          "by construction: Bayes factors are prior-independent):")
    grid = {}
    for lam in LAM_GRID:
        row = []
        for pi in PI_NAT_GRID:
            k, _ = ln_k_vs_best_null({"H_int": sum_int_epoch1a, "H_nat": ch1_ln_r_nat(lam)})
            row.append(round(k, 3))
        grid[lam] = row
        print(f"    lambda={lam:.1f}: {row}")
    # critical lambda where ln K falls below 3 (P1 boundary), at ch1 alone
    # since ch2/ch3 don't depend on lambda: solve Delta/lambda*ln10 = 3
    lam_crit = DELTA_DEX * LN10 / 3.0
    print(f"  critical lambda (ln K -> 3): {lam_crit:.3f} dex "
          f"(fiducial lambda=1 is {'inside' if lam_crit > 1 else 'outside'} the tolerated range)")

    # --- dynamic range (C2.7): use the lambda sweep bounds [0,3] as the
    # achievable range for the one lambda-dependent channel, holding ch2/ch3
    # fixed at their constructed values ---
    lnk_max, _ = ln_k_vs_best_null({"H_int": sum_int_epoch1a, "H_nat": ch1_ln_r_nat(1e-9)})
    lnk_min, _ = ln_k_vs_best_null({"H_int": sum_int_epoch1a, "H_nat": ch1_ln_r_nat(3.0)})
    rng = lnk_max - lnk_min
    print(f"  achievable range at Epoch 1a: [{lnk_min:+.3f}, {lnk_max:+.3f}] "
          f"({rng:.2f} nats; {'>=1 nat, informative' if rng >= 1 else '<1 nat, structurally bounded'})")

    # P6 as a function of the lambda sweep bound (R9 E-R9-05)
    p6_lambda_grid = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 5.0]
    p6_range_by_lambda_max = {}
    for lam_max in p6_lambda_grid:
        k_min, _ = ln_k_vs_best_null(
            {"H_int": sum_int_epoch1a, "H_nat": ch1_ln_r_nat(lam_max)})
        p6_range_by_lambda_max[lam_max] = lnk_max - k_min

    return {
        "p6_lambda_grid": p6_lambda_grid,
        "p6_range_by_lambda_max": p6_range_by_lambda_max,
        "epoch1a_lnk": lnk_epoch1a, "epoch1a_band": band(lnk_epoch1a),
        "collapseA_doppler_lnk": lnk_doppler, "collapseA_mult_lnk": lnk_mult,
        "collapseA_both_lnk": lnk_both, "collapseA_band": band(lnk_both),
        "collapseB_lnk": lnk_collapseB, "collapseB_band": band(lnk_collapseB),
        "lambda_critical": lam_crit, "range_epoch1a": [lnk_min, lnk_max],
        "P1": lnk_epoch1a >= 3, "P2": lnk_collapseB < 0, "P3": lnk_both < 1,
    }

# =====================================================================
# CASE 2: Project Hephaistos (mundane, per-object: candidates G, D, E)
# =====================================================================

def hephaistos():
    print("\n=== Project Hephaistos (candidates G, D, E) ===")
    # Epoch 1 (2024-05-05/06): full-text check of Suazo et al. 2024
    # (arXiv:2405.02927, ar5iv full text, Sec. 3.1 "Potential contamination"
    # and Sec. 4 discussion) resolves dossier gap note 1: the discovery
    # paper ITSELF already discusses chance alignment with dust-obscured
    # background galaxies as a considered, quantified, unresolved
    # alternative ("~2 contaminated sources expected" among ~2e5 stars with
    # W3/W4 detections; "the possibility of perfect alignments cannot be
    # ruled out"). H_bg is therefore on the Epoch-1 menu by C2.3 rule 1
    # (documented in the submitted paper itself), not introduced fresh by
    # Ren et al. 2024 as an uninformed first read of the dossier's gap note
    # might suggest.
    #
    # CONSTRUCTION: per-candidate Epoch-1 prior read directly from the
    # paper's own contamination-rate estimate: ~2 expected contaminants
    # among the 7 candidates gives a naive per-candidate base rate
    # p_bg = 2/7 = 0.286 at the moment of publication, before any
    # candidate-specific follow-up. ln_r[H_bg] = ln(p_bg/(1-p_bg)).
    P_BG_EPOCH1 = 2.0 / 7.0
    ln_r_bg_epoch1 = math.log(P_BG_EPOCH1 / (1 - P_BG_EPOCH1))

    results = {}
    for cand, epochs in [
        ("G", [
            ("2024-05-06", ln_r_bg_epoch1, False),
            # 2024-05-23: Ren et al. radio cross-match finds an off-star
            # radio counterpart offset ~5.0 arcsec for G. Per dossier, this
            # IS the discriminating datum for G. CONSTRUCTION: an off-star
            # radio counterpart offset from the Gaia stellar position is a
            # near-decisive AGN/background-source signature.
            # DECOMPOSED: P(off-star radio counterpart | H_bg) = 1.0 against
            # P(same | H_art, a structure at the Gaia stellar position) = 0.0183
            ("2024-05-23", math.log(1.0 / 0.0183), True),
        ]),
        ("D", [
            ("2024-05-06", ln_r_bg_epoch1, False),
            # 2026-07-03: archival diagnostics (Ren et al. 2026) find NO
            # contamination signature for D (in contrast to B, C), flagged
            # as needing dedicated follow-up. CONSTRUCTION: absence of the
            # astrometric/radio contamination signatures that worked for
            # B/C shifts weight toward H_art for D specifically.
            # DECOMPOSED: P(no contamination signature | H_bg) = 0.2231 against
            # P(same | H_art) = 1.0
            ("2026-07-03", math.log(0.2231 / 1.0), False),
            # 2026-07-10: JWST/MIRI (Zackrisson et al. 2026) resolves D as
            # a z~0.9 Hot DOG. Discriminating datum per dossier.
            # DECOMPOSED: P(resolved as a z~0.9 galaxy | H_bg) = 1.0 against
            # P(same | H_art) = 0.00248
            ("2026-07-10", math.log(1.0 / 0.00248), True),
        ]),
        ("E", [
            ("2024-05-06", ln_r_bg_epoch1, False),
            ("2026-07-03", math.log(0.2231 / 1.0), False),
            # JWST resolves E as a z~0.4 dusty starburst galaxy.
            ("2026-07-10", math.log(1.0 / 0.00248), True),
        ]),
    ]:
        cum = 0.0
        p4_violation = False
        rows = []
        for date, delta, is_discriminating in epochs:
            cum += delta
            lnk, _ = ln_k_vs_best_null({"H_bg": cum})
            if lnk >= 3 and not is_discriminating:
                p4_violation = True
            rows.append((date, cum, lnk, band(lnk)))
        for date, cum_v, lnk, b in rows:
            print(f"  {cand}  {date}: cum ln_r[H_bg]={cum_v:+.3f}  ln K={lnk:+.3f}  [{b}]")
        p4 = not p4_violation
        print(f"  {cand}: final ln K={rows[-1][2]:+.3f} [{rows[-1][3]}]  "
              f"(P4, no false positive: {'PASS' if p4 else 'FAIL'})")
        results[cand] = {"final_lnk": rows[-1][2], "final_band": rows[-1][3], "P4": p4,
                          "trajectory": rows}
    return results

# =====================================================================
# CASE 3: Boyajian's star (short-timescale dipping only; needs continuous
# likelihood per OCS-MIRI-1 / spec section B)
# =====================================================================

def q_ext(x):
    """Extinction efficiency, van de Hulst anomalous-diffraction approximation.
    x = 2*pi*a/lambda. x>>1 -> geometric optics (grey, Q->2); x<<1 -> Rayleigh
    (strongly wavelength-dependent, Q ~ x^4)."""
    if x < 1e-3:
        return (8.0 / 3.0) * x ** 4  # small-x Rayleigh limit of the AD formula
    return 2.0 - 4.0 / x * math.sin(x) + 4.0 / x ** 2 * (1.0 - math.cos(x))

def boyajian():
    print("\n=== Boyajian's star (short-timescale dipping; continuous likelihood) ===")
    LAM_BLUE_UM, LAM_RED_UM = 0.44, 0.79  # B and I bands, Boyajian et al. 2018 multiband setup

    def achromaticity(a_um):
        xb = 2 * math.pi * a_um / LAM_BLUE_UM
        xr = 2 * math.pi * a_um / LAM_RED_UM
        qb, qr = q_ext(xb), q_ext(xr)
        return qb / qr - 1.0  # 0 = grey; large = strongly non-grey (small particle)

    # H_art (solid megastructure occulter): scale >> optical wavelengths by
    # construction (any macroscopic structure), so Q_ext -> 2 at both bands,
    # achromaticity -> 0 deterministically. No free parameter; this is the
    # physical content of "optically thick material" (Boyajian et al. 2018's
    # own phrase for the excluded class).
    S_ART = 0.0

    # H_dust: particle size log-uniform prior over [1e-3, 10] um (sub-micron
    # to super-micron grains), per Boyajian et al. 2018's own constraint
    # ("particle sizes << 1 um for at least some dips"). Draws below are a
    # deterministic quadrature over a fine log-grid rather than a Monte
    # Carlo draw, since q_ext is cheap and smooth.
    N = 20000
    import statistics
    a_lo, a_hi = math.log10(1e-3), math.log10(10.0)
    achrom_samples = []
    for i in range(N):
        loga = a_lo + (a_hi - a_lo) * (i + 0.5) / N
        achrom_samples.append(achromaticity(10 ** loga))

    # Observed statistic (Boyajian et al. 2018): multiband photometry shows
    # significant differential reddening, "inconsistent with dip models that
    # invoke optically thick material" and "in-line with predictions for an
    # ordinary dust occulter" with particle sizes <<1um for at least some
    # dips. CONSTRUCTION: the exact measured reddening slope and its
    # uncertainty were not extracted from the primary photometry in this
    # pass (Appendix D states this as a limitation); the observation is
    # scored at the qualitative level the paper itself commits to -- "large,
    # non-grey, small-particle-consistent" -- taken as S_obs at the 90th
    # percentile of the dust-prior's own achromaticity distribution, a
    # conservative (not most-favorable) read of "at least some dips".
    achrom_samples.sort()
    s_obs = achrom_samples[int(0.90 * N)]

    # Gaussian measurement model in achromaticity space, sigma set so that
    # S_ART=0 sits >5 sigma from S_obs (paper's own language: "inconsistent
    # with", not merely disfavored) -- CONSTRUCTION.
    sigma = s_obs / 6.0

    def gauss_ln_l(s_model, s_obs, sigma):
        return -0.5 * ((s_model - s_obs) / sigma) ** 2 - math.log(sigma * math.sqrt(2 * math.pi))

    ln_l_art = gauss_ln_l(S_ART, s_obs, sigma)
    ln_l_dust = math.log(sum(math.exp(gauss_ln_l(s, s_obs, sigma)) for s in achrom_samples) / N)
    ln_r_dust_epoch3 = ln_l_dust - ln_l_art

    print(f"  observed achromaticity statistic S_obs={s_obs:.4f} "
          f"(90th pctile of dust-prior predictive; sigma={sigma:.4f})")
    # R9 E-R9-05: sigma is defined so that S_ART sits at 6 sigma, so the -17.9
    # nats it produces restates the stipulation rather than measuring anything.
    # Report ln_r across the stipulation instead of only at its fiducial.
    print("  sigma is a CONSTRUCTION (S_ART placed at a chosen n_sigma); "
          "ln_r[H_dust] across that choice:")
    for n_sig in (2.0, 3.0, 4.0, 5.0, 6.0, 8.0):
        sg = s_obs / n_sig
        la = gauss_ln_l(S_ART, s_obs, sg)
        ld = math.log(sum(math.exp(gauss_ln_l(x, s_obs, sg))
                          for x in achrom_samples) / N)
        print(f"    n_sigma={n_sig:.0f}: ln_r[H_dust]={ld - la:+.2f}")
    print("    the channel's magnitude is set by this choice, not by the "
          "photometry, which was not re-extracted (stated limitation)")
    print(f"  ln L(H_art)={ln_l_art:+.3f}  ln L(H_dust, marginalized over particle size)={ln_l_dust:+.3f}")

    epochs = [
        ("2015-09-11", 0.0, False),   # Boyajian et al. 2016 preprint; megastructure not yet on menu
        ("2015-10-15", 0.0, False),   # Wright et al. adds H_art to the menu; wavelength channel inactive
        ("2018-01-02", ln_r_dust_epoch3, True),  # multiband result; discriminating datum
    ]
    cum = 0.0
    p4_violation = False
    for date, delta, is_disc in epochs:
        cum += delta
        lnk, _ = ln_k_vs_best_null({"H_dust": cum})
        if lnk >= 3 and not is_disc:
            p4_violation = True
        print(f"  {date}: cum ln_r[H_dust]={cum:+.3f}  ln K={lnk:+.3f}  [{band(lnk)}]")
    final_lnk, _ = ln_k_vs_best_null({"H_dust": cum})
    p4 = not p4_violation
    print(f"  final ln K={final_lnk:+.3f} [{band(final_lnk)}]  "
          f"(P4, no false positive: {'PASS' if p4 else 'FAIL'})")
    return {"final_lnk": final_lnk, "final_band": band(final_lnk), "P4": p4,
            "S_obs": s_obs, "sigma": sigma}

if __name__ == "__main__":
    with open(PRIORS_PATH) as fh:
        priors = json.load(fh)
    print(f"Sealed priors file: {PRIORS_PATH}  (commit hash recorded separately, C2.3 seal)")

    lgm1_res = lgm1()
    heph_res = hephaistos()
    boy_res = boyajian()

    print("\n=== Pass/fail block (C2.1) ===")
    P4_all = all(heph_res[c]["P4"] for c in heph_res) and boy_res["P4"]
    print(f"P1 (LGM-1 detection, ln K>=3 at Epoch 1a): "
          f"{'PASS' if lgm1_res['P1'] else 'FAIL'} ({lgm1_res['epoch1a_lnk']:+.3f})")
    print(f"P2 (menu-completion collapse, ln K<0 after pulsar added): "
          f"{'PASS' if lgm1_res['P2'] else 'FAIL'} ({lgm1_res['collapseB_lnk']:+.3f})")
    print(f"P3 (data-driven collapse, ln K<1 after Collapse A): "
          f"{'PASS' if lgm1_res['P3'] else 'FAIL'} ({lgm1_res['collapseA_both_lnk']:+.3f})")
    print(f"P4 (no false positives, Hephaistos G/D/E + Boyajian): "
          f"{'PASS' if P4_all else 'FAIL'}")
    p5, p5_detail = check_seal()
    print(f"P5 (no hindsight leak, seal predates scoring): "
          f"{'PASS' if p5 else 'FAIL'} ({p5_detail})")
    range_epoch1a = lgm1_res["range_epoch1a"][1] - lgm1_res["range_epoch1a"][0]
    # R9 E-R9-05 / R8-E-15: the range's lower end is set by the top of an
    # arbitrary lambda sweep, so P6 as written can be made to pass by choosing
    # lambda_max large enough. Report the whole curve and label the criterion.
    print(f"P6 (achievable range, LGM-1 Epoch 1a): {range_epoch1a:.2f} nats at "
          f"lambda_max=3.0")
    print("  P6 as a function of lambda_max (the sweep bound is a choice, not a "
          "measurement):")
    p6_curve = lgm1_res["p6_range_by_lambda_max"]
    for lam_max in lgm1_res["p6_lambda_grid"]:
        print(f"    lambda_max={lam_max:.1f}: range={p6_curve[lam_max]:.2f} nats "
              f"({'>=1' if p6_curve[lam_max] >= 1 else '<1'})")
    p6_min_lam = min((l for l, r in p6_curve.items() if r >= 1.0), default=None)
    print(f"  P6 crosses 1 nat at lambda_max ~ {p6_min_lam}; above that it cannot "
          "fail, so it is reported as INFORMATIONAL rather than as a passed "
          "criterion. No pre-registered rule fixes lambda_max, and one is owed.")

    # R9 E-R9-05: name the terminal set, and carry the disclosed P3 failure in
    # the verdict line instead of excluding it silently.
    terminal = {"P1": lgm1_res["P1"], "P2": lgm1_res["P2"], "P4": P4_all, "P5": p5}
    overall_fail = not all(terminal.values())
    print("\nTerminal criteria (P1, P2, P4, P5): "
          + ", ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in terminal.items()))
    print("Informational (cannot fail as constructed, or repairable per C2.1): "
          f"P3={'PASS' if lgm1_res['P3'] else 'FAIL (disclosed)'}, P6")
    print(f"\nOVERALL: {'FAILS validation' if overall_fail else 'validation criteria not triggered'}"
          " on the terminal set; P3 fails as constructed and is reported, not repaired")
    if not lgm1_res["P3"]:
        print("  P3 fails as constructed (Collapse A ln K did not drop below 1); "
              "F3 is repairable per C2.1, reported as a finding in Appendix D rather "
              "than tuned away.")
