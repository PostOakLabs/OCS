"""Q2: matched-sample Monte Carlo for DS-01's offset percentile.

Row 1 of the DS-01 rigor campaign. Builds the chi2 of every VB21 member at
matched magnitude (18.5 <= G <= 19.5) and radius (25-31 arcmin), each with its
own errors and correlation, then reports where DS-01 sits in that distribution
under two readings: the empirical percentile and a parametric Monte Carlo that
includes the measurement noise of the matched stars.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SIGMAS = [0.253, 0.31, 0.54, 0.65]
NDRAW = 200


def wilson(k, n, z=1.959963985):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1.0 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (float(mid - half), float(mid + half))


def main():
    rng = np.random.default_rng(C.SEED)
    v = C.vb21()
    i = int(np.where(v["source_id"] == C.TARGET_ID)[0][0])

    memb = v["memberprob"] >= 0.9
    cov_all = C.cov2(v["pmrae"], v["pmdece"], v["pmcorr"])
    y_all = np.stack([v["pmra"], v["pmdec"]], axis=-1)
    mu_g, C_g = C.wmean(cov_all[memb], y_all[memb])

    sel = (memb
           & (v["g"] >= 18.5) & (v["g"] <= 19.5)
           & (v["r_arcmin"] >= 25.0) & (v["r_arcmin"] <= 31.0))
    n = int(sel.sum())
    delta = y_all[sel] - mu_g
    covs = cov_all[sel]

    out = {"sample": {
        "n": n,
        "g_range": [18.5, 19.5],
        "r_arcmin": [25.0, 31.0],
        "memberprob_min": 0.9,
        "g_median": float(np.median(v["g"][sel])),
        "r_median_arcmin": float(np.median(v["r_arcmin"][sel])),
    }, "rows": []}

    ds = y_all[i] - mu_g
    ds_cov = cov_all[i]

    for sg in SIGMAS:
        # chi2 of every matched member
        cov = covs + C_g + sg ** 2 * np.eye(2)
        chi2_m = np.einsum("ni,nij,nj->n", delta, np.linalg.inv(cov), delta)
        chi2_s = C.chi2_2d(ds, ds_cov + C_g + sg ** 2 * np.eye(2))

        k = int(np.sum(chi2_m >= chi2_s))
        pct = k / n
        lo, hi = wilson(k, n)

        # parametric Monte Carlo: draws from each star's measurement
        # distribution about the cluster mean, with the same covariance used in
        # chi2. The null is "a member like the others", so the intrinsic
        # dispersion is part of the draw; a draw without it would test the
        # narrower null "a star sitting exactly at the cluster mean" and is
        # reported separately as pct_mc_at_mean.
        draws = rng.multivariate_normal(np.zeros(2), np.eye(2), size=(n, NDRAW))
        L = np.linalg.cholesky(cov)
        sim = np.einsum("nij,nkj->nki", L, draws)
        chi2_sim = np.einsum("nki,nij,nkj->nk", sim, np.linalg.inv(cov), sim)
        pct_mc = float(np.mean(chi2_sim.ravel() >= chi2_s))

        L0 = np.linalg.cholesky(covs + C_g)
        sim0 = np.einsum("nij,nkj->nki", L0, draws)
        chi2_sim0 = np.einsum("nki,nij,nkj->nk", sim0, np.linalg.inv(cov), sim0)
        pct_mc0 = float(np.mean(chi2_sim0.ravel() >= chi2_s))

        # offset magnitude percentile, a second statistic on the same sample
        r_m = np.hypot(delta[:, 0], delta[:, 1])
        r_s = float(np.hypot(*ds))
        k_r = int(np.sum(r_m >= r_s))

        out["rows"].append({
            "sigma_int": sg,
            "chi2_target": chi2_s,
            "n_at_least": k,
            "percentile_empirical": pct,
            "percentile_wilson95": [lo, hi],
            "percentile_parametric_mc": pct_mc,
            "percentile_parametric_mc_at_mean": pct_mc0,
            "offset_target_mas_yr": r_s,
            "offset_median_mas_yr": float(np.median(r_m)),
            "offset_p16_mas_yr": float(np.percentile(r_m, 16)),
            "offset_p84_mas_yr": float(np.percentile(r_m, 84)),
            "offset_percentile_empirical": k_r / n,
            "offset_percentile_wilson95": list(wilson(k_r, n)),
        })

    path = C.write_json("q2_mc.json", out)
    print("wrote", path, "n =", n)
    for r in out["rows"]:
        print(f"sigma={r['sigma_int']:.3f} chi2={r['chi2_target']:.3f} "
              f"pct_emp={r['percentile_empirical']:.3f} "
              f"[{r['percentile_wilson95'][0]:.3f},{r['percentile_wilson95'][1]:.3f}] "
              f"pct_mc={r['percentile_parametric_mc']:.3f} "
              f"off_pct={r['offset_percentile_empirical']:.3f}")


if __name__ == "__main__":
    main()
