"""
Paper F v1.2 expansion analyses (WU OCS-F-EXPAND-1, referee items F-1..F-5).

Nothing here changes any v0.3 number.  The posterior of record remains
fF_posterior_v3.py (seed 42); this script imports it as a library, rebuilds
its baseline nuisance draws EXACTLY (same seed, same draw order) and asserts
the reproduced RIAF anchors against the published values before computing
anything new.  Everything below is either a re-run of that same posterior
with one nuisance frozen (F-1), a re-expression of draws already made (F-2),
a read of an existing output (F-3), or a new fixed-seed calculation on a
frozen input file (F-4, F-5).

Outputs (all written next to this script):
  fF_expand_nuisance.json    F-1  per-nuisance freeze / isolate ladder
  fF_expand_sed.json         F-2  per-band predicted nuLnu vs published limits
  fF_expand_sed.png          F-2  the figure
  fF_expand_exclcurve.json   F-3  continuous exclusion curve (pgfplots coords)
  fF_expand_duty.json        F-4  epoch-resolved radio flare exclusion
  fF_expand_dm.json          F-5  pulsar dispersion-measure requirement table

Run:  python3 fF_expand_v1.py
"""

import json
import os

import numpy as np

import fF_posterior_v3 as P

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_F4 = 20260820          # F-4 flare Monte Carlo (independent stream)
N_TRIALS = 4000             # realizations per (amplitude, duration, period)

Msun, kpc, c = P.Msun, P.kpc, P.c

# ---------------------------------------------------------------------------
# baseline draws, reproduced bit for bit from the posterior of record
# ---------------------------------------------------------------------------


def baseline_draws():
    """Re-run the first draws of run_all() in the same order, same seed."""
    P.rng = np.random.default_rng(42)
    return {f: P.draw_theta(P.N_MC, f) for f in P.FAMILIES}


def load_v3():
    with open(os.path.join(HERE, "fF_v3_results.json")) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# F-1  nuisance ladder
# ---------------------------------------------------------------------------
# Fiducial values are the central value of each prior in Table 2 of the paper:
# the log-normal median for n_e, the midpoint for the two uniforms, the mean
# for the two normals, and the geometric midpoint for the log-uniform band
# fractions.  Freezing a parameter there removes its spread without moving the
# centre of the prediction.

FIDUCIAL_LABEL = {
    "n_e": r"$n_{e}$ (gas density)",
    "c_s": r"$c_{s}$ (sound speed)",
    "d": r"$d$ (distance)",
    "f_X": r"$f_{X}$ (X-ray band fraction)",
    "f_IR": r"$f_{\mathrm{IR}}$ (IR band fraction)",
    "fp": r"$\delta_{\mathrm{FP}}$ (plane scatter)",
    "s": r"$s$ (inflow suppression)",
}


def fiducials(family):
    fx_lo, fx_hi, fir_lo, fir_hi, _ = P.FAMILIES[family]
    return {
        "n_e": 0.23,
        "c_s": 0.5 * (11.7e5 + 16.6e5),
        "d": 5.43 * kpc,
        "f_X": float(np.sqrt(fx_lo * fx_hi)),
        "f_IR": float(np.sqrt(fir_lo * fir_hi)),
        "fp": 0.0,
        "s": 0.4,
    }


def freeze(th, family, keys):
    """Copy of th with every key in `keys` set to its fiducial constant."""
    fid = fiducials(family)
    out = dict(th)
    n = len(th["n_e"])
    for k in keys:
        out[k] = np.full(n, fid[k])
    return out


def f1_nuisance(th_base, v3):
    fam = "riaf"
    th = th_base[fam]
    anchors = P.ANCHORS
    base = P.eps95_curve(anchors, fam, th)
    published = v3["anchors_riaf"]
    for a, b in zip(base, published):
        assert abs(a / b - 1.0) < 1e-9, (a, b)   # draw stream reproduced

    keys = list(FIDUCIAL_LABEL)
    rows = []
    for k in keys:
        frozen = P.eps95_curve(anchors, fam, freeze(th, fam, [k]))
        isolated = P.eps95_curve(
            anchors, fam, freeze(th, fam, [j for j in keys if j != k]))
        rows.append({
            "param": k,
            "label": FIDUCIAL_LABEL[k],
            "eps95_frozen": frozen,
            "eps95_isolated": isolated,
            # ratio < 1 means freezing this nuisance TIGHTENS the limit, i.e.
            # its spread was inflating eps95 by that factor
            "ratio_frozen_over_base": [f / b for f, b in zip(frozen, base)],
            "ratio_isolated_over_allfrozen": None,   # filled below
        })
    all_frozen = P.eps95_curve(anchors, fam, freeze(th, fam, keys))
    for r in rows:
        r["ratio_isolated_over_allfrozen"] = [
            i / a for i, a in zip(r["eps95_isolated"], all_frozen)]
    return {
        "family": fam,
        "anchors_Msun": (anchors / Msun).tolist(),
        "eps95_baseline": base,
        "eps95_all_frozen": all_frozen,
        "fiducials": {k: float(v) for k, v in fiducials(fam).items()},
        "rows": rows,
        "method": (
            "Each row re-runs the posterior of record with one nuisance held "
            "at its prior's central value ('frozen', all six others drawn) "
            "and, separately, with only that nuisance drawn and the other six "
            "held ('isolated'). The frozen ratio is eps95(frozen)/eps95"
            "(baseline); the isolated ratio is eps95(isolated)/eps95(all "
            "seven frozen). Neither is a variance decomposition: eps95 is a "
            "posterior quantile, not a sum of independent terms, and the "
            "ratios do not multiply to one."),
    }


# ---------------------------------------------------------------------------
# F-2  band-by-band adjudication
# ---------------------------------------------------------------------------
# Every quantity here is nu*L_nu in erg/s at the drawn distance, so the three
# instruments sit on one axis.  Predictions are evaluated at each family's own
# eps95: by construction the binding band is the one whose prediction reaches
# its published limit there, and the non-binding bands sit below theirs.

NU_RADIO = 7.25e9
NU_XRAY = 4.52e17           # geometric-mean photon energy of 0.5-7 keV, 1.87 keV
IR_NU = {"F200W": 2.998e14 / 2.00, "F444W": 2.998e14 / 4.44,
         "F770W": 2.998e14 / 7.70, "F1500W": 2.998e14 / 15.00}


def band_predictions(eps, M, th, family):
    """Per-draw nu*L_nu (erg/s) in each observed band at one (eps, M)."""
    mdot = P.mdot_bondi(M, th)
    Lbol = eps * mdot * c ** 2
    out = {}
    out["xray"] = th["f_X"] * Lbol
    out["ir"] = th["f_IR"] * Lbol * (P.D_REF_IR_CHEN / th["d"]) ** 2
    if P.FAMILIES[family][4]:
        LX_210 = th["f_X"] * Lbol * P.K_2TO10
        with np.errstate(divide="ignore"):
            logLR = (P.FP_A * np.log10(np.maximum(LX_210, 1e-30))
                     + P.FP_B * np.log10(M / Msun) + P.FP_C + th["fp"])
        S_pred = 10 ** logLR / (4 * np.pi * th["d"] ** 2 * 5.0e9)
        out["radio"] = S_pred * 4 * np.pi * th["d"] ** 2 * NU_RADIO
    return out


def f2_sed(th_base, v3):
    d0 = 5.43 * kpc
    ir_rows = P.IR_SETS[P.IR_COMPLETENESS_PRIMARY]
    limits = {
        "radio": {"nu": NU_RADIO,
                  "nuLnu": 5.5e-29 * 4 * np.pi * (5.43 * kpc) ** 2 * NU_RADIO,
                  "label": r"ATCA $5\sigma$ (7.25 GHz)"},
        "xray": {"nu": NU_XRAY, "nuLnu": 1.6e30,
                 "label": r"Chandra 95\% (0.5--7 keV)"},
    }
    for r in ir_rows:
        limits[r["filter"]] = {"nu": IR_NU[r["filter"]],
                               "nuLnu": r["L_lim"], "label": r["filter"]}

    anchors = {"8200": 8.2e3 * Msun, "40000": 4.0e4 * Msun}
    fams = {}
    for fam in ("riaf", "jet", "disk"):
        th = th_base[fam]
        eps_anch = P.eps95_curve(np.array(list(anchors.values())), fam, th)
        per_anchor = {}
        for (name, M), e in zip(anchors.items(), eps_anch):
            pred = band_predictions(e, M, th, fam)
            bands = {}
            for key, vals in pred.items():
                pc = [float(np.percentile(vals, p)) for p in (5, 50, 95)]
                if key == "ir":
                    for r in ir_rows:
                        bands[r["filter"]] = {"nu": IR_NU[r["filter"]],
                                              "p05": pc[0], "p50": pc[1],
                                              "p95": pc[2],
                                              "limit": r["L_lim"]}
                else:
                    bands[key] = {"nu": limits[key]["nu"], "p05": pc[0],
                                  "p50": pc[1], "p95": pc[2],
                                  "limit": limits[key]["nuLnu"]}
            binding = max(bands, key=lambda b: bands[b]["p50"] /
                          bands[b]["limit"])
            per_anchor[name] = {"eps95": e, "bands": bands,
                                "binding_band": binding,
                                "binding_ratio": (bands[binding]["p50"] /
                                                  bands[binding]["limit"])}
        fams[fam] = per_anchor
    return {"limits": limits, "families": fams, "d_assumed_kpc": d0 / kpc,
            "note": ("Predicted nu*L_nu percentiles over the 40,000 baseline "
                     "nuisance draws, evaluated at each family's own eps95 at "
                     "that anchor. The radio limit is plotted at 5 sigma "
                     "(5.5 uJy) for visual comparability with the X-ray and "
                     "infrared limits, which are published as bounds rather "
                     "than as rms; the likelihood itself uses the 1.1 uJy "
                     "rms as a Gaussian sigma and is unchanged.")}


def f2_figure(sed):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = ["radio", "F1500W", "F770W", "F444W", "F200W", "xray"]
    ticks = ["7.25 GHz\nATCA", "F1500W", "F770W", "F444W", "F200W",
             "0.5-7 keV\nChandra"]
    colors = {"riaf": "#1f4e9c", "jet": "#0f7a70", "disk": "#7a2f9c"}
    names = {"riaf": "RIAF", "jet": "jet-dominated", "disk": "thin disk"}
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.6), sharey=True)
    for ax, anchor, title in zip(
            axes, ("8200", "40000"),
            (r"$M = 8{,}200\ M_\odot$", r"$M = 4\times10^{4}\ M_\odot$")):
        for j, fam in enumerate(("riaf", "jet", "disk")):
            per = sed["families"][fam][anchor]["bands"]
            xs, lo, mid, hi = [], [], [], []
            for i, b in enumerate(order):
                if b not in per:
                    continue
                xs.append(i + 0.20 * (j - 1))
                lo.append(per[b]["p05"])
                mid.append(per[b]["p50"])
                hi.append(per[b]["p95"])
            ax.errorbar(xs, mid,
                        yerr=[np.array(mid) - np.array(lo),
                              np.array(hi) - np.array(mid)],
                        fmt="o", ms=4.5, lw=1.3, capsize=3,
                        color=colors[fam],
                        label=names[fam] if ax is axes[0] else None)
        for i, b in enumerate(order):
            lim = sed["limits"][b]["nuLnu"]
            ax.plot([i - 0.42, i + 0.42], [lim, lim], color="k", lw=2.2,
                    zorder=5)
            ax.plot([i], [lim], marker="v", color="k", ms=7, zorder=5)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels(ticks, fontsize=8)
        ax.set_yscale("log")
        ax.set_xlim(-0.6, len(order) - 0.4)
        ax.set_ylim(1e25, 1e32)
        ax.set_title(title, fontsize=11)
        ax.grid(axis="y", alpha=0.18)
    axes[0].set_ylabel(r"$\nu L_\nu$ (erg s$^{-1}$)")
    axes[0].legend(loc="upper left", fontsize=9, frameon=False)
    axes[0].text(0.02, 0.03, "black bars: published limits",
                 transform=axes[0].transAxes, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fF_expand_sed.png"), dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# F-3  continuous exclusion curve (no new compute; re-export of v0.3 output)
# ---------------------------------------------------------------------------


def f3_exclcurve(v3):
    M = v3["M"]
    out = {"M": M, "curves": {}}
    for k in ("riaf", "jet", "riaf_noradio"):
        out["curves"][k] = v3["exclfrac_curve"][k]
        out["pgf_" + k] = " ".join(
            "(%g,%.4f)" % (m, f)
            for m, f in zip(M, v3["exclfrac_curve"][k]))
    out["anchors"] = {"M": v3["anchors_M"],
                      "excl": v3["exclfrac_anchors"]}
    # crossing masses: where each curve first reaches 50 and 90 per cent
    for k in ("riaf", "jet", "riaf_noradio"):
        f = np.array(v3["exclfrac_curve"][k])
        cross = {}
        for lvl in (0.5, 0.9):
            idx = np.where(f >= lvl)[0]
            cross["M%d" % int(lvl * 100)] = (
                float(np.interp(lvl, f[:idx[0] + 1], M[:idx[0] + 1]))
                if len(idx) else None)
        out.setdefault("crossings", {})[k] = cross
    out["banares_cap_Msun"] = 6.0e3
    out["source"] = "fF_v3_results.json exclfrac_curve (no recomputation)"
    return out


# ---------------------------------------------------------------------------
# F-4  epoch-resolved duty cycle
# ---------------------------------------------------------------------------
# Per-block point-source sensitivity is scaled from the combined image:
# sigma_i = sigma_comb * sqrt(T_total / t_i).  This assumes the on-source hour
# is equally sensitive in every block, which the source paper does not state
# per block (its three projects observe at 5.5 and 9.0 GHz with different
# array configurations).  It is the only scaling available from the published
# table and is flagged as such in the manuscript.


def block_times(ep):
    """(t_start_hours_since_first_block, duration_hours) per block."""
    import datetime as _dt
    rows = sorted(ep["blocks"], key=lambda r: (r["date"], r["start_utc"]))
    t0 = None
    out = []
    for r in rows:
        h, m = (int(x) for x in r["start_utc"].split(":"))
        d = _dt.datetime.strptime(r["date"], "%Y-%m-%d").replace(hour=h,
                                                                 minute=m)
        if t0 is None:
            t0 = d
        out.append(((d - t0).total_seconds() / 3600.0, r["hours"],
                    r["project"], r["date"]))
    return out


def f4_duty(ep):
    sigma_comb = 1.1                      # uJy/beam, 7.25 GHz combined image
    T_tot = ep["total_hours_table"]
    blocks = block_times(ep)
    dur = np.array([b[1] for b in blocks])
    start = np.array([b[0] for b in blocks])
    sig_i = sigma_comb * np.sqrt(T_tot / dur)
    span_h = float(start[-1] + dur[-1])

    per_block = [{"project": b[2], "date": b[3], "hours": b[1],
                  "sigma_uJy": float(s), "detect_5sigma_uJy": float(5 * s)}
                 for b, s in zip(blocks, sig_i)]

    rng = np.random.default_rng(SEED_F4)
    amps = [10.0, 30.0, 100.0, 300.0, 1000.0]        # uJy, flare amplitude
    durs = [0.5, 2.0, 8.0, 24.0]                     # hours, flare duration
    periods = np.logspace(np.log10(6.0), np.log10(2.0e5), 45)   # hours

    def detect_prob(S, tau, T_rec):
        """P(at least one detection) over random flare phase, N_TRIALS draws.

        A flare train of period T_rec and duration tau is laid over the real
        block timeline with a uniform random phase. Detection is either a
        single block whose tau-averaged flux exceeds its own 5-sigma point,
        or the whole-campaign mean exceeding the combined 5-sigma point.
        """
        phase = rng.uniform(0.0, T_rec, N_TRIALS)
        det = np.zeros(N_TRIALS, dtype=bool)
        on_tot = np.zeros(N_TRIALS)
        for t0, dt, s in zip(start, dur, sig_i):
            # on-time of the flare train inside [t0, t0+dt], per trial
            k0 = np.floor((t0 - phase) / T_rec)
            on = np.zeros(N_TRIALS)
            for kk in (k0, k0 + 1, k0 + 2):
                fs = phase + kk * T_rec
                on += np.clip(np.minimum(fs + tau, t0 + dt)
                              - np.maximum(fs, t0), 0.0, None)
            on = np.minimum(on, dt)
            on_tot += on
            det |= (S * on / dt) > (5.0 * s)
        det |= (S * on_tot / dur.sum()) > (5.0 * sigma_comb)
        return float(np.mean(det))

    grid = []
    for S in amps:
        for tau in durs:
            probs = [detect_prob(S, tau, T) for T in periods]
            probs = np.array(probs)
            # longest recurrence period still detected in >=95% of phases
            ok = np.where(probs >= 0.95)[0]
            T_excl = float(periods[ok[-1]]) if len(ok) else None
            grid.append({"amp_uJy": S, "dur_hr": tau,
                         "T_excluded_below_hr": T_excl,
                         "T_excluded_below_days": (T_excl / 24.0
                                                   if T_excl else None),
                         "duty_at_threshold": (tau / T_excl if T_excl
                                               else None),
                         "probs": probs.tolist()})
    return {
        "sigma_combined_uJy": sigma_comb,
        "total_hours": T_tot,
        "n_blocks": len(blocks),
        "campaign_span_hours": span_h,
        "campaign_span_years": span_h / 24.0 / 365.25,
        "median_block_hours": float(np.median(dur)),
        "block_sigma_range_uJy": [float(sig_i.min()), float(sig_i.max())],
        "median_block_sigma_uJy": float(np.median(sig_i)),
        "per_block": per_block,
        "periods_hr": periods.tolist(),
        "grid": grid,
        "seed": SEED_F4,
        "n_trials": N_TRIALS,
        "scaling_assumption": (
            "sigma_i = 1.1 uJy * sqrt(177.19 / t_i); equal sensitivity per "
            "on-source hour across the three projects and both observing "
            "frequencies, which Mahida et al. (2026) do not state per block."),
    }


# ---------------------------------------------------------------------------
# F-5  dispersion-measure forecast
# ---------------------------------------------------------------------------
# Two geometries are carried, because they answer different questions:
#   core  -- gas filling the cluster core, radius R_core, the configuration a
#            DM gradient can actually measure with the present sight lines;
#   infl  -- gas confined inside the influence radius of the hole, the
#            configuration Paper F's Bondi rate is about.
# The chord through a uniform sphere of radius R at projected radius b is
# 2*sqrt(R^2 - b^2), so a pulsar behind the sphere accumulates
# DM_excess = n_e * chord(b) (pc cm^-3 with the chord in pc); a pulsar at the
# cluster's mean depth accumulates half of it on average.

R_CORE_PC = 3.74            # 2.37 arcmin core radius (Harris) at 5.43 kpc
R_INFL_PC = 0.4             # GM/sigma^2 at 4e4 Msun, sigma = 21 km/s (Sec. 5)
D_KPC = 5.43


def f5_dm():
    # The timing-set extraction lives with Paper H. This script runs both in
    # the manuscript tree (paper/figs) and in the published mirror
    # (repo/papers/figs), so both relative locations are tried.
    cands = [os.path.join(HERE, "..", "h", "data", "pulsars.json"),
             os.path.join(HERE, "..", "..", "..", "paper", "h", "data",
                          "pulsars.json")]
    path = next(p for p in cands if os.path.exists(p))
    with open(path, encoding="utf-8") as fh:
        pd = json.load(fh)
    rows = []
    for p in pd["pulsars"]:
        dm = p["DM"]
        b_pc = p["theta"]["value"] / 60.0 * np.pi / 180.0 * D_KPC * 1e3
        rows.append({
            "letter": p["letter"],
            "theta_arcmin": p["theta"]["value"],
            "b_pc": float(b_pc),
            "DM": dm["value"],
            "DM_err": dm.get("uncertainty"),
            "DM_where": dm["where"],
            "timing_solution": dm.get("uncertainty") is not None,
            "DM1": (p.get("DM1") or {}).get("value"),
            "DM1_err": (p.get("DM1") or {}).get("uncertainty"),
        })
    rows.sort(key=lambda r: r["b_pc"])

    def chord(b, R):
        return 2.0 * np.sqrt(max(R ** 2 - b ** 2, 0.0))

    signals = {}
    for tag, R in (("core", R_CORE_PC), ("infl", R_INFL_PC)):
        sig = {}
        for ne in (0.01, 0.05, 0.1, 0.2):
            sig["ne_%g" % ne] = {
                "full_chord_centre_pc_cm3": ne * chord(0.0, R),
                "per_pulsar": {r["letter"]: ne * chord(r["b_pc"], R)
                               for r in rows},
                "n_pulsars_inside": sum(1 for r in rows if r["b_pc"] < R),
            }
        signals[tag] = {"R_pc": R, "by_density": sig}

    # what the present 19 sight lines already say about core-filling gas:
    # least-squares amplitude of the chord template against the measured DMs,
    # with a free constant for the Galactic foreground.
    b = np.array([r["b_pc"] for r in rows])
    dm = np.array([r["DM"] for r in rows])
    ch = np.array([chord(x, R_CORE_PC) for x in b])
    A = np.vstack([np.ones_like(ch), ch]).T
    coef, *_ = np.linalg.lstsq(A, dm, rcond=None)
    resid = dm - A @ coef
    dof = len(dm) - 2
    s2 = float(resid @ resid / dof)
    cov = s2 * np.linalg.inv(A.T @ A)
    ne_hat, ne_err = float(coef[1]), float(np.sqrt(cov[1, 1]))

    err_timing = [r["DM_err"] for r in rows if r["DM_err"]]
    return {
        "pulsars": rows,
        "n_pulsars": len(rows),
        "n_with_timing_DM": sum(1 for r in rows if r["timing_solution"]),
        "n_with_DM1": sum(1 for r in rows if r["DM1"] is not None),
        "timing_DM_precision_pc_cm3": {
            "min": min(err_timing), "max": max(err_timing),
            "median": float(np.median(err_timing))},
        "DM_range_pc_cm3": [float(dm.min()), float(dm.max())],
        "DM_scatter_rms_pc_cm3": float(np.std(dm, ddof=1)),
        "geometry": {"D_kpc": D_KPC, "R_core_pc": R_CORE_PC,
                     "R_infl_pc": R_INFL_PC,
                     "b_range_pc": [float(b.min()), float(b.max())]},
        "signals": signals,
        "present_constraint": {
            "model": ("DM_i = DM_0 + n_e * chord(b_i; R_core), uniform sphere, "
                      "free foreground constant, ordinary least squares on the "
                      "19 published DMs"),
            "ne_hat_cm3": ne_hat, "ne_err_cm3": ne_err,
            "ne_95_upper_cm3": ne_hat + 1.645 * ne_err,
            "residual_rms_pc_cm3": float(np.sqrt(s2)),
            "note": ("The sight-line-to-sight-line DM scatter, not the timing "
                     "precision, sets this. It exceeds the per-pulsar DM "
                     "uncertainty by three orders of magnitude, so the "
                     "requirement is on modelling or averaging down that "
                     "scatter, not on measuring DM better."),
        },
        "precision_required": {
            "basis": ("Scaled from the fit above, whose amplitude error is "
                      "sigma(n_e) = %.3f cm^-3 on 19 sight lines. Under the "
                      "same per-sight-line scatter the error falls as "
                      "N^-1/2, so N_required = 19 * (sigma / target)^2."
                      % ne_err),
            "core": {
                "sigma_ne_now_cm3": ne_err,
                "n_needed_1sigma_at_0.1": 19.0 * (ne_err / 0.1) ** 2,
                "n_needed_3sigma_at_0.1": 19.0 * (ne_err / (0.1 / 3.0)) ** 2,
                "scatter_reduction_needed_for_3sigma_at_0.1":
                    ne_err / (0.1 / 3.0),
                "signal_central_chord_at_0.1_pc_cm3": 0.1 * chord(0.0,
                                                                  R_CORE_PC),
            },
            "influence_radius": {
                "signal_central_chord_at_0.1_pc_cm3": 0.1 * chord(0.0,
                                                                  R_INFL_PC),
                "n_sight_lines_intersecting": sum(1 for r in rows
                                                  if r["b_pc"] < R_INFL_PC),
                "note": ("No published pulsar sight line passes within the "
                         "influence radius, so this geometry is not "
                         "constrained at any timing precision; the innermost "
                         "sight line is at %.2f pc." % b.min()),
            },
        },
    }


# ---------------------------------------------------------------------------


def main():
    v3 = load_v3()
    th_base = baseline_draws()

    nuis = f1_nuisance(th_base, v3)
    with open(os.path.join(HERE, "fF_expand_nuisance.json"), "w") as fh:
        json.dump(nuis, fh, indent=1)

    sed = f2_sed(th_base, v3)
    with open(os.path.join(HERE, "fF_expand_sed.json"), "w") as fh:
        json.dump(sed, fh, indent=1)
    f2_figure(sed)

    exc = f3_exclcurve(v3)
    with open(os.path.join(HERE, "fF_expand_exclcurve.json"), "w") as fh:
        json.dump(exc, fh, indent=1)

    with open(os.path.join(HERE, "fF_epochs.json")) as fh:
        ep = json.load(fh)
    duty = f4_duty(ep)
    with open(os.path.join(HERE, "fF_expand_duty.json"), "w") as fh:
        json.dump(duty, fh, indent=1)

    dm = f5_dm()
    with open(os.path.join(HERE, "fF_expand_dm.json"), "w") as fh:
        json.dump(dm, fh, indent=1)

    # ---- console summary -------------------------------------------------
    print("F-1 baseline eps95 (6k/8.2k/40k):",
          ["%.3e" % x for x in nuis["eps95_baseline"]])
    print("F-1 all-frozen           :",
          ["%.3e" % x for x in nuis["eps95_all_frozen"]])
    for r in nuis["rows"]:
        print("   %-5s frozen/base %s   isolated/allfrozen %s" % (
            r["param"],
            ["%.3f" % x for x in r["ratio_frozen_over_base"]],
            ["%.3f" % x for x in r["ratio_isolated_over_allfrozen"]]))
    for fam in sed["families"]:
        for anch in sed["families"][fam]:
            f = sed["families"][fam][anch]
            print("F-2 %-5s %-6s eps95 %.3e binding %s (pred/limit %.2f)"
                  % (fam, anch, f["eps95"], f["binding_band"],
                     f["binding_ratio"]))
    print("F-3 crossings:", exc["crossings"])
    print("F-4 block sigma range %.1f-%.1f uJy (median %.1f)"
          % (duty["block_sigma_range_uJy"][0], duty["block_sigma_range_uJy"][1],
             duty["median_block_sigma_uJy"]))
    for g in duty["grid"]:
        print("   S=%6.0f uJy tau=%4.1f h -> excluded for recurrence < %s"
              % (g["amp_uJy"], g["dur_hr"],
                 ("%.0f h (%.1f d)" % (g["T_excluded_below_hr"],
                                       g["T_excluded_below_days"]))
                 if g["T_excluded_below_hr"] else "none"))
    print("F-5 %d pulsars, %d timing DMs, DM scatter %.2f pc/cm3"
          % (dm["n_pulsars"], dm["n_with_timing_DM"],
             dm["DM_scatter_rms_pc_cm3"]))
    print("F-5 present core-gas fit: n_e = %.3f +/- %.3f cm^-3 (95%% < %.2f)"
          % (dm["present_constraint"]["ne_hat_cm3"],
             dm["present_constraint"]["ne_err_cm3"],
             dm["present_constraint"]["ne_95_upper_cm3"]))
    print("F-5 signal at n_e=0.1: core %.3f, influence-radius %.3f pc cm^-3"
          % (dm["signals"]["core"]["by_density"]["ne_0.1"]
             ["full_chord_centre_pc_cm3"],
             dm["signals"]["infl"]["by_density"]["ne_0.1"]
             ["full_chord_centre_pc_cm3"]))


if __name__ == "__main__":
    main()
