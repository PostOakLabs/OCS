"""
Paper F, WU OCS-R7-CALC-F-1: the three confirmed referee majors, computed.

Nothing here changes any v0.3 number.  The posterior of record remains
fF_posterior_v3.py (seed 42); this script imports it as a library, rebuilds
its baseline nuisance draws EXACTLY (same seed, same draw order), and asserts
the reproduced anchors against the published values before computing anything
new -- the fF_expand_v1.py pattern.

  Part A  F-M2  P_excl recomputed under every sensitivity variant the paper
                already carries, each variant's limit compared against the
                natural-flow band drawn on THAT VARIANT'S OWN nuisances (the
                comparison the published table never makes).
                Riders: F-t4 (10x tighter radio leg), F-n4/F-P7 (seed spread).
  Part B  F-M1  duty-cycle exclusion boundaries under per-block sensitivity
                scatter around sigma_i = 1.1 uJy sqrt(177.19/t_i).
                Riders: F-n2 (block statistics regenerate from fF_epochs.json),
                F-n1 (period-grid quantization of the printed boundaries).
  Part C  F-M3  injection-recovery of the Gaussian-at-zero reconstruction
                against the survival-function likelihood a non-detection
                actually implies; coverage of the 95 per cent upper limit.

Outputs (written next to this script):
  fF_calcF1_exclbracket.json   Part A
  fF_calcF1_duty_band.json     Part B
  fF_calcF1_coverage.json      Part C

Run:  python3 fF_calcF1_v1.py
"""

import json
import os
import time

import numpy as np
from statistics import NormalDist
from scipy.special import log_ndtr

import fF_posterior_v3 as P
import fF_expand_v1 as X

HERE = os.path.dirname(os.path.abspath(__file__))

Msun, kpc, c, G, m_p = P.Msun, P.kpc, P.c, P.G, P.m_p

SEED_B = 20260823          # Part B sensitivity-scatter stream
SEED_C = 20260823          # Part C injection stream

# ---- pre-committed sizes (see board/notes/R7-CALC-F-1.md section 0) --------
B_N_REAL = 100             # sensitivity realizations per cell
B_N_TRIALS = 1500          # flare-phase trials per realization
C_N_INJ = 200              # injections per (eps_true, M) cell
C_N_MC = 4000              # nuisance draws per recovery
C_GRID = np.logspace(-14, -2, 61)
SEEDS_SPREAD = list(range(42, 50))

_T0 = time.time()


def log(msg):
    print("[%7.1fs] %s" % (time.time() - _T0, msg), flush=True)


# ===========================================================================
# reproduction gate
# ===========================================================================

def baseline_draws():
    P.rng = np.random.default_rng(42)
    return {f: P.draw_theta(P.N_MC, f) for f in P.FAMILIES}


def load_json(name):
    with open(os.path.join(HERE, name)) as fh:
        return json.load(fh)


def assert_reproduction(th_base, v3):
    """Regenerate the published RIAF anchors from the seed-42 stream."""
    got = P.eps95_curve(P.ANCHORS, "riaf", th_base["riaf"])
    for a, b in zip(got, v3["anchors_riaf"]):
        assert abs(a / b - 1.0) < 1e-9, (a, b)
    got_pe = P.excl_fraction(P.ANCHORS, got, th_base["riaf"])
    for a, b in zip(got_pe, v3["exclfrac_anchors"]["riaf"]):
        assert abs(a - b) < 1e-12, (a, b)
    return {"anchors_riaf": got, "exclfrac_riaf": got_pe}


# ===========================================================================
# PART A -- F-M2: the exclusion fraction under the sensitivity ladder
# ===========================================================================
# P_excl = P[eps_nat > eps_l] compares two quantities built from the SAME
# nuisance draws.  Table tab:sens recomputes only eps_l under each variant,
# and the published exclusion fractions all evaluate the natural-flow band on
# the BASELINE draws.  Under an n_e-prior change both objects move together,
# so the net effect on P_excl is not inferable from the published table.
# Every variant below recomputes both sides on its own draws.

SIGMA_STAR_CMS = 21.0e5     # km/s -> cm/s, the paper set's sigma fiducial


def mdot_bondi_paperE(M, th):
    """Paper E's turbulent-medium convention: lambda = 1, (sigma^2+c_s^2)^3/2.

    Appendix app:conventions prices the net ratio at ~1.9 (this paper's mdot
    is ~1.9x Paper E's at equal M, n_e).  Applied to the Bondi rate only;
    f_B's geometric definition (r_B = GM/c_s^2) keeps the paper's own
    convention, since that suppression factor is defined against the thermal
    Bondi radius in both papers.  The choice is stated rather than buried:
    carrying the turbulent velocity into r_B as well would move eps_nat
    further in the same direction.
    """
    rho = P.MU_E * m_p * th["n_e"]
    v_eff = np.sqrt(SIGMA_STAR_CMS ** 2 + th["c_s"] ** 2)
    return 4 * np.pi * 1.0 * (G * M) ** 2 * rho / v_eff ** 3


FAM_COLS = ("riaf", "jet", "riaf_noradio")


def variant_pexcl(th, mdot_fn=None, **kw):
    """eps_l and P_excl at the three anchors, both on the SAME draws `th`.

    `th` is keyed by the DRAWING family; riaf_noradio reuses the riaf draws
    evaluated under the disk family's (radio-free) likelihood, exactly as the
    posterior of record does.
    """
    old = P.mdot_bondi
    if mdot_fn is not None:
        P.mdot_bondi = mdot_fn
    try:
        out = {}
        for fam in FAM_COLS:
            draw_fam = "riaf" if fam == "riaf_noradio" else fam
            like_fam = "disk" if fam == "riaf_noradio" else fam
            e95 = P.eps95_curve(P.ANCHORS, like_fam, th[draw_fam], **kw)
            out[fam] = {"eps95": e95,
                        "P_excl": P.excl_fraction(P.ANCHORS, e95, th["riaf"])}
        return out
    finally:
        P.mdot_bondi = old


def part_a(th_base, v3):
    log("Part A: exclusion-fraction bracket")
    rows = {}

    def add(tag, desc, th, **kw):
        t0 = time.time()
        rows[tag] = {"variant": desc, **variant_pexcl(th, **kw)}
        log("  %-22s %.1fs  P_excl(riaf) = %s" %
            (tag, time.time() - t0,
             ["%.3f" % x for x in rows[tag]["riaf"]["P_excl"]]))

    add("baseline", "baseline (published)", th_base)

    # --- the Table tab:sens rows, each drawn on the published stream ---
    P.rng = np.random.default_rng(42)
    _ = {f: P.draw_theta(P.N_MC, f) for f in P.FAMILIES}     # base draws
    _dead = P.draw_theta(P.N_MC, "disk")                     # stream spacer
    del _dead
    th_wide = P.draw_theta(P.N_MC, "riaf", ne_width=1.5)
    th_low = P.draw_theta(P.N_MC, "riaf", ne_median=0.023)
    th_floor = P.draw_theta(P.N_MC, "riaf", ne_width=1.5, ne_floor=0.05)

    # the published variant anchors, regenerated: a second reproduction gate
    for th_v, key in ((th_wide, "anchors_riaf_wide"),
                      (th_low, "anchors_riaf_lowne"),
                      (th_floor, "anchors_riaf_floor")):
        got = P.eps95_curve(P.ANCHORS, "riaf", th_v)
        for a, b in zip(got, v3[key]):
            assert abs(a / b - 1.0) < 1e-9, (key, a, b)
    log("  variant reproduction gate: wide/lowne/floor anchors exact")

    def as_set(th_riaf):
        """Transport an n_e variant onto every family's draws.

        The riaf column uses the variant draws whole, which is what the
        published Table tab:sens rows used.  The jet and disk families differ
        from riaf only in their band-fraction ranges, so the variant is
        transported to them by swapping in the variant n_e column and leaving
        every other nuisance on the published stream.
        """
        out = {"riaf": th_riaf}
        for f in ("jet", "disk"):
            d = dict(th_base[f])
            d["n_e"] = th_riaf["n_e"]
            out[f] = d
        return out

    variant_sets = {"ne_wide": as_set(th_wide),
                    "ne_lowmed": as_set(th_low),
                    "ne_wide_floor": as_set(th_floor)}

    add("ne_wide", "n_e prior widened to 1.5 dex", variant_sets["ne_wide"])
    add("ne_lowmed", "n_e prior median / 10", variant_sets["ne_lowmed"])
    add("ne_wide_floor", "widened + wind floor n_e >= 0.05",
        variant_sets["ne_wide_floor"])
    add("eps_floor11", "eps-grid floor raised to 1e-11", th_base,
        eps_grid=np.logspace(-11, -2, 91))

    for name, z in P.XRAY_Z_VARIANTS.items():
        add("xz_" + name, "X-ray limit read as %s" % name, th_base,
            sig_fx=P.FX_LIM / z)

    add("ir_tightest", "IR: tightest single filter only", th_base,
        ir_mode="tightest")
    for cname in ("99.7%", "68%"):
        add("ir_" + cname.replace(".", "").replace("%", ""),
            "IR completeness row %s" % cname, th_base,
            ir_set=P.IR_SETS[cname])

    add("bondi_paperE", "Bondi denominator: Paper E turbulent convention",
        th_base, mdot_fn=mdot_bondi_paperE)

    add("radio_10x", "radio leg 10x tighter (F-t4 rider, SKA-era)", th_base,
        sig_radio=P.SIG_S_RADIO / 10.0)

    # --- cancellation accounting ---------------------------------------
    base_e95 = rows["baseline"]["riaf"]["eps95"]
    nat_base = [float(np.median(P.eps_nat_draws(M, th_base["riaf"])))
                for M in P.ANCHORS]
    cancel = {}
    for tag, r in rows.items():
        if tag == "baseline":
            continue
        th_v = variant_sets.get(tag, th_base)
        if tag == "bondi_paperE":
            old = P.mdot_bondi
            P.mdot_bondi = mdot_bondi_paperE
            nat_v = [float(np.median(P.eps_nat_draws(M, th_v["riaf"])))
                     for M in P.ANCHORS]
            P.mdot_bondi = old
        else:
            nat_v = [float(np.median(P.eps_nat_draws(M, th_v["riaf"])))
                     for M in P.ANCHORS]
        cancel[tag] = {
            "eps95_ratio_to_baseline":
                [a / b for a, b in zip(r["riaf"]["eps95"], base_e95)],
            "nat_median_ratio_to_baseline":
                [a / b for a, b in zip(nat_v, nat_base)],
            "P_excl_delta":
                [a - b for a, b in zip(r["riaf"]["P_excl"],
                                       rows["baseline"]["riaf"]["P_excl"])],
        }

    # --- F-n4 / F-P7 rider: seed-to-seed spread -------------------------
    log("  seed spread (%d seeds)" % len(SEEDS_SPREAD))
    spread = {"seeds": SEEDS_SPREAD, "eps95_riaf": [], "P_excl_riaf": []}
    for s in SEEDS_SPREAD:
        P.rng = np.random.default_rng(s)
        th_s = {f: P.draw_theta(P.N_MC, f) for f in P.FAMILIES}
        e = P.eps95_curve(P.ANCHORS, "riaf", th_s["riaf"])
        spread["eps95_riaf"].append(e)
        spread["P_excl_riaf"].append(
            P.excl_fraction(P.ANCHORS, e, th_s["riaf"]))
    a = np.array(spread["eps95_riaf"])
    p = np.array(spread["P_excl_riaf"])
    spread["eps95_mean"] = a.mean(0).tolist()
    spread["eps95_sd"] = a.std(0, ddof=1).tolist()
    spread["eps95_rel_sd"] = (a.std(0, ddof=1) / a.mean(0)).tolist()
    spread["eps95_min_max"] = [a.min(0).tolist(), a.max(0).tolist()]
    spread["P_excl_mean"] = p.mean(0).tolist()
    spread["P_excl_sd"] = p.std(0, ddof=1).tolist()
    spread["P_excl_min_max"] = [p.min(0).tolist(), p.max(0).tolist()]

    # --- the bracket ----------------------------------------------------
    keys_all = list(rows)
    keys_an = [t for t in rows if t != "radio_10x"]
    bracket = {}
    for fam in FAM_COLS:
        v_all = np.array([rows[t][fam]["P_excl"] for t in keys_all])
        v_an = np.array([rows[t][fam]["P_excl"] for t in keys_an])
        bracket[fam] = {
            "baseline": rows["baseline"][fam]["P_excl"],
            "min_analysis_only": v_an.min(0).tolist(),
            "max_analysis_only": v_an.max(0).tolist(),
            "argmin_analysis_only": [keys_an[i] for i in v_an.argmin(0)],
            "argmax_analysis_only": [keys_an[i] for i in v_an.argmax(0)],
            "min_incl_forecast": v_all.min(0).tolist(),
            "max_incl_forecast": v_all.max(0).tolist(),
        }

    return {"anchors_Msun": (P.ANCHORS / Msun).tolist(),
            "variants": rows, "cancellation": cancel,
            "seed_spread": spread, "bracket": bracket,
            "note": ("Every variant recomputes BOTH eps_l and the "
                     "natural-flow draws on its own nuisances. The published "
                     "P_excl values compare each limit against the baseline "
                     "band only.")}


# ===========================================================================
# PART B -- F-M1: per-block sensitivity scatter through the duty-cycle table
# ===========================================================================

AMPS = [10.0, 30.0, 100.0, 300.0, 1000.0]
DURS = [0.5, 2.0, 8.0, 24.0]
SCATTERS = [0.10, 0.11, 0.20, 0.30]     # dex; 0.11 dex ~ +-30 per cent rms


def duty_grid(sig_i, start, dur, sigma_comb, rng, n_trials, periods):
    """T_excluded_below for every (amplitude, duration) cell.

    Identical detection rule to fF_expand_v1.f4_duty: a flare train of period
    T_rec and duration tau laid over the real block timeline at a uniform
    random phase, detected either by a single block's tau-averaged flux
    exceeding that block's own 5-sigma point or by the whole-campaign mean
    exceeding the combined 5-sigma point.
    """
    tot = dur.sum()

    def detect_prob(S, tau, T_rec):
        phase = rng.uniform(0.0, T_rec, n_trials)
        det = np.zeros(n_trials, dtype=bool)
        on_tot = np.zeros(n_trials)
        for t0, dt, s in zip(start, dur, sig_i):
            k0 = np.floor((t0 - phase) / T_rec)
            on = np.zeros(n_trials)
            for kk in (k0, k0 + 1, k0 + 2):
                fs = phase + kk * T_rec
                on += np.clip(np.minimum(fs + tau, t0 + dt)
                              - np.maximum(fs, t0), 0.0, None)
            on = np.minimum(on, dt)
            on_tot += on
            det |= (S * on / dt) > (5.0 * s)
        det |= (S * on_tot / tot) > (5.0 * sigma_comb)
        return float(np.mean(det))

    out = {}
    for S in AMPS:
        for tau in DURS:
            probs = np.array([detect_prob(S, tau, T) for T in periods])
            ok = np.where(probs >= 0.95)[0]
            out[(S, tau)] = float(periods[ok[-1]]) if len(ok) else None
    return out


def part_b(ep, published):
    log("Part B: duty-table sensitivity band")
    sigma_comb = 1.1
    T_tot = ep["total_hours_table"]
    blocks = X.block_times(ep)
    dur = np.array([b[1] for b in blocks])
    start = np.array([b[0] for b in blocks])
    sig_i = sigma_comb * np.sqrt(T_tot / dur)
    periods = np.logspace(np.log10(6.0), np.log10(2.0e5), 45)
    periods_fine = np.logspace(np.log10(6.0), np.log10(2.0e5), 177)

    # ---- F-n2 rider: block statistics regenerate from fF_epochs.json ---
    n2 = {
        "n_blocks": len(blocks),
        "total_hours": float(T_tot),
        "median_block_hours": float(np.median(dur)),
        "min_block_hours": float(dur.min()),
        "max_block_hours": float(dur.max()),
        "sigma_range_uJy": [float(sig_i.min()), float(sig_i.max())],
        "median_sigma_uJy": float(np.median(sig_i)),
        "median_5sigma_uJy": float(5 * np.median(sig_i)),
        "span_years": float((start[-1] + dur[-1]) / 24.0 / 365.25),
        "by_project": ep["by_project"],
        "source": "regenerated in this script from figs/fF_epochs.json",
    }
    n2["checks"] = {
        "printed_rms_range_4.5_to_12.0":
            bool(abs(sig_i.min() - 4.5) < 0.05
                 and abs(sig_i.max() - 12.0) < 0.05),
        "printed_median_rms_5.3": bool(abs(np.median(sig_i) - 5.3) < 0.05),
        "printed_median_onsource_7.6": bool(abs(np.median(dur) - 7.6) < 0.05),
        "printed_median_5sigma_26.5":
            bool(abs(5 * np.median(sig_i) - 26.5) < 0.3),
    }
    log("  F-n2 block-stat regeneration: %s" % n2["checks"])

    # ---- reproduction gate: zero scatter, published trial count --------
    rng = np.random.default_rng(X.SEED_F4)
    repro = duty_grid(sig_i, start, dur, sigma_comb, rng, X.N_TRIALS, periods)
    pub = {(g["amp_uJy"], g["dur_hr"]): g["T_excluded_below_hr"]
           for g in published["grid"]}
    for k, v in repro.items():
        assert (v is None) == (pub[k] is None), (k, v, pub[k])
        if v is not None:
            assert abs(v / pub[k] - 1.0) < 1e-12, (k, v, pub[k])
    log("  duty-grid reproduction gate: 20/20 cells exact")

    # ---- F-n1 rider: period-grid quantization --------------------------
    rng = np.random.default_rng(X.SEED_F4)
    fine = duty_grid(sig_i, start, dur, sigma_comb, rng, X.N_TRIALS,
                     periods_fine)
    quant = {}
    step45 = float(periods[1] / periods[0])
    stepfine = float(periods_fine[1] / periods_fine[0])
    for k in repro:
        quant["%g/%g" % k] = {
            "published_45pt_grid": pub[k],
            "refined_177pt_grid": fine[k],
            "ratio_fine_over_published": (fine[k] / pub[k]
                                          if fine[k] and pub[k] else None),
            "implied_duty_published": (k[1] / pub[k] if pub[k] else None),
            "implied_duty_refined": (k[1] / fine[k] if fine[k] else None),
        }
    quant["_grid_steps"] = {"published_step_ratio": step45,
                            "refined_step_ratio": stepfine}
    log("  F-n1 grid-quantization pass: published step ratio %.3f" % step45)

    # ---- MC-noise floor from the reduced trial count -------------------
    rng = np.random.default_rng(SEED_B)
    noise = [duty_grid(sig_i, start, dur, sigma_comb, rng, B_N_TRIALS,
                       periods) for _ in range(20)]
    trial_noise = {}
    for k in repro:
        vs = [d[k] for d in noise if d[k] is not None]
        trial_noise["%g/%g" % k] = {
            "published": pub[k],
            "reduced_trials_median": float(np.median(vs)) if vs else None,
            "reduced_trials_min_max": ([float(np.min(vs)), float(np.max(vs))]
                                       if vs else None),
            "n_unbounded": sum(1 for d in noise if d[k] is None),
        }
    log("  trial-count noise floor done (20 reruns at n_trials=%d)"
        % B_N_TRIALS)

    # ---- the sensitivity band ------------------------------------------
    bands = {}
    for sdex in SCATTERS:
        t0 = time.time()
        rng = np.random.default_rng(SEED_B + int(sdex * 1000))
        draws = []
        for _ in range(B_N_REAL):
            # Log-normal multiplicative scatter about the stated scaling,
            # renormalized so the campaign-combined sensitivity is preserved:
            # the combined image rms (1.1 uJy) is a MEASURED number, so a
            # per-block redistribution must not change it.  Without the
            # renormalization the draw would also move the campaign depth,
            # which is not the assumption under test.
            fac = 10 ** rng.normal(0.0, sdex, len(sig_i))
            w_new = (1.0 / (sig_i * fac) ** 2).sum()
            w_old = (1.0 / sig_i ** 2).sum()
            renorm = np.sqrt(w_new / w_old)
            draws.append(duty_grid(sig_i * fac * renorm, start, dur,
                                   sigma_comb, rng, B_N_TRIALS, periods))
        row = {}
        for k in repro:
            vs = [d[k] for d in draws if d[k] is not None]
            row["%g/%g" % k] = {
                "published": pub[k],
                "median": float(np.median(vs)) if vs else None,
                "p5_p95": ([float(np.percentile(vs, 5)),
                            float(np.percentile(vs, 95))] if vs else None),
                "min_max": ([float(np.min(vs)), float(np.max(vs))]
                            if vs else None),
                "n_unbounded": sum(1 for d in draws if d[k] is None),
                "n": len(vs),
                "frac_within_one_grid_step":
                    (float(np.mean([abs(np.log(v / pub[k]))
                                    <= np.log(step45) for v in vs]))
                     if vs and pub[k] else None),
            }
        bands["%.2fdex" % sdex] = row
        log("  scatter %.2f dex done (%.0fs)" % (sdex, time.time() - t0))

    return {"block_stats_F_n2": n2, "grid_quantization_F_n1": quant,
            "trial_noise": trial_noise, "bands": bands,
            "scatters_dex": SCATTERS, "n_realizations": B_N_REAL,
            "n_trials": B_N_TRIALS, "seed": SEED_B,
            "renormalization_note": (
                "Per-block sensitivity scatter is applied at FIXED combined "
                "campaign sensitivity: the 1.1 uJy combined-image rms is a "
                "measured quantity, so redistributing sensitivity between "
                "blocks preserves the inverse-variance sum.")}


# ===========================================================================
# PART C -- F-M3: is the Gaussian-at-zero reconstruction faithful?
# ===========================================================================
# A non-detection reported as "flux < f_lim at confidence C" is a survival
# statement, P(observed < f_lim | predicted).  The paper instead evaluates a
# Gaussian centred at zero with sigma = f_lim / z(C).  The two agree in the
# deep-prediction limit and differ by O(1) near the limit.  Part C compares
# the two likelihoods on the real data and then measures the coverage of the
# 95 per cent upper limit under each on identical simulated data.

Z95 = NormalDist().inv_cdf(0.95)


def _pred(eps, M, th, d_ref_ir=None):
    """Predicted (flux_X, nuLnu_IR, S_radio) for one (eps, M) over draws."""
    if d_ref_ir is None:
        d_ref_ir = P.D_REF_IR_CHEN
    mdot = P.mdot_bondi(M, th)
    Lbol = eps * mdot * c ** 2
    fX = th["f_X"] * Lbol / (4 * np.pi * th["d"] ** 2)
    LIR = th["f_IR"] * Lbol * (d_ref_ir / th["d"]) ** 2
    LX_210 = th["f_X"] * Lbol * P.K_2TO10
    with np.errstate(divide="ignore"):
        logLR = (P.FP_A * np.log10(np.maximum(LX_210, 1e-30))
                 + P.FP_B * np.log10(M / Msun) + P.FP_C + th["fp"])
    S = 10 ** logLR / (4 * np.pi * th["d"] ** 2 * 5.0e9)
    return fX, LIR, S


def log_like_survival(eps, M, th, family, obs=None):
    """Censored ('survival') likelihood: P(observed < limit | predicted).

    The limit on each leg is the published bound and sigma is the same sigma
    the Gaussian-at-zero convention uses, so the ONLY difference between the
    two likelihoods is the shape, not the assumed noise level.
    """
    use_radio = P.FAMILIES[family][4]
    ir_set = P.IR_SETS[P.IR_COMPLETENESS_PRIMARY]
    fX, LIR, S = _pred(eps, M, th)
    lim_fx = P.FX_LIM if obs is None else obs["fx"]
    ll = log_ndtr((lim_fx - fX) / P.SIG_FX)
    for f in ir_set:
        lim_ir = f["L_lim"] if obs is None else obs["ir"][f["filter"]]
        ll = ll + log_ndtr((lim_ir - LIR) / f["sigma"])
    if use_radio:
        lim_S = 5.0 * P.SIG_S_RADIO if obs is None else obs["radio"]
        ll = ll + log_ndtr((lim_S - S) / P.SIG_S_RADIO)
    return ll


def log_like_gauss(eps, M, th, family, obs=None, **kw):
    """The paper's convention, optionally centred on realized data."""
    if obs is None:
        return P.log_like(eps, M, th, family, **kw)
    ir_set = P.IR_SETS[P.IR_COMPLETENESS_PRIMARY]
    use_radio = P.FAMILIES[family][4]
    fX, LIR, S = _pred(eps, M, th)
    ll = -0.5 * ((fX - obs["fx_meas"]) / P.SIG_FX) ** 2
    for f in ir_set:
        ll = ll + -0.5 * ((LIR - obs["ir_meas"][f["filter"]])
                          / f["sigma"]) ** 2
    if use_radio:
        ll = ll + -0.5 * ((S - obs["radio_meas"]) / P.SIG_S_RADIO) ** 2
    return ll


def eps95_from(llfn, masses, family, th, grid, **kw):
    out = []
    for M in masses:
        post = np.empty(len(grid))
        for i, e in enumerate(grid):
            ll = llfn(e, M, th, family, **kw)
            m = ll.max()
            post[i] = np.exp(m) * np.mean(np.exp(ll - m))
        post /= post.sum()
        out.append(float(np.interp(0.95, np.cumsum(post), grid)))
    return out


def part_c(th_base, v3):
    log("Part C: reconstruction faithfulness + coverage")

    # ---- C1: the two likelihoods on the real data ----------------------
    c1 = {}
    for fam in ("riaf", "jet", "disk"):
        g = P.eps95_curve(P.ANCHORS, fam, th_base[fam])
        s = eps95_from(log_like_survival, P.ANCHORS, fam, th_base[fam],
                       P.EPS_GRID)
        c1[fam] = {"eps95_gaussian_at_zero": g, "eps95_survival": s,
                   "ratio_survival_over_gauss": [b / a for a, b in zip(g, s)]}
        log("  C1 %-5s survival/gauss = %s"
            % (fam,
               ["%.3f" % r for r in c1[fam]["ratio_survival_over_gauss"]]))
    s_nr = eps95_from(log_like_survival, P.ANCHORS, "disk", th_base["riaf"],
                      P.EPS_GRID)
    c1["riaf_noradio"] = {
        "eps95_gaussian_at_zero": v3["anchors_riaf_noradio"],
        "eps95_survival": s_nr,
        "ratio_survival_over_gauss":
            [b / a for a, b in zip(v3["anchors_riaf_noradio"], s_nr)]}
    c1["P_excl_survival"] = {
        fam: P.excl_fraction(P.ANCHORS, c1[fam]["eps95_survival"],
                             th_base["riaf"])
        for fam in ("riaf", "jet", "riaf_noradio")}
    c1["P_excl_gaussian"] = v3["exclfrac_anchors"]

    # ---- C2: injection-recovery coverage -------------------------------
    rng = np.random.default_rng(SEED_C)
    fam = "riaf"
    ir_set = P.IR_SETS[P.IR_COMPLETENESS_PRIMARY]
    anchor_e95 = {8200.0: v3["anchors_riaf"][1],
                  40000.0: v3["anchors_riaf"][2]}
    cells = []
    for m_msun in (8200.0, 40000.0):
        for mult in (0.01, 0.1, 0.3, 1.0, 3.0):
            cells.append((m_msun * Msun, anchor_e95[m_msun] * mult, mult))

    cov = []
    for (M, eps_true, mult) in cells:
        t0 = time.time()
        n_cov_g = n_cov_s = n_det = 0
        rat = []
        for j in range(C_N_INJ):
            P.rng = np.random.default_rng(SEED_C + 7919 * j)
            th_true = P.draw_theta(1, fam)
            fX_t, LIR_t, S_t = _pred(eps_true, M, th_true)
            obs = {
                "fx_meas": float(fX_t[0] + rng.normal(0, P.SIG_FX)),
                "ir_meas": {f["filter"]:
                            float(LIR_t[0] + rng.normal(0, f["sigma"]))
                            for f in ir_set},
                "radio_meas": float(S_t[0] + rng.normal(0, P.SIG_S_RADIO)),
            }
            n_det += int(obs["radio_meas"] > 5 * P.SIG_S_RADIO
                         or obs["fx_meas"] > P.FX_LIM)
            obs["fx"] = P.FX_LIM
            obs["ir"] = {f["filter"]: f["L_lim"] for f in ir_set}
            obs["radio"] = 5.0 * P.SIG_S_RADIO
            P.rng = np.random.default_rng(4242 + j)
            th_r = P.draw_theta(C_N_MC, fam)
            g = eps95_from(log_like_gauss, [M], fam, th_r, C_GRID, obs=obs)[0]
            s = eps95_from(log_like_survival, [M], fam, th_r, C_GRID,
                           obs=obs)[0]
            n_cov_g += int(g >= eps_true)
            n_cov_s += int(s >= eps_true)
            rat.append(s / g)
        cov.append({
            "M_Msun": M / Msun, "eps_true": eps_true,
            "eps_true_over_published_eps95": mult, "n": C_N_INJ,
            "coverage_gaussian_at_zero": n_cov_g / C_N_INJ,
            "coverage_survival": n_cov_s / C_N_INJ,
            "detection_rate": n_det / C_N_INJ,
            "median_ratio_survival_over_gauss": float(np.median(rat)),
        })
        log("  C2 M=%6.0f x%.2f: cov G=%.3f S=%.3f det=%.2f ratio=%.3f (%.0fs)"
            % (M / Msun, mult, cov[-1]["coverage_gaussian_at_zero"],
               cov[-1]["coverage_survival"], cov[-1]["detection_rate"],
               cov[-1]["median_ratio_survival_over_gauss"],
               time.time() - t0))

    return {"C1_real_data": c1, "C2_coverage": cov,
            "n_injections_per_cell": C_N_INJ, "N_MC_recovery": C_N_MC,
            "eps_grid_points": len(C_GRID), "seed": SEED_C,
            "coverage_note": (
                "Coverage is the frequentist coverage of a Bayesian 95 per "
                "cent upper limit under the model's own prior; it is not "
                "required to equal 0.95 cell by cell. The diagnostic quantity "
                "is the DIFFERENCE between the two conventions on identical "
                "simulated data.")}


# ===========================================================================

if __name__ == "__main__":
    v3 = load_json("fF_v3_results.json")
    duty_pub = load_json("fF_expand_duty.json")
    ep = load_json("fF_epochs.json")

    th_base = baseline_draws()
    assert_reproduction(th_base, v3)
    log("reproduction gate passed: anchors + exclusion fractions exact")

    a = part_a(th_base, v3)
    with open(os.path.join(HERE, "fF_calcF1_exclbracket.json"), "w") as fh:
        json.dump(a, fh, indent=1)

    b = part_b(ep, duty_pub)
    with open(os.path.join(HERE, "fF_calcF1_duty_band.json"), "w") as fh:
        json.dump(b, fh, indent=1)

    th_base = baseline_draws()          # restore the seed-42 stream
    cc = part_c(th_base, v3)
    with open(os.path.join(HERE, "fF_calcF1_coverage.json"), "w") as fh:
        json.dump(cc, fh, indent=1)

    log("done")
