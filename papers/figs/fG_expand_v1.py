"""Paper G v1.2 expansion analyses (WU OCS-G-EXPAND-1, referee items G-1..G-6).

Nothing here changes any v1.1 number.  The analysis of record remains
paper/g/analysis/run_g.py (seed 20260814); this script imports its three modules
as libraries, rebuilds the pipeline state in the same order with the same inputs,
and asserts the reproduced frame offset, membership sums, MSP-like counts and
residual against analysis/results_omega_cen.json before computing anything new.

New content is of four kinds.  G-1, G-2, G-3 and G-5 are pictures of numbers the
v1.1 run already produced.  G-4 is a ranking of the existing 39-source MSP-like
pool under the rule pre-registered in board/notes/G-EXPAND-1-EDITLOG.md Sec. 1,
committed before this file was written.  G-6 is a new fixed-input calculation on
the vendored catalogue's own counts.  No association changes, no re-analysis.

Outputs (all written next to this script):
  fG_expand_skymap.png / .json        G-1  core sky map
  fG_expand_colourflux.png / .json    G-2  colour-flux plane
  fG_expand_lognlogs.png / .json      G-3  log N-log S residual
  fG_target_list.json                 G-4  ranked candidate list (full pool)
  fG_expand_control.png / .json       G-5  control recovery / purity
  fG_expand_variability.json          G-6  epoch-comparison cost table

Run:  python3 fG_expand_v1.py
"""

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GDIR = os.path.abspath(os.path.join(HERE, "..", "g"))
sys.path.insert(0, os.path.join(GDIR, "analysis"))

import classify as C          # noqa: E402
import crossmatch as X        # noqa: E402
import residual as R          # noqa: E402
import run_g as G             # noqa: E402

RESULTS = os.path.join(GDIR, "analysis", "results_omega_cen.json")
CONTROL = os.path.join(GDIR, "analysis", "results_control_47tuc.json")

# ---------------------------------------------------------------------------
# external inputs used only by G-6, each primary-verified on 2026-08-20
# ---------------------------------------------------------------------------
T_2012_KS = 222.2            # Henleywillis+2018: 173.7 + 48.5 ks, ObsIDs 13726/13727
T_2000_KS = 70.0             # Haggard, Cool & Davies 2009, ApJ 697, 224, abstract
EROSITA_LIMIT_CGS = 5.0e-14  # Merloni+2024 A&A 682 A34, eRASS1 0.5-2 keV, 50% complete
EROSITA_HEW_ARCSEC = 26.0    # Predehl+2021 A&A 647 A1, HEW averaged over the FoV


def _w(name, obj):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)


# ---------------------------------------------------------------------------
# pipeline state, reproduced and asserted against the run of record
# ---------------------------------------------------------------------------


def rebuild():
    """Re-derive every v1.1 quantity this expansion stands on, then check it."""
    published = json.load(open(RESULTS, encoding="utf-8"))

    cat = X.load_omega_cen_catalogue()
    probes = X.load_omega_cen_probes()
    radii = [s["offset_rc"] * G.OMEGA_CEN_RC_ARCSEC for s in cat]
    offset = X.estimate_frame_offset(cat, probes["tier1"], G.ZH_ANCHORS)

    xm1 = X.run_crossmatch(cat, probes["tier1"], G.OMEGA_CEN_CENTRE, "t1",
                           n_trials=G.N_TRIALS, seed=G.SEED, frame_offset=offset)
    xm2 = X.run_crossmatch(cat, probes["tier2"], G.OMEGA_CEN_CENTRE, "t2",
                           n_trials=G.N_TRIALS, seed=G.SEED, frame_offset=offset)

    area_deg2 = math.pi * G.OMEGA_CEN_RMAX_ARCSEC ** 2 / 3600.0 ** 2
    agn = R.agn_bracket(1.40e-16, area_deg2)
    model = C.external_model(60, G.OMEGA_CEN_RC_ARCSEC,
                             agn["surface_density_per_deg2"] / 3600.0 ** 2,
                             G.OMEGA_CEN_RMAX_ARCSEC)
    rows = C.assign_membership(cat, model, radii)

    recovered = [m["match_id"] for m in xm1["matches"] if m["matched"]]
    region = C.msp_like_region(cat, recovered)

    keep = {r["id"] for r in rows if r["radius_arcsec"] <= G.OMEGA_CEN_RMAX_ARCSEC}
    cat_ap = [s for s in cat if s["id"] in keep]
    rows_ap = [r for r in rows if r["id"] in keep]
    counts = {k: C.count_msp_like(cat_ap, region, rows_ap, k)
              for k in ("box", "ellipse")}

    # ---- assertions against the published run ------------------------------
    fr = published["frame_registration"]
    assert abs(offset["dra_arcsec"] - fr["dra_arcsec"]) < 1e-9, offset
    assert abs(offset["ddec_arcsec"] - fr["ddec_arcsec"]) < 1e-9, offset
    assert offset["n_anchors"] == fr["n_anchors"]

    pub_ml = published["residual_census"]["msp_like_unidentified"]["counts"]
    for k in ("box", "ellipse"):
        assert counts[k]["n_unidentified_inside"] == pub_ml[k]["n_unidentified_inside"], k
        assert abs(counts[k]["membership_weighted_count"]
                   - pub_ml[k]["membership_weighted_count"]) < 1e-6, k

    pub_res = published["residual_census"]
    assert len(cat_ap) == pub_res["aperture"]["n_catalogue_sources_inside"]
    assert sum(1 for r in rows_ap if not r["identified"]) == pub_res["n_unidentified"]
    assert abs(agn["n_expected"] - pub_res["agn_expectation"]["n_expected"]) < 1e-9

    pub_mem = published["membership_sensitivity"]["n_mem_60__fifth_percentile_soft"]
    got = round(sum(r["p_member_spatial"] for r in rows), 2)
    assert abs(got - pub_mem["sum_p_member"]) < 0.011, (got, pub_mem["sum_p_member"])

    print("[assert] v1.1 pipeline state reproduced: offset, membership, "
          "MSP-like counts, aperture and background all match results_omega_cen.json")

    return {
        "published": published, "cat": cat, "probes": probes, "radii": radii,
        "offset": offset, "xm1": xm1, "xm2": xm2, "agn": agn, "model": model,
        "rows": rows, "region": region, "cat_ap": cat_ap, "rows_ap": rows_ap,
        "counts": counts, "recovered": recovered, "area_deg2": area_deg2,
    }


# ---------------------------------------------------------------------------
# G-4  ranked candidate target list
# ---------------------------------------------------------------------------
# The ranking rule was fixed and committed in board/notes/G-EXPAND-1-EDITLOG.md
# Sec. 1 before this function existed:
#
#     R = P_member x (1 - P_chance)
#
# pool  = unidentified, in-aperture, colour+flux present, inside the PRIMARY box
# P_mem = classify.membership_probability under the adopted baseline model
#         (N_mem = 60, r_c = 155", background at the 5th-percentile soft limit)
# P_ch  = max of the three crossmatch.chance_coincidence estimators, candidate
#         treated as its own probe, sigma_radio = 0, 20,000 trials, seed 20260814
# ties  = descending soft flux, then catalogue name ascending
#
# One implementation decision, disclosed rather than folded in: the candidate is
# removed from the catalogue when its own chance rate is computed.  A source
# cannot be a false association with itself, and leaving it in would credit every
# candidate with a guaranteed hit in any trial that lands back on its position.


def raw_census():
    path = os.path.join(GDIR, "data", "xray_census.json")
    with open(path, encoding="utf-8") as fh:
        return {s["name"]: s for s in json.load(fh)["sources"]}


def confirmed_counterpart_ids():
    """Henleywillis IDs that later radio work identifies as MSP X-ray counterparts.

    Read from the vendored Zhao & Heinke counterpart file, not from this pipeline's
    own matches, so the flag does not depend on the match rule under test.
    """
    path = os.path.join(GDIR, "data", "msp_counterparts.json")
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    out = set()
    for row in d.get("counterparts", d.get("msp_counterparts", [])):
        for key in ("henleywillis_id", "hw_id", "henleywillis_source", "xray_id"):
            if row.get(key):
                out.add(str(row[key]))
    return out


def caveat_flags(raw, radius_arcsec, in_ellipse):
    """Per-source flags, all read from census fields, none of them scored."""
    flags = []
    if raw.get("new_source_flag"):
        flags.append("new_source")
    if (raw.get("epos_95pct_arcsec") or 0.0) > 1.0:
        flags.append("large_error_circle")
    if raw.get("flux_ratio_note_g"):
        flags.append("flux_ratio_flagged")
    fr = raw.get("flux_ratio_2012_2000")
    if fr:
        try:
            if abs(math.log10(float(fr))) > 0.3:
                flags.append("variable_candidate")
        except ValueError:
            pass
    cm = raw.get("xray_counts_medium_corrected")
    if cm is not None and cm < 10.0:
        flags.append("low_counts")
    if radius_arcsec > 400.0:
        flags.append("outer_aperture")
    if in_ellipse is False:
        flags.append("outside_ellipse")
    return flags


def g4_target_list(S):
    raw = raw_census()
    pool_ids = list(S["counts"]["box"]["ids"])
    by_id = {s["id"]: s for s in S["cat"]}
    prow = {r["id"]: r for r in S["rows"]}

    cat_ra = np.array([s["ra"] for s in S["cat"]])
    cat_dec = np.array([s["dec"] for s in S["cat"]])
    cat_epos = np.array([s["epos95"] for s in S["cat"]])
    idx_of = {s["id"]: i for i, s in enumerate(S["cat"])}

    confirmed = confirmed_counterpart_ids()
    anchors = set(S["region"]["anchors_used"])

    rows = []
    for cid in pool_ids:
        src = by_id[cid]
        keep = np.ones(len(S["cat"]), dtype=bool)
        keep[idx_of[cid]] = False        # a source is not its own false match
        probe = {"id": cid, "ra": src["ra"], "dec": src["dec"], "sigma_radio": 0.0}
        cc = X.chance_coincidence(probe, cat_ra[keep], cat_dec[keep], cat_epos[keep],
                                  G.OMEGA_CEN_CENTRE, n_trials=G.N_TRIALS, seed=G.SEED)
        p_ch = max(cc["p_chance_rotation"], cc["p_chance_offset"],
                   cc["p_chance_analytic_poisson"])
        p_mem = prow[cid]["p_member_spatial"]
        rows.append({
            "id": cid,
            "ra_j2000": raw[cid]["ra_j2000"],
            "dec_j2000": raw[cid]["dec_j2000"],
            "radius_arcsec": prow[cid]["radius_arcsec"],
            "epos_95pct_arcsec": raw[cid]["epos_95pct_arcsec"],
            "colour_log_soft_hard": src["color"],
            "flux_soft_1e-19_W_m2": src["flux_soft"],
            "flux_total_1e-19_W_m2": src["flux_total"],
            "counts_medium_corrected": raw[cid]["xray_counts_medium_corrected"],
            "p_member": round(p_mem, 4),
            "p_chance_rotation": cc["p_chance_rotation"],
            "p_chance_offset": cc["p_chance_offset"],
            "p_chance_analytic_poisson": round(cc["p_chance_analytic_poisson"], 6),
            "p_chance_used_max": round(p_ch, 6),
            "score": round(p_mem * (1.0 - p_ch), 6),
            "flags": caveat_flags(raw[cid], prow[cid]["radius_arcsec"],
                                  C.in_region(src, S["region"], "ellipse")),
            "confirmed_msp_counterpart": cid in confirmed,
            "box_anchor": cid in anchors,
        })

    rows.sort(key=lambda r: (-r["score"], -(r["flux_soft_1e-19_W_m2"] or 0.0), r["id"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    # The pre-registered pool is defined by the absence of a published OPTICAL
    # identification, which is the catalogue's own field.  Sources later confirmed
    # as MSP X-ray counterparts by radio work still carry a null optical ID, so the
    # rule retains them.  They are flagged rather than removed, and a secondary
    # ordering with them dropped is reported alongside; the rule itself is not
    # rewritten after seeing its output.
    fresh = [r for r in rows if not r["confirmed_msp_counterpart"]]
    for i, r in enumerate(fresh, 1):
        r["rank_counterparts_removed"] = i

    p_ch_all = [r["p_chance_used_max"] for r in rows]

    out = {
        "item": "G-4",
        "ranking_rule": {
            "pre_registered_in": "board/notes/G-EXPAND-1-EDITLOG.md Sec. 1",
            "committed_before_computation": True,
            "score": "P_member * (1 - P_chance)",
            "p_member": ("classify.membership_probability under the adopted baseline "
                         "external model: N_mem = 60, r_c = 155 arcsec, background "
                         "surface density from the log N-log S relation at the "
                         "5th-percentile soft flux limit"),
            "p_chance": ("max of rotation, offset and analytic-Poisson estimators from "
                         "crossmatch.chance_coincidence, candidate treated as its own "
                         "probe with sigma_radio = 0, the source itself removed from "
                         "the comparison catalogue, %d trials, seed %d"
                         % (G.N_TRIALS, G.SEED)),
            "ties": "descending soft flux, then catalogue name ascending",
            "pool": ("unidentified, inside the 480 arcsec aperture, colour and total "
                     "flux both tabulated, inside the primary n=4 bounding box of "
                     "Sec. 5.7"),
            "no_threshold_applied": True,
        },
        "n_pool": len(rows),
        "n_pool_confirmed_counterparts": sum(1 for r in rows
                                             if r["confirmed_msp_counterpart"]),
        "n_top20_confirmed_counterparts": sum(1 for r in rows[:20]
                                              if r["confirmed_msp_counterpart"]),
        "p_chance_range": [min(p_ch_all), max(p_ch_all)],
        "p_chance_is_near_uniform": ("the three estimators return between %.4f and "
                                     "%.4f over the whole pool, so the (1 - P_chance) "
                                     "factor changes no rank by more than one place "
                                     "and the ordering is P_member to within that. "
                                     "Stated rather than repaired: the rule was fixed "
                                     "before the numbers existed."
                                     % (min(p_ch_all), max(p_ch_all))),
        "top_n_printed_in_paper": 20,
        "score_range": [rows[-1]["score"], rows[0]["score"]],
        "not_a_claim": ("a follow-up priority ordering under two stated assumptions. "
                        "No AGN screen is applied, so Sec. 5.7's upper-bound caveat "
                        "applies to every row, and P_member moves with the external "
                        "normalisation exactly as Table 4 shows."),
        "candidates": rows,
    }
    _w("fG_target_list.json", out)
    return out


# ---------------------------------------------------------------------------
# G-3  log N-log S residual
# ---------------------------------------------------------------------------
# No new estimator.  The Moretti relation and its bracket are those of Sec. 5.4,
# drawn as a function of flux limit instead of evaluated at one; the observed
# curve is the cumulative count of unidentified in-aperture sources above the
# same limit.


def g3_lognlogs(S):
    unid = [r["id"] for r in S["rows_ap"] if not r["identified"]]
    by_id = {s["id"]: s for s in S["cat"]}
    fluxes = np.array(sorted(by_id[i]["flux_soft"] for i in unid
                             if by_id[i]["flux_soft"]))
    n_no_soft = len(unid) - len(fluxes)

    grid = np.logspace(math.log10(0.6), math.log10(60.0), 90)   # 1e-19 W/m2
    obs = np.array([float((fluxes >= f).sum()) for f in grid])
    brackets = [R.agn_bracket(float(f) * 1e-16, S["area_deg2"]) for f in grid]
    exp_c = np.array([b["n_expected"] for b in brackets])
    exp_lo = np.array([b["n_expected_low"] for b in brackets])
    exp_hi = np.array([b["n_expected_high"] for b in brackets])
    in_range = np.array([b["within_fitted_flux_range"] for b in brackets])

    adopted = 1.40      # 5th-percentile soft flux, in 1e-19 W/m2
    j = int(np.argmin(np.abs(grid - adopted)))
    summary = {
        "n_flux_bins": len(grid),
        "adopted_limit_1e-19_W_m2": adopted,
        "observed_at_adopted": float(obs[j]),
        "expected_at_adopted": float(exp_c[j]),
        "residual_at_adopted": round(float(obs[j] - exp_c[j]), 1),
        "fraction_of_grid_where_observed_inside_bracket": round(
            float(np.mean((obs >= exp_lo) & (obs <= exp_hi))), 3),
        "n_grid_points_above_high_bracket": int((obs > exp_hi).sum()),
        "above_bracket_flux_band_1e-19_W_m2": (
            [float(grid[np.where(obs > exp_hi)[0][0]]),
             float(grid[np.where(obs > exp_hi)[0][-1]])]
            if np.any(obs > exp_hi) else None),
        "max_excess_over_high_bracket_sources": round(
            float((obs - exp_hi).max()), 1),
        "poisson_sigma_on_observed_there": round(
            float(np.sqrt(obs[np.argmax(obs - exp_hi)])), 1),
        "reading": ("the observed curve lies inside the bracket over most of the "
                    "grid and brushes its upper edge over a narrow, non-contiguous "
                    "flux band. The largest excess is smaller than the Poisson "
                    "error on the count there, so no excess is claimed."),
    }
    out = {
        "item": "G-3",
        "n_unidentified_in_aperture": len(unid),
        "n_unidentified_without_soft_flux": n_no_soft,
        "moretti_parameters": R.MORETTI_SOFT,
        "area_deg2": round(S["area_deg2"], 5),
        "curve": {
            "flux_limit_1e-19_W_m2": [round(float(f), 4) for f in grid],
            "observed_cumulative": [float(v) for v in obs],
            "expected_central": [round(float(v), 2) for v in exp_c],
            "expected_low": [round(float(v), 2) for v in exp_lo],
            "expected_high": [round(float(v), 2) for v in exp_hi],
            "within_moretti_fitted_range": [bool(v) for v in in_range],
        },
        "summary": summary,
        "caveat": ("the observed curve flattens at the faint end because the "
                   "catalogue is incomplete there, not because the sky is; and "
                   "Eddington bias pushes faint fluxes up, so the observed curve "
                   "is an upper bound on the true count at a given limit."),
    }
    _w("fG_expand_lognlogs.json", out)
    return out


# ---------------------------------------------------------------------------
# G-6  epoch-comparison cost table (planning content, no epoch analysis)
# ---------------------------------------------------------------------------
# The catalogue counts are the 2012 ACIS-I data alone (173.7 + 48.5 ks).  The
# only other deep Chandra epoch of this field is the ~70 ks 2000 exposure of
# Haggard, Cool & Davies (2009).  For a source held at constant flux the second
# epoch collects r = t_2000/t_2012 times the counts, and the 3-sigma detectable
# flux ratio follows from Poisson errors on the two rates.  Nothing is measured
# here: no epoch-resolved event data are touched and no source is called variable.


def g6_variability(S):
    raw = raw_census()
    r_exp = T_2000_KS / T_2012_KS
    pool = set(S["counts"]["box"]["ids"])

    rows = []
    for src in S["cat_ap"]:
        n12 = raw[src["id"]]["xray_counts_medium_corrected"]
        if not n12 or n12 <= 0:
            continue
        n00 = n12 * r_exp
        sig = math.sqrt(1.0 / n12 + 1.0 / n00)
        rows.append({
            "id": src["id"],
            "counts_2012_medium_corrected": n12,
            "expected_counts_2000_at_constant_flux": round(n00, 1),
            "sigma_ln_ratio": round(sig, 4),
            "min_detectable_flux_ratio_3sigma": round(math.exp(3.0 * sig), 2),
            "gaussian_approximation_valid": bool(n00 >= 10.0),
            "in_msp_like_pool": src["id"] in pool,
        })
    rows.sort(key=lambda r: r["min_detectable_flux_ratio_3sigma"])

    def tally(thr, only_pool=False, valid_only=True):
        return sum(1 for r in rows
                   if r["min_detectable_flux_ratio_3sigma"] < thr
                   and (r["gaussian_approximation_valid"] or not valid_only)
                   and (r["in_msp_like_pool"] or not only_pool))

    ladder = [{"flux_ratio": t,
               "n_aperture_sources": tally(t),
               "n_msp_like_pool": tally(t, only_pool=True),
               "n_aperture_sources_no_validity_cut": tally(t, valid_only=False),
               "n_msp_like_pool_no_validity_cut": tally(t, only_pool=True,
                                                        valid_only=False)}
              for t in (1.5, 2.0, 3.0, 5.0, 10.0)]

    # eROSITA leg: depth and beam, both against the catalogue's own numbers.
    flux_cgs = np.array([s["flux_total"] for s in S["cat_ap"] if s["flux_total"]])
    n_above = int((flux_cgs * 1e-16 >= EROSITA_LIMIT_CGS).sum())
    ra = np.array([s["ra"] for s in S["cat_ap"]])
    dec = np.array([s["dec"] for s in S["cat_ap"]])
    cosd = math.cos(math.radians(G.OMEGA_CEN_CENTRE["dec"]))
    d = np.hypot((ra[:, None] - ra[None, :]) * cosd,
                 dec[:, None] - dec[None, :]) * 3600.0
    np.fill_diagonal(d, np.inf)
    n_blended = int((d.min(axis=1) <= EROSITA_HEW_ARCSEC).sum())

    out = {
        "item": "G-6",
        "scope": ("planning content. No epoch-resolved event data are analysed and "
                  "no source is classified as variable here."),
        "chandra": {
            "t_2012_ks": T_2012_KS,
            "t_2000_ks": T_2000_KS,
            "t_2000_reference": "Haggard, Cool & Davies 2009, ApJ 697, 224",
            "exposure_ratio": round(r_exp, 4),
            "band": "medium, 0.5-4.5 keV, vignetting- and exposure-corrected counts",
            "method": ("sigma_lnR = sqrt(1/n_2012 + 1/n_2000) with n_2000 the count "
                       "a constant-flux source would give in the shallower epoch; "
                       "R_min = exp(3 sigma_lnR). Gaussian error propagation on "
                       "Poisson counts, flagged invalid where the fainter epoch "
                       "expects under 10 counts."),
            "n_aperture_sources_with_counts": len(rows),
            "n_gaussian_valid": sum(1 for r in rows if r["gaussian_approximation_valid"]),
            "ladder": ladder,
            "best_in_pool": [r["id"] for r in rows if r["in_msp_like_pool"]][:5],
            "validity_floor_note": ("the 10-count floor on the shallower epoch bites "
                                    "at n_2012 = 31.7, where R_min is already 2.95, "
                                    "so restricting to rows where the Gaussian "
                                    "approximation holds and requiring R_min < 3 are "
                                    "nearly the same cut. Counts are given both ways "
                                    "rather than picking one."),
            "caveats": [
                "the 2000 exposure reaches a limiting flux of ~4.3e-16 erg/cm2/s "
                "against ~3e-16 for the 2012 data, so the shallower epoch is not "
                "simply a shorter version of the deeper one",
                "aperture, off-axis angle and extraction differ between the two "
                "reductions; matching them is part of the cost this table prices",
                "R_min is a floor on what an epoch comparison could detect, not a "
                "prediction of what it would find",
            ],
        },
        "erosita": {
            "flux_limit_cgs_0.5-2keV": EROSITA_LIMIT_CGS,
            "flux_limit_reference": ("Merloni et al. 2024, A&A 682, A34, eRASS1 "
                                     "50 per cent completeness"),
            "hew_arcsec_fov_averaged": EROSITA_HEW_ARCSEC,
            "hew_reference": "Predehl et al. 2021, A&A 647, A1",
            "n_aperture_sources_above_limit": n_above,
            "n_aperture_sources_with_neighbour_inside_hew": n_blended,
            "n_aperture_sources": len(S["cat_ap"]),
        },
        "per_source": rows,
    }
    _w("fG_expand_variability.json", out)
    return out


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _tanplane(ra, dec, centre):
    """Offsets east and north of the cluster centre, in arcsec."""
    cosd = math.cos(math.radians(centre["dec"]))
    dx = (np.asarray(ra) - centre["ra"]) * cosd * 3600.0
    dy = (np.asarray(dec) - centre["dec"]) * 3600.0
    return dx, dy


def g1_skymap(S):
    """G-1: the core sky map, catalogue against timing positions."""
    plt = _mpl()
    from matplotlib.patches import Circle

    centre = G.OMEGA_CEN_CENTRE
    raw = raw_census()
    prow = {r["id"]: r for r in S["rows"]}
    ident = {i: prow[i]["identified"] for i in prow}
    pool = set(S["counts"]["box"]["ids"])

    dx, dy = _tanplane([s["ra"] for s in S["cat"]], [s["dec"] for s in S["cat"]], centre)
    rr = np.array([prow[s["id"]]["radius_arcsec"] for s in S["cat"]])
    is_id = np.array([bool(ident[s["id"]]) for s in S["cat"]])
    is_pool = np.array([s["id"] in pool for s in S["cat"]])
    inside = rr <= G.OMEGA_CEN_RMAX_ARCSEC

    probes = X.apply_frame_offset(S["probes"]["tier1"] + S["probes"]["tier2"], S["offset"])
    px, py = _tanplane([q["ra"] for q in probes], [q["dec"] for q in probes], centre)
    ptier = np.array([q["tier"] for q in probes])
    pid = [q["id"] for q in probes]

    matched = {m["probe"]: m for m in S["xm1"]["matches"] if m["matched"]}
    anchors = {a["probe"]: a for a in S["offset"]["anchors"]}

    by_id = {s_["id"]: s_ for s_ in S["cat"]}
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.5))

    circ_scale = {520.0: 40.0, 130.0: 10.0}
    vec_scale = {520.0: 60.0, 130.0: 20.0}
    for ax, half, title in zip(
            axes, (520.0, 130.0),
            ("full aperture, match circles $\\times40$",
             "core, inner $130''$, match circles $\\times10$")):
        m_out = (~is_id) & (~is_pool)
        ax.scatter(dx[m_out], dy[m_out], s=9, facecolor="none",
                   edgecolor="#9aa3ad", linewidth=0.6,
                   label="unidentified" if half > 500 else None)
        ax.scatter(dx[is_id], dy[is_id], s=13, marker="s", color="#2f6f3e",
                   alpha=0.75, label="published optical ID" if half > 500 else None)
        ax.scatter(dx[is_pool], dy[is_pool], s=26, marker="D", facecolor="none",
                   edgecolor="#c2571a", linewidth=1.1,
                   label="MSP-like pool (39)" if half > 500 else None)

        t1 = ptier == 1
        ax.scatter(px[t1], py[t1], s=52, marker="*", color="#1f4e9c",
                   label="pulsar, tier 1 (registered)" if half > 500 else None,
                   zorder=6)
        ax.scatter(px[~t1], py[~t1], s=46, marker="*", facecolor="none",
                   edgecolor="#1f4e9c", linewidth=1.0,
                   label="pulsar, tier 2" if half > 500 else None, zorder=6)

        for c, ls, lab in ((G.OMEGA_CEN_RC_ARCSEC, ":", "core radius $155''$"),
                           (G.OMEGA_CEN_RMAX_ARCSEC, "--", "aperture $480''$")):
            ax.add_patch(Circle((0, 0), c, fill=False, ls=ls, lw=1.0,
                                edgecolor="#4a4a4a",
                                label=lab if half > 500 else None))

        for i, q in enumerate(probes):
            m = matched.get(q["id"])
            if m is None:
                continue
            ax.add_patch(Circle((px[i], py[i]), m["match_radius_arcsec"] * circ_scale[half],
                                fill=False, edgecolor="#b3261e", lw=0.9, zorder=7))
            ax.annotate(q["id"], (px[i], py[i]), textcoords="offset points",
                        xytext=(6, 5), fontsize=8, color="#1f4e9c", zorder=8)

        # per-anchor deviation vectors, exaggerated so a sub-arcsecond shift shows
        for pid_, a in anchors.items():
            if pid_ not in pid:
                continue
            i = pid.index(pid_)
            ax.arrow(px[i], py[i],
                     -a["dra_arcsec"] * vec_scale[half],
                     a["ddec_arcsec"] * vec_scale[half],
                     head_width=half / 55.0, head_length=half / 42.0,
                     fc="#2f6f3e", ec="#2f6f3e", lw=0.8, zorder=8,
                     length_includes_head=True)

        # the MSP H association, called out: registered position to source 14c
        i_h = pid.index("H")
        h14 = by_id["14c"]
        hx, hy = _tanplane([h14["ra"]], [h14["dec"]], centre)
        ax.plot([px[i_h], hx[0]], [py[i_h], hy[0]], color="#b3261e", ls="--",
                lw=1.2, zorder=9)
        ax.annotate("H to 14c, $1.81''$", (px[i_h], py[i_h]),
                    textcoords="offset points",
                    xytext=((-16, -26) if half > 500 else (10, -6)),
                    ha=("right" if half > 500 else "left"),
                    fontsize=8.4, color="#b3261e", weight="bold", zorder=10)

        ax.set_xlim(half, -half)
        ax.set_ylim(-half, half)
        ax.set_aspect("equal")
        ax.set_xlabel(r"$\Delta\alpha\cos\delta$ (arcsec, east left)")
        ax.set_title(title, fontsize=10)
        ax.grid(alpha=0.15)
    axes[0].set_ylabel(r"$\Delta\delta$ (arcsec)")
    axes[0].legend(loc="upper left", fontsize=7.4, frameon=False,
                   handletextpad=0.5, labelspacing=0.35)
    axes[1].annotate("green arrows: per-anchor X-ray $-$ radio deviation,\n"
                     "exaggerated $\\times20$",
                     (0.03, 0.03), xycoords="axes fraction", fontsize=7.4)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fG_expand_skymap.png"), dpi=200)
    plt.close(fig)

    out = {
        "item": "G-1",
        "n_sources_plotted": len(S["cat"]),
        "n_inside_aperture": int(inside.sum()),
        "n_probes_plotted": len(probes),
        "n_registered_matches": len(matched),
        "frame_offset_arcsec": {"dra": S["offset"]["dra_arcsec"],
                                "ddec": S["offset"]["ddec_arcsec"]},
        "anchor_shift_vectors": [{"probe": k, "dra_arcsec": v["dra_arcsec"],
                                  "ddec_arcsec": v["ddec_arcsec"],
                                  "residual_arcsec": v["residual_arcsec"]}
                                 for k, v in anchors.items()],
        "match_circle_scale_in_figure": {"left_panel": 40.0, "right_panel": 10.0},
        "deviation_vector_scale_in_figure": {"left_panel": 60.0, "right_panel": 20.0},
        "note": ("match circles are sub-arcsecond and are drawn at an exaggerated "
                 "scale so they are visible at this field size; every quoted "
                 "separation is the true one."),
    }
    _w("fG_expand_skymap.json", out)
    return out


def g2_colourflux(S):
    """G-2: the colour-flux plane with the box and the ellipse drawn."""
    plt = _mpl()
    from matplotlib.patches import Rectangle, Ellipse

    reg = S["region"]
    pool = set(S["counts"]["box"]["ids"])
    ell_ids = set(S["counts"]["ellipse"]["ids"])
    prow = {r["id"]: r for r in S["rows"]}

    pts = {"unid": [], "ident": [], "box": [], "ell_only": [], "anchor": []}
    for s in S["cat_ap"]:
        if s["color"] is None or not s["flux_total"]:
            continue
        xy = (s["color"], math.log10(s["flux_total"]))
        if s["id"] in reg["anchors_used"]:
            pts["anchor"].append(xy)
        elif prow[s["id"]]["identified"]:
            pts["ident"].append(xy)
        elif s["id"] in pool:
            pts["box"].append(xy)
        elif s["id"] in ell_ids:
            pts["ell_only"].append(xy)
        else:
            pts["unid"].append(xy)

    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    b = reg["box"]
    ax.add_patch(Rectangle((b["color_min"], b["log_flux_total_min"]),
                           b["color_max"] - b["color_min"],
                           b["log_flux_total_max"] - b["log_flux_total_min"],
                           fill=False, edgecolor="#c2571a", lw=1.6,
                           label="primary box ($n=4$ anchors)"))
    e = reg["ellipse"]
    cov = np.array(e["cov"])
    vals, vecs = np.linalg.eigh(cov)
    ang = math.degrees(math.atan2(vecs[1, np.argmax(vals)], vecs[0, np.argmax(vals)]))
    w, h = 2.0 * e["n_sigma"] * np.sqrt(np.maximum(vals[::-1], 0.0))
    ax.add_patch(Ellipse(e["mean"], w, h, angle=ang, fill=False,
                         edgecolor="#1f4e9c", ls="--", lw=1.4,
                         label=r"$2\sigma$ ellipse (secondary)"))

    def sc(key, **kw):
        if pts[key]:
            a = np.array(pts[key])
            ax.scatter(a[:, 0], a[:, 1], **kw)

    sc("unid", s=11, facecolor="none", edgecolor="#9aa3ad", lw=0.6,
       label="unidentified, outside both")
    sc("ident", s=15, marker="s", color="#2f6f3e", alpha=0.7,
       label="published optical ID")
    sc("ell_only", s=22, marker="^", facecolor="none", edgecolor="#1f4e9c", lw=1.0,
       label="unidentified, ellipse only")
    sc("box", s=30, marker="D", facecolor="none", edgecolor="#c2571a", lw=1.2,
       label="unidentified, inside box (39)")
    sc("anchor", s=90, marker="*", color="#b3261e", zorder=6,
       label="confirmed MSP counterpart anchor (4)")

    ax.set_xlabel(r"X-ray colour  $\log_{10}(\mathrm{soft}/\mathrm{hard})$")
    ax.set_ylabel(r"$\log_{10}$ total flux $(10^{-19}\,\mathrm{W\,m^{-2}})$")
    ax.grid(alpha=0.15)
    ax.legend(loc="upper left", fontsize=8, frameon=False, labelspacing=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fG_expand_colourflux.png"), dpi=200)
    plt.close(fig)

    out = {
        "item": "G-2",
        "region": reg,
        "counts": S["counts"],
        "n_plotted": sum(len(v) for v in pts.values()),
        "n_aperture_sources_without_colour_or_flux": len(S["cat_ap"]) -
        sum(len(v) for v in pts.values()),
        "note": ("the box is drawn on the four anchors plotted inside it, so their "
                 "position in the region is a construction, not a test of it."),
    }
    _w("fG_expand_colourflux.json", out)
    return out


def g3_figure(g3):
    plt = _mpl()
    c = g3["curve"]
    f = np.array(c["flux_limit_1e-19_W_m2"])
    obs = np.array(c["observed_cumulative"])
    ce = np.array(c["expected_central"])
    lo = np.array(c["expected_low"])
    hi = np.array(c["expected_high"])

    fig, axes = plt.subplots(2, 1, figsize=(7.4, 6.4), sharex=True,
                             gridspec_kw={"height_ratios": [2.1, 1.0]})
    ax = axes[0]
    ax.fill_between(f, lo, hi, color="#1f4e9c", alpha=0.16,
                    label="Moretti background, parameter bracket")
    ax.plot(f, ce, color="#1f4e9c", lw=1.5, label="Moretti background, central")
    ax.plot(f, obs, color="#b3261e", lw=1.8,
            label="unidentified sources, observed")
    adopted = g3["summary"]["adopted_limit_1e-19_W_m2"]
    for a in axes:
        a.axvline(adopted, color="k", ls=":", lw=1.0)
    ax.annotate("adopted limit\n$1.4\\times10^{-16}$", (adopted, 0.965),
                xycoords=("data", "axes fraction"),
                textcoords="offset points", xytext=(6, 0), fontsize=8, va="top")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_ylabel(r"$N(>S)$ inside the $480''$ aperture")
    ax.grid(alpha=0.15, which="both")
    ax.legend(loc="lower left", fontsize=8.4, frameon=False)

    ax = axes[1]
    ax.fill_between(f, lo - ce, hi - ce, color="#1f4e9c", alpha=0.16)
    ax.axhline(0.0, color="#1f4e9c", lw=1.2)
    ax.plot(f, obs - ce, color="#b3261e", lw=1.8)
    ax.set_xscale("log")
    ax.set_xlabel(r"soft-band flux limit $(10^{-19}\,\mathrm{W\,m^{-2}}"
                  r" = 10^{-16}\,\mathrm{erg\,cm^{-2}\,s^{-1}})$")
    ax.set_ylabel("observed $-$ central")
    ax.grid(alpha=0.15, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fG_expand_lognlogs.png"), dpi=200)
    plt.close(fig)


def g5_control(S):
    """G-5: control recovery and purity, as a figure rather than three percentages."""
    plt = _mpl()
    pub = json.load(open(CONTROL, encoding="utf-8"))
    scales = [1.0, 1.5, 2.5]
    keys = ["radius_scale_%s" % ("1.0" if x == 1.0 else ("1.5" if x == 1.5 else "2.5"))
            for x in scales]
    rec = [pub["runs"][k]["summary"]["recovery_fraction"] for k in keys]
    spur_rot = [pub["runs"][k]["summary"]["expected_spurious_rotation"] for k in keys]
    spur_off = [pub["runs"][k]["summary"]["expected_spurious_offset"] for k in keys]
    n_truth = pub["gate"]["n_truth"]

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.6))

    ax = axes[0]
    ax.plot(scales, rec, marker="o", color="#1f4e9c", lw=1.8,
            label="recovery fraction")
    ax.set_ylim(0.7, 1.03)
    ax.set_xlabel("match radius scale")
    ax.set_ylabel("recovered fraction of %d counterparts" % n_truth)
    ax.grid(alpha=0.15)
    ax2 = ax.twinx()
    ax2.plot(scales, spur_rot, marker="s", ls="--", color="#b3261e", lw=1.4,
             label="expected spurious (rotation)")
    ax2.plot(scales, spur_off, marker="^", ls=":", color="#c2571a", lw=1.4,
             label="expected spurious (offset)")
    ax2.set_ylabel("expected spurious matches over the probe set")
    ax2.set_ylim(0.0, 2.8)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower right", fontsize=8, frameon=False)

    ax = axes[1]
    run = pub["runs"]["radius_scale_1.0"]["matches"]
    miss_ids = {m["probe"] for m in pub["gate"]["misses"]}
    for m in run:
        sep = m["separation_arcsec"]
        rad = m.get("match_radius_arcsec")
        if rad is None:
            by = [x for x in pub["runs"]["radius_scale_2.5"]["matches"]
                  if x["probe"] == m["probe"]]
            rad = (by[0]["match_radius_arcsec"] / 2.5) if by and by[0]["match_radius_arcsec"] else None
        if rad is None:
            continue
        hit = m["probe"] not in miss_ids
        ax.scatter([rad], [sep], s=42,
                   marker="o" if hit else "X",
                   color="#1f4e9c" if hit else "#b3261e", zorder=5)
        if not hit:
            ax.annotate(m["probe"], (rad, sep), textcoords="offset points",
                        xytext=(6, 2), fontsize=9, color="#b3261e")
    lim = np.linspace(0.0, 0.78, 20)
    ax.plot(lim, lim, color="k", lw=1.0, ls="--")
    ax.set_xlim(0.24, 0.44)
    ax.set_ylim(0.0, 0.72)
    ax.annotate("dashed: separation $=$ match radius\n"
                "above it, missed at scale 1.0",
                (0.435, 0.71), fontsize=8, ha="right", va="top")
    ax.set_xlabel("match radius at scale 1.0 (arcsec)")
    ax.set_ylabel("separation from radio position (arcsec)")
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fG_expand_control.png"), dpi=200)
    plt.close(fig)

    out = {
        "item": "G-5",
        "n_truth": n_truth,
        "gate_passed": pub["gate"]["passed"],
        "ladder": [{"radius_scale": sc_, "recovery_fraction": r,
                    "n_recovered": int(round(r * n_truth)),
                    "expected_spurious_rotation": a,
                    "expected_spurious_offset": b}
                   for sc_, r, a, b in zip(scales, rec, spur_rot, spur_off)],
        "misses_at_scale_1": pub["gate"]["misses"],
        "purity_note": ("expected spurious counts are summed false-association "
                        "probabilities over the whole probe set, so at scale 1.0 "
                        "the recovered set of %d carries an expected %.2f (rotation) "
                        "or %.2f (offset) false entries."
                        % (int(round(rec[0] * n_truth)), spur_rot[0], spur_off[0])),
        "caveat": ("the control catalogue was itself registered onto the radio frame "
                   "using X-ray detections of 19 of these MSPs, so this is an "
                   "optimistic bound on match performance."),
    }
    _w("fG_expand_control.json", out)
    return out


# ---------------------------------------------------------------------------
# LaTeX table bodies, so the manuscript rows are regenerable rather than typed
# ---------------------------------------------------------------------------

FLAG_KEY = {"new_source": "n", "variable_candidate": "v", "low_counts": "l",
            "outside_ellipse": "e", "large_error_circle": "x",
            "flux_ratio_flagged": "g", "outer_aperture": "o"}


def latex_tables(targets, variability):
    rows = []
    for r in targets["candidates"][:targets["top_n_printed_in_paper"]]:
        fl = "".join(sorted(FLAG_KEY[f] for f in r["flags"] if f in FLAG_KEY))
        if r["confirmed_msp_counterpart"]:
            fl = "c" + fl
        if r["box_anchor"]:
            fl = "a" + fl
        rows.append("%d & %s & %.0f & $%+.2f$ & %.1f & %.3f & %.1f & %.3f & %s \\\\"
                    % (r["rank"], r["id"], r["radius_arcsec"],
                       r["colour_log_soft_hard"], r["flux_soft_1e-19_W_m2"],
                       r["p_member"], 1000.0 * r["p_chance_used_max"], r["score"],
                       (fl if fl else "--")))
    with open(os.path.join(HERE, "_g4_table.tex"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")

    lad = ["%.1f & %d & %d & %d & %d \\\\"
           % (row["flux_ratio"], row["n_aperture_sources"], row["n_msp_like_pool"],
              row["n_aperture_sources_no_validity_cut"],
              row["n_msp_like_pool_no_validity_cut"])
           for row in variability["chandra"]["ladder"]]
    with open(os.path.join(HERE, "_g6_table.tex"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lad) + "\n")


if __name__ == "__main__":
    S = rebuild()
    print("G-1", g1_skymap(S)["n_registered_matches"], "registered matches drawn")
    print("G-2", g2_colourflux(S)["n_plotted"], "points plotted")
    print("G-5", json.dumps(g5_control(S)["ladder"]))
    g3 = g3_lognlogs(S)
    print("G-3", g3["summary"])
    g6 = g6_variability(S)
    print("G-6 ladder", json.dumps(g6["chandra"]["ladder"]))
    print("G-6 valid", g6["chandra"]["n_gaussian_valid"], "of",
          g6["chandra"]["n_aperture_sources_with_counts"])
    print("G-6 erosita", g6["erosita"]["n_aperture_sources_above_limit"],
          "above limit;", g6["erosita"]["n_aperture_sources_with_neighbour_inside_hew"],
          "blended")
    g3_figure(g3)
    t = g4_target_list(S)
    print("G-4 pool", t["n_pool"], "score range", t["score_range"])
    latex_tables(t, g6)
    print("wrote _g4_table.tex and _g6_table.tex")
    for r in t["candidates"][:20]:
        print(" %2d %-5s r=%6.1f Pm=%.3f Pch=%.4f S=%.4f %s"
              % (r["rank"], r["id"], r["radius_arcsec"], r["p_member"],
                 r["p_chance_used_max"], r["score"], ",".join(r["flags"])))
