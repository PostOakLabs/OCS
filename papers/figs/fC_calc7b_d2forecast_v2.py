"""R9-C-1 / C-CALC-5 v2: D2 pulsar mock-population forecast, joint likelihood.

Supersedes fC_calc7b_d2forecast.py, which is retained unchanged so the v1
chain stays auditable.  Three defects are repaired here:

  C-R9-04 / C-B2   fit_family maximised and integrated the likelihood PER
                   PULSAR (sum_i log sum_k L_ki), which lets every pulsar
                   choose its own central mass.  The quantity D2 needs is the
                   common-potential one: max_k sum_i log L_ki for the profile
                   likelihood and logmean_k sum_i log L_ki for the evidence.
                   v1 also returned lmax and lnev differing only by a constant
                   for the extended family, so its "Delta chi^2" and its
                   "ln K" were the same number up to log(ngrid).
  C-R9-04 / C-R8-06  KMS2PC was 3.0857e11, its own comment said 3.086e-11,
                   and the correct conversion is 1 (km/s)^2/pc = 1e6/pc_in_m
                   = 3.2408e-11 m/s^2.  Gate G_A failed by ~22 dex and the
                   failure was never surfaced.  Cells are dimensionless in the
                   noise ladder, so the cell results are unaffected; the gate
                   is not.
  C-R9-03 / C-R8-05  only the truth-signed fixed-parameter statistic was
                   reported.  Both statistics are now written for both
                   truths, with the sign convention stated, and a third truth
                   is added whose extended component encloses the same mass as
                   the compact one at the median pulsar radius, so that cell
                   tests profile shape rather than enclosed mass.

The extended family (M, a) nests the compact family at a -> 0, so the
free-parameter comparison carries Delta dof = 1 at a parameter-space boundary.
The raw Delta chi^2 and an AIC-penalised version are both reported.

Read-only imports of the Paper H machinery, as in v1.
Output: paper/figs/fC_calc7b_d2forecast_v2.json
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
H_MOCK = os.path.join(HERE, os.pardir, "h", "mock")
H_FLAGD = os.path.join(HERE, os.pardir, "h", "flagd")
sys.path.insert(0, os.path.abspath(H_MOCK))
sys.path.insert(0, os.path.abspath(H_FLAGD))

import mock_cluster as mc          # read-only
import msp_density as md           # read-only

PC_M = 3.085677581e16
KMS2PC = 1.0e6 / PC_M              # 1 (km/s)^2/pc in m/s^2 = 3.2408e-11
DIST_KPC = 5.494
PC_PER_AMIN = DIST_KPC * 1000.0 * math.pi / (180.0 * 60.0)

SIGMA_LADDER = [3.09, 10.0, 31.6, 64.0, 200.0]      # (km/s)^2/pc
CENSUS = [19, 25, 40, 100]
N_REAL = 200
SEED0 = 20260824

Z_MAX, N_Z = 60.0, 301
Z = np.linspace(0.0, Z_MAX, N_Z)

M_PM = np.logspace(3.0, math.log10(3.0e5), 36)      # compact family grid
M_EXT = np.logspace(3.0, math.log10(6.0e5), 30)     # extended family, mass
A_EXT = np.logspace(-1.0, 1.0, 9)                   # extended family, scale
N_EXT = len(M_EXT) * len(A_EXT)

M_COMPACT, A_COMPACT = 2.0e4, 1.0e-4
M_EXTENDED, A_EXTENDED = 2.5e5, 2.0


def g_point(r, z):
    return z / r ** 3


def g_plummer(r, z, a_pc):
    return z / (r * r + a_pc * a_pc) ** 1.5


def logmvexp(x, axis):
    m = x.max(axis=axis, keepdims=True)
    return (m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True))).squeeze(axis)


def joint_stats(J):
    """J has shape (n_grid, n_pulsar) of per-pulsar log-marginals.
    Returns the common-potential profile maximum and the flat-prior
    log-evidence, both formed on the JOINT log-likelihood sum_i J[k, i]."""
    Jk = J.sum(axis=1)                       # joint log-likelihood per grid point
    return float(Jk.max()), float(logmvexp(Jk[None, :], 1)[0] - math.log(len(Jk)))


def main():
    with open(os.path.join(HERE, os.pardir, "h", "data", "pulsars.json"),
              encoding="utf-8") as f:
        psr = json.load(f)["pulsars"]
    R_real = np.array([p["theta"]["value"] * PC_PER_AMIN for p in psr])

    # --- gates -----------------------------------------------------------
    # G_A anchors the machinery to the number the paper prints at Section
    # sec:radio: "a 4e4 Msun point mass imposes a = 6e-8 m/s^2 at r = 0.3 pc".
    # v1 tested none of that: it used M = 2e4, put the test point at
    # (0.3, 0, 0.3) so |r| = 0.424 pc rather than 0.3, kept only the
    # z-projection, and left the visible mass in.  With the unit error fixed
    # but the construction left alone the gate still misses by 81 per cent, so
    # both defects have to be repaired for the gate to test anything.
    p_pm = mc.ClusterParams(M_dark=M_COMPACT, a_dark=A_COMPACT)
    p_gate = mc.ClusterParams(M_vis=0.0, M_dark=4.0e4, a_dark=A_COMPACT)
    a_g = mc.accel_los(np.array([[0.0, 0.0, 0.3]]), p_gate)
    a_m_s2 = float(abs(a_g[0]) * KMS2PC)
    gate_A = {"construction": "dark-only 4e4 Msun point mass, |a| at r = 0.3 pc",
              "a_0.3pc_m_s2": a_m_s2, "printed": 6e-8,
              "closed_form_m_s2": 6.674e-11 * 4.0e4 * 1.989e30 / (0.3 * PC_M) ** 2,
              "rel_err_vs_printed": abs(a_m_s2 - 6e-8) / 6e-8,
              "pass": bool(abs(a_m_s2 - 6e-8) / 6e-8 < 0.05),
              "v1_constant": 3.0857e11, "v1_comment_value": 3.086e-11,
              "v2_constant": KMS2PC}

    p_ext = mc.ClusterParams(M_dark=M_EXTENDED, a_dark=A_EXTENDED)
    rng0 = np.random.default_rng(1)
    r_draw = md.sample_r(2000, rng0, rc=md.RC_STAR_PC,
                         alpha=md.ALPHA_FIDUCIAL, r_max=8.0)
    nh = mc.random_directions(2000, rng0)
    a_ext = np.abs(mc.accel_los(r_draw[:, None] * nh, p_ext)) * KMS2PC
    # Two-sided now that the scale is right.  v1's version could only ever
    # fail if the maximum fell below 1e-9, which the 1e22 unit error made
    # impossible, so it was vacuous.  The printed 1e-9..4e-9 turns out to
    # bracket the MEDIAN, not the envelope, which spans nearly four decades.
    q = np.percentile(a_ext, [5, 50, 95])
    gate_B = {"envelope_min_m_s2": float(a_ext.min()),
              "envelope_max_m_s2": float(a_ext.max()),
              "p5_p50_p95_m_s2": [float(x) for x in q],
              "printed_bounds": [1e-9, 4e-9],
              "printed_brackets_median": bool(1e-9 < q[1] < 4e-9),
              "envelope_decades": float(math.log10(a_ext.max() / a_ext.min())),
              "pass": bool(1e-9 < q[1] < 4e-9)}

    # --- mass-matched extended truth -------------------------------------
    # Plummer(M, a = 2 pc) enclosing the same mass as the 2e4 point mass at
    # the median projected pulsar radius: M r^3/(r^2+a^2)^1.5 = M_compact.
    r_med = float(np.median(R_real))
    M_MATCHED = M_COMPACT * (r_med ** 2 + A_EXTENDED ** 2) ** 1.5 / r_med ** 3
    p_matched = mc.ClusterParams(M_dark=M_MATCHED, a_dark=A_EXTENDED)

    def build_set(R_pc):
        n = len(R_pc)
        a_vis = np.zeros((n, N_Z))
        w = np.zeros((n, N_Z))
        cdf = np.zeros((n, N_Z))
        g_pm = np.zeros((n, N_Z))
        g_ext = np.zeros((n, N_Z, len(A_EXT)))
        for i, R in enumerate(R_pc):
            r = np.sqrt(R * R + Z * Z)
            p0 = mc.ClusterParams()
            a_vis[i] = np.abs(mc.accel_los(
                np.column_stack([R * np.ones(N_Z), np.zeros(N_Z), Z]), p0))
            rho = np.array([mc.rho_tracer_norm(math.hypot(R, zz), p0)
                            for zz in Z])
            cdf[i] = np.cumsum(rho)
            cdf[i] /= cdf[i][-1]
            w[i] = rho / rho.sum()
            g_pm[i] = g_point(r, Z)
            for j, a_pc in enumerate(A_EXT):
                g_ext[i, :, j] = g_plummer(r, Z, a_pc)
        # g has shape (N_Z, n_a); g.T is (n_a, N_Z), so the product below is
        # (n_M, n_a, N_Z) and flattens to the same (M outer, a inner) ordering
        # v1 built by its double loop (asserted against that loop in tests).
        ext_models = np.stack([(M_EXT[:, None, None] * g.T[None, :, :]
                                ).reshape(N_EXT, N_Z) for g in g_ext])
        R2 = np.asarray(R_pc)[:, None] ** 2
        return {"R": R_pc, "a_vis": a_vis, "w": w, "cdf": cdf,
                "g_pm": g_pm, "g_ext": g_ext,
                "logw": np.log(w),
                "ext_models": ext_models,                       # (n, N_EXT, N_Z)
                "pm_models": M_PM[None, :, None] * g_pm[:, None, :],
                "simpleA": M_COMPACT * g_pm,                    # (n, N_Z)
                "simpleB": M_EXTENDED * Z[None, :]
                           / (R2 + Z[None, :] ** 2 + A_EXTENDED ** 2) ** 1.5}

    sets = {19: build_set(R_real)}
    rng_ext = np.random.default_rng(SEED0 - 1)
    for n in (25, 40, 100):
        r3 = md.sample_r(n - 19, rng_ext, rc=md.RC_STAR_PC,
                         alpha=md.ALPHA_FIDUCIAL, r_max=8.0)
        nh = mc.random_directions(n - 19, rng_ext)
        pos = r3[:, None] * nh
        R_add = np.hypot(pos[:, 0], pos[:, 1])
        sets[n] = build_set(np.concatenate([R_real, R_add]))

    def family_J(d, a_obs, sig, fam):
        """per-pulsar log-marginals over the line-of-sight position,
        shape (n_grid, n_pulsar).  Vectorised over pulsars: the residual is
        (n, n_grid, N_Z) and the z-marginal reduces the last axis, which is
        the same per-(pulsar, grid-point) reduction the per-pulsar loop did."""
        dd = a_obs[:, None] - d["a_vis"]                    # (n, N_Z)
        models = d["pm_models"] if fam == "pm" else d["ext_models"]
        res = dd[:, None, :] - models                       # (n, n_grid, N_Z)
        lp = -0.5 * (res / sig) ** 2 + d["logw"][:, None, :]
        return logmvexp(lp, 2).T                            # (n_grid, n)

    def dsimple_stat(d, a_obs, sig):
        """2(lnL_extended - lnL_compact) for the two NAMED potentials, no free
        parameters.  Signed positive toward EXTENDED for every truth; v1 signed
        it toward whichever family was true, which is why it always looked
        good regardless of what the data said."""
        dd = a_obs[:, None] - d["a_vis"]
        lA = logmvexp(-0.5 * ((dd - d["simpleA"]) / sig) ** 2 + d["logw"], 1)
        lB = logmvexp(-0.5 * ((dd - d["simpleB"]) / sig) ** 2 + d["logw"], 1)
        return 2.0 * (lB.sum() - lA.sum())

    # Per-cell checkpoint.  Each cell is seeded by its own index, so a resumed
    # run reproduces exactly what an uninterrupted one would have written.
    ckpt_path = os.path.join(HERE, "fC_calc7b_d2forecast_v2.ckpt.jsonl")
    done = {}
    if os.path.exists(ckpt_path):
        with open(ckpt_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    done[rec["cell"]] = rec["res"]
        print("resuming: %d cells already on disk" % len(done), flush=True)

    results = []
    cell = 0
    truths = (("compact", p_pm), ("extended", p_ext),
              ("extended_massmatched", p_matched))
    for truth_name, p_true in truths:
        M_true, a_true = p_true.M_dark, p_true.a_dark
        for sig in SIGMA_LADDER:
            for n in CENSUS:
                cell += 1
                if cell in done:
                    results.append(done[cell])
                    continue
                rng = np.random.default_rng(SEED0 + cell)
                d = sets[n]
                dchi, lnk, dsimple = [], [], []
                for _rep in range(N_REAL):
                    a_obs = np.zeros(n)
                    for i in range(n):
                        u = rng.uniform()
                        iz = min(int(np.searchsorted(d["cdf"][i], u)), N_Z - 1)
                        zz = Z[iz]
                        r = math.hypot(d["R"][i], zz)
                        g = (g_point(r, zz) if truth_name == "compact"
                             else g_plummer(r, zz, a_true))
                        a_obs[i] = (abs(d["a_vis"][i, iz]) + M_true * g
                                    + rng.normal(0.0, sig))
                    lpm_max, lpm_ev = joint_stats(family_J(d, a_obs, sig, "pm"))
                    lex_max, lex_ev = joint_stats(family_J(d, a_obs, sig, "ext"))
                    dchi.append(2.0 * (lex_max - lpm_max))
                    lnk.append(lex_ev - lpm_ev)
                    dsimple.append(dsimple_stat(d, a_obs, sig))
                dchi = np.array(dchi)
                lnk = np.array(lnk)
                dsimple = np.array(dsimple)
                ext_true = truth_name.startswith("extended")
                res = {
                    "truth": truth_name, "sigma": sig, "N": n,
                    "M_truth": M_true, "a_truth": a_true,
                    # sign convention: positive favours EXTENDED, all three
                    "median_dchi2_free": float(np.median(dchi)),
                    "median_dchi2_free_aic": float(np.median(dchi)) - 2.0,
                    "p_dchi2_free_sign_correct": float(
                        (dchi > 0).mean() if ext_true else (dchi < 0).mean()),
                    "median_lnK_free": float(np.median(lnk)),
                    "p_lnK_free_sign_correct": float(
                        (lnk > 0).mean() if ext_true else (lnk < 0).mean()),
                    "median_dsimple": float(np.median(dsimple)),
                    "p_dsimple_sign_correct": float(
                        (dsimple > 0).mean() if ext_true
                        else (dsimple < 0).mean()),
                    "p_dsimple_route_correct": float(
                        (dsimple >= 9.0).mean() if ext_true
                        else (dsimple <= -9.0).mean()),
                    "p_dsimple_inconclusive": float((np.abs(dsimple) < 9.0).mean()),
                }
                results.append(res)
                with open(ckpt_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"cell": cell, "res": res}) + "\n")
                print("[%2d/%2d] %-21s sig=%6.1f N=%3d  dchi2_free=%10.2f "
                      "sign=%.2f  dsimple=%12.2f route=%.2f"
                      % (cell, len(truths) * len(SIGMA_LADDER) * len(CENSUS),
                         truth_name, sig, n, res["median_dchi2_free"],
                         res["p_dchi2_free_sign_correct"],
                         res["median_dsimple"], res["p_dsimple_route_correct"]),
                      flush=True)

    out = {"_meta": {"script": "paper/figs/fC_calc7b_d2forecast_v2.py",
                     "supersedes": "fC_calc7b_d2forecast.py",
                     "N_REAL": N_REAL, "seed0": SEED0,
                     "sigma_ladder": SIGMA_LADDER, "census": CENSUS,
                     "truths": {"compact": {"M": M_COMPACT, "a_pc": A_COMPACT},
                                "extended": {"M": M_EXTENDED,
                                             "a_pc": A_EXTENDED},
                                "extended_massmatched": {
                                    "M": M_MATCHED, "a_pc": A_EXTENDED,
                                    "matched_at_r_pc": r_med}},
                     "sign_convention": "positive favours EXTENDED for all "
                                        "three statistics",
                     "delta_dof_free": 1,
                     "distance_kpc": DIST_KPC,
                     "KMS2PC": KMS2PC},
           "gates": {"G_A": gate_A, "G_B": gate_B},
           "cells": results}

    # G_C, provenance: the fixed-parameter statistic involves no fitting, so
    # if the rewrite left the data generation alone it must reproduce v1's
    # dsimple exactly, up to the sign convention v1 flipped by truth.  This is
    # what makes every v1 -> v2 change attributable to the likelihood repair.
    v1_path = os.path.join(HERE, "fC_calc7b_d2forecast.json")
    gate_C = {"checked": False}
    if os.path.exists(v1_path):
        with open(v1_path, encoding="utf-8") as f:
            v1 = json.load(f)["cells"]
        worst, npair = 0.0, 0
        for c1 in v1:
            for c2 in results:
                if (c1["truth"] == c2["truth"] and c1["sigma"] == c2["sigma"]
                        and c1["N"] == c2["N"]):
                    sgn = 1.0 if c1["truth"] == "extended" else -1.0
                    a, b = sgn * c1["median_dsimple"], c2["median_dsimple"]
                    worst = max(worst, abs(a - b) / max(abs(a), 1e-30))
                    npair += 1
        gate_C = {"checked": True, "n_cells_compared": npair,
                  "max_rel_diff": worst, "pass": bool(worst < 1e-12)}
    out["gates"]["G_C_v1_draw_provenance"] = gate_C

    with open(os.path.join(HERE, "fC_calc7b_d2forecast_v2.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("written fC_calc7b_d2forecast_v2.json")
    print("G_A", gate_A["pass"], "G_B", gate_B["pass"], "G_C", gate_C)
    for g, nm in ((gate_A, "G_A"), (gate_B, "G_B"), (gate_C, "G_C")):
        if not g.get("pass", True):
            raise SystemExit("GATE %s FAILED: %r" % (nm, g))


if __name__ == "__main__":
    main()
