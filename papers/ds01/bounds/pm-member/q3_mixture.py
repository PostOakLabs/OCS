"""Q3: independent two-component mixture fit at 25-31 arcmin.

Row 4 of the DS-01 rigor campaign. Fits a cluster plus field mixture in proper
motion space to Gaia DR3 stars in the annulus, with each star's own 2x2
measurement covariance added to the component covariance. No proper-motion
pre-selection is applied, so the separation is made by the fit.

Variants: three annuli, two control rings (used to initialise and, in a second
pass, to fix the field component), and a quality subset that mimics the VB21
quality filter DS-01 fails.
"""
import os
import sys
import time

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

NRESTART = 3


def unpack(theta):
    """theta -> (pi0, m0, S0, m1, S1). Cholesky parameters keep S positive definite."""
    pi0 = 1.0 / (1.0 + np.exp(-theta[0]))
    out = []
    j = 1
    for _ in range(2):
        m = theta[j:j + 2]
        l11 = np.exp(theta[j + 2])
        l21 = theta[j + 3]
        l22 = np.exp(theta[j + 4])
        L = np.array([[l11, 0.0], [l21, l22]])
        out.append((m, L @ L.T))
        j += 5
    return pi0, out[0][0], out[0][1], out[1][0], out[1][1]


def pack(pi0, m0, S0, m1, S1):
    th = [np.log(pi0 / (1 - pi0))]
    for m, S in ((m0, S0), (m1, S1)):
        L = np.linalg.cholesky(S)
        th += [m[0], m[1], np.log(L[0, 0]), L[1, 0], np.log(L[1, 1])]
    return np.array(th)


def nll(theta, y, cov):
    pi0, m0, S0, m1, S1 = unpack(theta)
    comps = []
    for pi, m, S in ((pi0, m0, S0), (1 - pi0, m1, S1)):
        c = cov + S
        d = y - m
        sol = np.linalg.solve(c, d[..., None])[..., 0]
        quad = np.einsum("ni,ni->n", d, sol)
        _, logdet = np.linalg.slogdet(c)
        comps.append(np.log(pi) - 0.5 * (quad + logdet + 2 * np.log(2 * np.pi)))
    a = np.stack(comps, axis=1)
    mx = a.max(axis=1)
    return -float(np.sum(mx + np.log(np.exp(a - mx[:, None]).sum(axis=1))))


def fit(y, cov, starts):
    best = None
    for th0 in starts:
        res = minimize(nll, th0, args=(y, cov), method="L-BFGS-B",
                       options={"maxiter": 400})
        if best is None or res.fun < best.fun:
            best = res
    return best


def _nll_fixedmean(theta, y, cov, m1):
    """Cluster free, field mean fixed at the control-ring centroid."""
    pi0 = 1.0 / (1.0 + np.exp(-theta[0]))
    m0 = theta[1:3]
    L0 = np.array([[np.exp(theta[3]), 0.0], [theta[4], np.exp(theta[5])]])
    S0 = L0 @ L0.T
    L1 = np.array([[np.exp(theta[6]), 0.0], [theta[7], np.exp(theta[8])]])
    S1 = L1 @ L1.T
    comps = []
    for pi, m, S in ((pi0, m0, S0), (1 - pi0, m1, S1)):
        c = cov + S
        d = y - m
        sol = np.linalg.solve(c, d[..., None])[..., 0]
        quad = np.einsum("ni,ni->n", d, sol)
        _, logdet = np.linalg.slogdet(c)
        comps.append(np.log(pi) - 0.5 * (quad + logdet + 2 * np.log(2 * np.pi)))
    a = np.stack(comps, axis=1)
    mx = a.max(axis=1)
    return -float(np.sum(mx + np.log(np.exp(a - mx[:, None]).sum(axis=1))))


def posterior(theta, y, cov, m1=None):
    if m1 is None:
        pi0, m0, S0, m1_, S1 = unpack(theta)
        m1 = m1_
    else:
        pi0 = 1.0 / (1.0 + np.exp(-theta[0]))
        m0 = theta[1:3]
        L0 = np.array([[np.exp(theta[3]), 0.0], [theta[4], np.exp(theta[5])]])
        S0 = L0 @ L0.T
        L1 = np.array([[np.exp(theta[6]), 0.0], [theta[7], np.exp(theta[8])]])
        S1 = L1 @ L1.T
    comps = []
    for pi, m, S in ((pi0, m0, S0), (1 - pi0, m1, S1)):
        c = cov + S
        d = y - m
        sol = np.linalg.solve(c, d[..., None])[..., 0]
        quad = np.einsum("ni,ni->n", d, sol)
        _, logdet = np.linalg.slogdet(c)
        comps.append(np.log(pi) - 0.5 * (quad + logdet))
    a = np.stack(comps, axis=1)
    a -= a.max(axis=1, keepdims=True)
    p = np.exp(a)
    return p / p.sum(axis=1, keepdims=True)


def ring_stats(y, cov, mu, lo, hi):
    d = y - mu
    r = np.hypot(d[:, 0], d[:, 1])
    sel = (r >= lo) & (r < hi)
    m, c = C.wmean(cov[sel], y[sel])
    return m, c, int(sel.sum())


def main():
    t0 = time.time()
    v = C.vb21()
    i = int(np.where(v["source_id"] == C.TARGET_ID)[0][0])
    cov_v = C.cov2(v["pmrae"], v["pmdece"], v["pmcorr"])
    y_v = np.stack([v["pmra"], v["pmdec"]], axis=-1)
    memb = v["memberprob"] >= 0.9
    mu_g, C_g = C.wmean(cov_v[memb], y_v[memb])

    g = C.gaia_cone()
    ok = (np.isin(g["astrometric_params_solved"], [31, 95])
          & np.isfinite(g["pmra"]) & np.isfinite(g["pmdec"])
          & np.isfinite(g["pmra_error"]) & np.isfinite(g["pmdec_error"])
          & np.isfinite(g["phot_g_mean_mag"]) & np.isfinite(g["bp_rp"]))
    y = np.stack([g["pmra"], g["pmdec"]], axis=-1)
    cov = C.cov2(g["pmra_error"], g["pmdec_error"],
                 np.nan_to_num(g["pmra_pmdec_corr"], nan=0.0))

    ds_y = y_v[i]
    ds_cov = cov_v[i]

    def annulus(lo, hi):
        return ok & (g["r_arcmin"] >= lo) & (g["r_arcmin"] <= hi)

    rng = np.random.default_rng(C.SEED)

    def make_starts(n, seed_shift=0):
        r = np.random.default_rng(C.SEED + seed_shift)
        base = [pack(0.1, mu_g, np.diag([0.25 ** 2, 0.25 ** 2]),
                     mu_g + np.array([1.0, 1.0]), np.diag([1.5 ** 2, 1.5 ** 2]))]
        out = list(base)
        for _ in range(n - 1):
            pi = r.uniform(0.03, 0.4)
            m0 = mu_g + r.normal(0, 0.05, 2)
            m1 = mu_g + r.normal(0, 1.0, 2)
            S0 = np.diag(np.exp(r.normal(np.log(0.25 ** 2), 0.4, 2)))
            S1 = np.diag(np.exp(r.normal(np.log(1.2 ** 2), 0.4, 2)))
            out.append(pack(pi, m0, S0, m1, S1))
        return out

    variants = []
    for (lo, hi) in [(25.0, 31.0), (24.0, 32.0), (26.0, 30.0)]:
        sel = annulus(lo, hi)
        variants.append({"name": f"annulus_{lo:g}_{hi:g}", "sel": sel,
                         "rings": None, "fix": False})
    # control-ring variants on the primary annulus
    sel = annulus(25.0, 31.0)
    for (rlo, rhi) in [(1.5, 2.5), (3.0, 4.0)]:
        variants.append({"name": f"ring_{rlo:g}_{rhi:g}_free", "sel": sel,
                         "rings": (rlo, rhi), "fix": False})
        variants.append({"name": f"ring_{rlo:g}_{rhi:g}_fixed", "sel": sel,
                         "rings": (rlo, rhi), "fix": True})
    # quality subset
    qsel = sel & (np.nan_to_num(g["ipd_gof_harmonic_amplitude"], nan=1.0) < 0.1)
    variants.append({"name": "qflag_like", "sel": qsel, "rings": None, "fix": False})

    rows = []
    for var in variants:
        sel = var["sel"]
        ys, cs = y[sel], cov[sel]
        fixed_mean = None
        if var["rings"] is not None:
            m_ring, c_ring, n_ring = ring_stats(ys, cs, mu_g, *var["rings"])
            if var["fix"]:
                fixed_mean = m_ring
        starts = make_starts(NRESTART, seed_shift=len(rows))
        if fixed_mean is not None:
            # cluster free, field mean pinned at the ring centroid, field
            # covariance free. A ring is a shell, not a Gaussian, so its own
            # covariance is not a usable field covariance.
            th0 = np.array([np.log(0.1 / 0.9), mu_g[0], mu_g[1],
                            np.log(0.25), 0.0, np.log(0.25),
                            np.log(1.5), 0.0, np.log(1.5)])
            res = minimize(_nll_fixedmean, th0, args=(ys, cs, fixed_mean),
                           method="L-BFGS-B", options={"maxiter": 400})
            pi0 = 1.0 / (1.0 + np.exp(-res.x[0]))
            m0 = res.x[1:3]
            L0 = np.array([[np.exp(res.x[3]), 0.0], [res.x[4], np.exp(res.x[5])]])
            S0 = L0 @ L0.T
            L1 = np.array([[np.exp(res.x[6]), 0.0], [res.x[7], np.exp(res.x[8])]])
            S1 = L1 @ L1.T
            m1 = fixed_mean
            post = posterior(res.x, np.stack([ds_y]), np.stack([ds_cov]), m1=m1)[0]
            pmem = float(post[0])
            nllv = float(res.fun)
            conv = bool(res.success)
            pp = posterior(res.x, ys, cs, m1=m1)[:, 0]
            ncomp = [int(np.sum(pp >= 0.5)), int(np.sum(pp < 0.5))]
        else:
            res = fit(ys, cs, starts)
            pi0, m0, S0, m1, S1 = unpack(res.x)
            post = posterior(res.x, np.stack([ds_y]), np.stack([ds_cov]))[0]
            pmem = float(post[0])
            nllv = float(res.fun)
            conv = bool(res.success)
            # assignment counts at 0.5
            pp = posterior(res.x, ys, cs)[:, 0]
            ncomp = [int(np.sum(pp >= 0.5)), int(np.sum(pp < 0.5))]

        rows.append({
            "variant": var["name"],
            "n_stars": int(sel.sum()),
            "pi_cluster": float(pi0),
            "cluster_mean": [float(m0[0]), float(m0[1])],
            "cluster_sigma_major": float(np.sqrt(np.linalg.eigvalsh(S0).max())),
            "cluster_sigma_minor": float(np.sqrt(np.linalg.eigvalsh(S0).min())),
            "field_mean": [float(m1[0]), float(m1[1])],
            "field_sigma_major": float(np.sqrt(np.linalg.eigvalsh(S1).max())),
            "field_sigma_minor": float(np.sqrt(np.linalg.eigvalsh(S1).min())),
            "n_cluster_at_0p5": ncomp[0],
            "n_field_at_0p5": ncomp[1],
            "p_mem_ds01": pmem,
            "nll": nllv,
            "converged": conv,
            "ring": var["rings"],
            "field_fixed": bool(var["fix"]),
            "n_ring": (int(ring_stats(ys, cs, mu_g, *var["rings"])[2])
                       if var["rings"] is not None else None),
        })
        print(f"{var['name']:22s} n={rows[-1]['n_stars']:6d} "
              f"pi={pi0:.4f} Pmem={pmem:.4f} nll={nllv:.1f} "
              f"sig_c={rows[-1]['cluster_sigma_major']:.3f} "
              f"sig_f={rows[-1]['field_sigma_major']:.3f} "
              f"t={time.time()-t0:.0f}s", flush=True)

    out = {
        "target": {"source_id": C.TARGET_ID, "pmra": float(ds_y[0]),
                   "pmdec": float(ds_y[1]), "pmrae": float(np.sqrt(ds_cov[0, 0])),
                   "pmdece": float(np.sqrt(ds_cov[1, 1])),
                   "pmcorr": float(ds_cov[0, 1] / np.sqrt(ds_cov[0, 0] * ds_cov[1, 1]))},
        "global_mean_used_for_rings": [float(mu_g[0]), float(mu_g[1])],
        "cuts": {"astrometric_params_solved": [31, 95],
                 "annuli": [[25, 31], [24, 32], [26, 30]],
                 "rings": [[1.5, 2.5], [3.0, 4.0]],
                 "qflag_like_ipd_gof_max": 0.1},
        "n_cone_usable": int(ok.sum()),
        "n_restart": NRESTART,
        "variants": rows,
        "p_mem_range": [min(r["p_mem_ds01"] for r in rows),
                        max(r["p_mem_ds01"] for r in rows)],
        "vb21_memberprob": float(v["memberprob"][i]),
    }
    path = C.write_json("q3_mixture.json", out)
    print("wrote", path, "elapsed", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
