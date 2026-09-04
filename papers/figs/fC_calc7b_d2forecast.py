"""R7-CALC-C2D / C-CALC-5: D2 pulsar mock-population forecast.

Pre-committed spec: 0xAlpha/results/R7-CALC-C2D.md section 0.1 (committed
before this script existed; seeds 20260824 + cell index).

Injects the compact (2e4 Msun point-mass) and extended (2.5e5 Msun, 2 pc
Plummer) potentials at the 19 real TRAPUM projected radii (+ synthetic
census extensions), marginalises unknown line-of-sight positions over the
tracer density (mock_cluster.rho_tracer_norm, read-only import), applies
Gaussian per-pulsar acceleration noise on a pre-committed ladder, and fits
both model families by profile likelihood + flat-prior evidence.

H machinery is imported READ-ONLY.  Output: paper/figs/fC_calc7b_d2forecast.json
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
H_MOCK = os.path.join(HERE, os.pardir, "h", "mock")
H_FLAGD = os.path.join(HERE, os.pardir, "h", "flagd")
sys.path.insert(0, os.path.abspath(H_MOCK))
sys.path.insert(0, os.path.abspath(H_FLAGD))

import mock_cluster as mc          # read-only
import msp_density as md           # read-only

YEAR = 3.15576e7
KMS2PC = 3.0857e11                 # 1 (km/s)^2/pc in m/s^2  -> 3.086e-11 m/s^2
DIST_KPC = 5.494
PC_PER_AMIN = DIST_KPC * 1000.0 * math.pi / (180.0 * 60.0)  # 5.494 kpc -> 1.598 pc per arcmin   # 1.5905 pc per arcmin

SIGMA_LADDER = [3.09, 10.0, 31.6, 64.0, 200.0]      # (km/s)^2/pc
CENSUS = [19, 25, 40, 100]
N_REAL = 200
SEED0 = 20260824

Z_MAX, N_Z = 60.0, 301
Z = np.linspace(0.0, Z_MAX, N_Z)

M_PM = np.logspace(3.0, math.log10(3.0e5), 36)      # compact family grid
M_EXT = np.logspace(3.0, math.log10(6.0e5), 30)     # extended family, mass
A_EXT = np.logspace(-1.0, 1.0, 9)                   # extended family, scale

G_PC = mc.G_PC  # machinery's own constant


def vis_enc(r):
    p0 = mc.ClusterParams()
    return mc.M_enc(r, p0) - 0.0  # dark = 0 default


def a_vis_of_r(r):
    p0 = mc.ClusterParams()
    return mc.accel_los(np.column_stack([r, np.zeros_like(r), np.zeros_like(r)]), p0)


def g_point(r, z):
    return z / r ** 3


def g_plummer(r, z, a_pc):
    return z / (r * r + a_pc * a_pc) ** 1.5


def main():
    # --- real positions -------------------------------------------------
    with open(os.path.join(HERE, os.pardir, "h", "data", "pulsars.json"),
              encoding="utf-8") as f:
        psr = json.load(f)["pulsars"]
    theta_am = [p["theta"]["value"] for p in psr]
    R_real = np.array([t * PC_PER_AMIN for t in theta_am])

    # --- gates -----------------------------------------------------------
    p_pm = mc.ClusterParams(M_dark=2e4, a_dark=1e-4)
    r_test = np.array([0.3])
    a_g = mc.accel_los(np.column_stack([r_test, np.zeros(1), r_test]), p_pm)
    a_m_s2 = float(abs(a_g[0]) * KMS2PC)
    gate_A = {"a_0.3pc_m_s2": a_m_s2, "printed": 6e-8,
              "pass": bool(abs(a_m_s2 - 6e-8) / 6e-8 < 0.05)}

    p_ext = mc.ClusterParams(M_dark=2.5e5, a_dark=2.0)
    rng0 = np.random.default_rng(1)
    r_draw = md.sample_r(2000, rng0, rc=md.RC_STAR_PC,
                         alpha=md.ALPHA_FIDUCIAL, r_max=8.0)
    nh = mc.random_directions(2000, rng0)
    pos = r_draw[:, None] * nh
    a_ext = np.abs(mc.accel_los(pos, p_ext)) * KMS2PC
    gate_B = {"envelope_min_m_s2": float(a_ext.min()),
              "envelope_max_m_s2": float(a_ext.max()),
              "printed_bounds_scale": "1e-9..4e-9",
              "pass": bool(a_ext.max() > 1e-9)}

    # --- precompute per-pulsar z-grids ----------------------------------
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
        return {"R": R_pc, "a_vis": a_vis, "w": w, "cdf": cdf,
                "g_pm": g_pm, "g_ext": g_ext}

    sets = {19: build_set(R_real)}
    rng_ext = np.random.default_rng(SEED0 - 1)
    for n in (25, 40, 100):
        r3 = md.sample_r(n - 19, rng_ext, rc=md.RC_STAR_PC,
                         alpha=md.ALPHA_FIDUCIAL, r_max=8.0)
        nh = mc.random_directions(n - 19, rng_ext)
        pos = r3[:, None] * nh
        R_add = np.hypot(pos[:, 0], pos[:, 1])
        sets[n] = build_set(np.concatenate([R_real, R_add]))

    def logmvexp(x, axis):
        m = x.max(axis=axis, keepdims=True)
        return (m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True))).squeeze(axis)

    def fit_family(d, a_obs, sig, fam):
        """profile lnL over grid + log-evidence; returns (lnL_max, ln_ev)."""
        n = len(a_obs)
        lnL = np.zeros(n)
        if fam == "pm":
            grid = M_PM
            for i in range(n):
                # model = a_vis + M * g_pm  ->  d = a_obs - a_vis
                dd = a_obs[i] - d["a_vis"][i]
                # ln N(dd; M g, sig) summed over z with weights w
                res = dd[None, :] - grid[:, None] * d["g_pm"][i][None, :]
                lp = -0.5 * (res / sig) ** 2 + np.log(d["w"][i])[None, :]
                lsum = logmvexp(lp, 1)
                lnL[i] = logmvexp(lsum[None, :], 1)[0]
            lmax = lnL.sum()
            # evidence over grid: mean of joint likelihood
            lj = np.zeros(len(grid))
            for i in range(n):
                pass
            # vectorised joint: shape (grid, n)
            J = np.zeros((len(grid), n))
            for i in range(n):
                dd = a_obs[i] - d["a_vis"][i]
                res = dd[None, :] - grid[:, None] * d["g_pm"][i][None, :]
                lp = -0.5 * (res / sig) ** 2 + np.log(d["w"][i])[None, :]
                J[:, i] = logmvexp(lp, 1)
            lnev = logmvexp(J, 0).sum() - math.log(len(grid))
            return lmax, lnev
        else:
            ngrid = len(M_EXT) * len(A_EXT)
            J = np.zeros((ngrid, n))
            for i in range(n):
                dd = a_obs[i] - d["a_vis"][i]
                # res[k, z] = dd - M*g for the k-th (M,a) pair
                k = 0
                res = np.empty((ngrid, N_Z))
                for jm, M in enumerate(M_EXT):
                    for ja, a_pc in enumerate(A_EXT):
                        res[k] = dd - M * d["g_ext"][i, :, ja]
                        k += 1
                lp = -0.5 * (res / sig) ** 2 + np.log(d["w"][i])[None, :]
                J[:, i] = logmvexp(lp, 1)
            lmax = logmvexp(J, 0).sum()
            lnev = logmvexp(J, 0).sum() - math.log(ngrid)
            return lmax, lnev

    # --- cells ------------------------------------------------------------
    results = []
    cell = 0
    for truth_name, p_true in (("compact", p_pm), ("extended", p_ext)):
        M_true, a_true = p_true.M_dark, p_true.a_dark
        for sig in SIGMA_LADDER:
            for n in CENSUS:
                cell += 1
                rng = np.random.default_rng(SEED0 + cell)
                d = sets[n]
                npsr = n
                dchi, lnk, correct = [], [], 0
                dsimple = []
                for rep in range(N_REAL):
                    a_obs = np.zeros(npsr)
                    for i in range(npsr):
                        u = rng.uniform()
                        iz = int(np.searchsorted(d["cdf"][i], u))
                        iz = min(iz, N_Z - 1)
                        zz = Z[iz]
                        r = math.hypot(d["R"][i], zz)
                        if truth_name == "compact":
                            g = g_point(r, zz)
                            a_t = abs(d["a_vis"][i, iz]) + M_true * g
                        else:
                            g = g_plummer(r, zz, a_true)
                            a_t = abs(d["a_vis"][i, iz]) + M_true * g
                        a_obs[i] = a_t + rng.normal(0.0, sig)
                    lpm_max, lpm_ev = fit_family(d, a_obs, sig, "pm")
                    lex_max, lex_ev = fit_family(d, a_obs, sig, "ext")
                    dchi.append(2.0 * (lex_max - lpm_max))
                    lnk.append(lex_ev - lpm_ev)
                    # Addendum A2: simple-vs-simple statistic between the two
                    # NAMED potentials (no free parameters) - the form the
                    # campaign paper's criterion language ("between the two
                    # potentials") actually specifies.
                    lA = 0.0
                    lB = 0.0
                    for i in range(npsr):
                        rA = np.sqrt(d["R"][i] ** 2 + Z * Z)
                        ddA = a_obs[i] - d["a_vis"][i] - 2.0e4 * d["g_pm"][i]
                        lpA = -0.5 * (ddA / sig) ** 2 + np.log(d["w"][i])
                        lA += logmvexp(lpA, 0)
                        gB = Z / (rA * rA + 4.0) ** 1.5
                        ddB = a_obs[i] - d["a_vis"][i] - 2.5e5 * gB
                        lpB = -0.5 * (ddB / sig) ** 2 + np.log(d["w"][i])
                        lB += logmvexp(lpB, 0)
                    dsimple.append(2.0 * (lA - lB) if truth_name == "compact"
                                   else 2.0 * (lB - lA))
                dchi = np.array(dchi)
                lnk = np.array(lnk)
                truth_is_ext = truth_name == "extended"
                res = {"truth": truth_name, "sigma": sig, "N": n,
                       "median_dchi2": float(np.median(dchi)),
                       "p_dchi2_ge9": float((dchi >= 9.0).mean()),
                       "median_lnK": float(np.median(lnk)),
                       "p_sign_correct": float((lnk > 0).mean() if truth_is_ext
                                               else (lnk < 0).mean()),
                       "median_dsimple": float(np.median(dsimple)),
                       "p_dsimple_ge9": float((np.array(dsimple) >= 9.0).mean())}
                results.append(res)
                print(f"[{cell}/40] {truth_name:8s} sig={sig:6.1f} N={n:3d} "
                      f"med_dchi2={res['median_dchi2']:9.2f} "
                      f"P(>=9)={res['p_dchi2_ge9']:.2f} "
                      f"med_lnK={res['median_lnK']:8.2f}", flush=True)

    out = {"_meta": {"script": "paper/figs/fC_calc7b_d2forecast.py",
                     "N_REAL": N_REAL, "seed0": SEED0,
                     "sigma_ladder": SIGMA_LADDER, "census": CENSUS,
                     "truths": {"compact": {"M": 2e4, "a_pc": 1e-4},
                                "extended": {"M": 2.5e5, "a_pc": 2.0}},
                     "distance_kpc": DIST_KPC},
           "gates": {"G_A": gate_A, "G_B": gate_B},
           "cells": results}
    with open(os.path.join(HERE, "fC_calc7b_d2forecast.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("written fC_calc7b_d2forecast.json")

if __name__ == "__main__":
    main()



