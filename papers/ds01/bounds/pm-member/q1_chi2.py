"""Q1: chi-square of DS-01's proper-motion offset under four dispersions.

Rows 1 and 2 of the DS-01 rigor campaign. Reads the VB21 catalogue, forms the
offset against three cluster means, and evaluates chi2 with the full 2x2
covariance of the measurement, the covariance of the mean, and an isotropic
intrinsic dispersion. Also reports the radial/tangential split, the rotation
term at DS-01's position angle, the local-minus-global difference and the
perspective correction.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SIGMAS = [0.253, 0.31, 0.54, 0.65]
NBOOT = 1000


def main():
    rng = np.random.default_rng(C.SEED)
    v = C.vb21()
    i = int(np.where(v["source_id"] == C.TARGET_ID)[0][0])

    s_ra, s_dec = float(v["pmra"][i]), float(v["pmdec"][i])
    sa, sd = float(v["pmrae"][i]), float(v["pmdece"][i])
    rho = float(v["pmcorr"][i])
    Cs = C.cov2(sa, sd, rho)
    mu_s = np.array([s_ra, s_dec])
    r_target = float(v["r_deg"][i])

    # --- member sets -------------------------------------------------------
    memb = v["memberprob"] >= 0.9
    loc = memb & (v["r_arcmin"] >= 25.0) & (v["r_arcmin"] <= 31.0)
    cov_all = C.cov2(v["pmrae"], v["pmdece"], v["pmcorr"])
    y_all = np.stack([v["pmra"], v["pmdec"]], axis=-1)

    mu_glob, C_glob = C.wmean(cov_all[memb], y_all[memb])
    mu_loc, C_loc = C.wmean(cov_all[loc], y_all[loc])

    # bootstrap covariance of each mean over member resamples
    def boot_cov(sel, n=NBOOT):
        idx = np.where(sel)[0]
        draws = np.empty((n, 2))
        for k in range(n):
            pick = rng.choice(idx, size=idx.size, replace=True)
            draws[k], _ = C.wmean(cov_all[pick], y_all[pick])
        return np.cov(draws, rowvar=False), draws

    Cb_glob, _ = boot_cov(memb)
    Cb_loc, _ = boot_cov(loc)
    Cc_glob = C_glob + Cb_glob
    Cc_loc = C_loc + Cb_loc

    # --- rotation fit ------------------------------------------------------
    er, et, r_rad = C.unit_vectors(v["x"], v["y"])
    # tangential velocity relative to the global mean
    d_all = y_all - mu_glob
    vt = np.einsum("nj,nj->n", d_all, et)
    sig_t = np.sqrt(np.einsum("nj,njk,nk->n", et, cov_all, et))

    bins = np.arange(25.0, 32.0, 1.0)
    rot_rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        sel = memb & (v["r_arcmin"] >= lo) & (v["r_arcmin"] < hi)
        if sel.sum() < 50:
            continue
        phi = np.arctan2(v["y"][sel], v["x"][sel])
        w = 1.0 / (sig_t[sel] ** 2 + 0.253 ** 2)
        X = np.stack([np.cos(phi), np.sin(phi)], axis=-1)
        A = np.einsum("n,ni,nj->ij", w, X, X)
        b = np.einsum("n,ni,n->i", w, X, vt[sel])
        a1, a2 = np.linalg.solve(A, b)
        amp = float(np.hypot(a1, a2))
        phi0 = float(np.arctan2(-a1, a2))
        resid = vt[sel] - (a1 * np.cos(phi) + a2 * np.sin(phi))
        rot_rows.append({"r_lo": float(lo), "r_hi": float(hi), "n": int(sel.sum()),
                         "amp": amp, "phi0_deg": float(np.degrees(phi0)),
                         "rms": float(np.sqrt(np.average(resid ** 2, weights=w)))})

    # interpolate the amplitude to DS-01's radius
    rr = np.array([0.5 * (r["r_lo"] + r["r_hi"]) for r in rot_rows])
    aa = np.array([r["amp"] for r in rot_rows])
    amp_target = float(np.interp(r_target * 60.0, rr, aa))

    phi_s = float(np.arctan2(v["y"][i], v["x"][i]))
    # phase at the target radius: use the nearest bin's phi0
    j = int(np.argmin(np.abs(rr - r_target * 60.0)))
    phi0 = np.radians(rot_rows[j]["phi0_deg"])
    et_s = et[i]
    rot_vec = amp_target * np.sin(phi_s - phi0) * et_s

    # single global fit over 25-31 arcmin as an independent check
    selw = memb & (v["r_arcmin"] >= 25.0) & (v["r_arcmin"] <= 31.0)
    phi_w = np.arctan2(v["y"][selw], v["x"][selw])
    w = 1.0 / (sig_t[selw] ** 2 + 0.253 ** 2)
    X = np.stack([np.cos(phi_w), np.sin(phi_w)], axis=-1)
    A = np.einsum("n,ni,nj->ij", w, X, X)
    b = np.einsum("n,ni,n->i", w, X, vt[selw])
    g1, g2 = np.linalg.solve(A, b)
    glob_amp = float(np.hypot(g1, g2))
    glob_phi0 = float(np.degrees(np.arctan2(-g1, g2)))

    mu_loc_rot = mu_loc + rot_vec

    # cross-check against the archive's own rotation profile (third of six
    # columns, the median); the profile is only read, never used as an input
    prof = C.profile()
    prof_rot_median = float(np.interp(r_target, prof["r_deg"], prof["rot"][:, 2]))
    prof_disp_median = float(np.interp(r_target, prof["r_deg"], prof["disp"][:, 2]))

    # --- perspective -------------------------------------------------------
    theta = np.array([v["x"][i], v["y"][i]])  # deg
    theta_rad = np.radians(theta)
    D_pc = C.D_SSOT_KPC * 1000.0
    persp_vec = -(C.RV_SYS / D_pc) * theta_rad * 4.7405  # mas/yr
    persp_mag = float(np.hypot(*persp_vec))

    # --- chi-square grid ---------------------------------------------------
    means = {
        "global": (mu_glob, Cc_glob),
        "local_25_31": (mu_loc, Cc_loc),
        "local_rotation_corrected": (mu_loc_rot, Cc_loc),
    }
    table = []
    for name, (mu_c, Cc) in means.items():
        delta = mu_s - mu_c
        for sg in SIGMAS:
            cov = Cs + Cc + sg ** 2 * np.eye(2)
            chi2 = C.chi2_2d(delta, cov)
            table.append({
                "mean": name,
                "sigma_int": sg,
                "chi2": chi2,
                "dof": 2,
                "p": C.p_two_dof(chi2),
                "z_equiv": C.z_from_chi2(chi2),
                "offset_mas_yr": float(np.hypot(*delta)),
                "delta_pmra": float(delta[0]),
                "delta_pmdec": float(delta[1]),
            })

    # --- radial / tangential ----------------------------------------------
    delta = mu_s - mu_loc
    rt = []
    for label, e in (("radial", er[i]), ("tangential", et[i])):
        proj = float(delta @ e)
        var = float(e @ (Cs + Cc_loc) @ e)
        rt.append({"component": label, "offset": proj, "sigma": float(np.sqrt(var)),
                   "z": proj / np.sqrt(var), "chi2_1dof": proj ** 2 / var,
                   "unit_vector": [float(e[0]), float(e[1])]})

    # --- local minus global -----------------------------------------------
    d_lg = mu_loc - mu_glob
    C_lg = Cc_loc + Cc_glob
    chi2_lg = C.chi2_2d(d_lg, C_lg)

    out = {
        "target": {
            "source_id": C.TARGET_ID,
            "pmra": s_ra, "pmdec": s_dec,
            "pmrae": sa, "pmdece": sd, "pmcorr": rho,
            "r_deg": r_target, "r_arcmin": r_target * 60.0,
            "position_angle_deg": float(np.degrees(phi_s)),
            "memberprob_vb21": float(v["memberprob"][i]),
            "qflag": int(v["qflag"][i]),
        },
        "means": {
            "global": {"pmra": float(mu_glob[0]), "pmdec": float(mu_glob[1]),
                       "n_members": int(memb.sum()),
                       "sigma_ra": float(np.sqrt(Cc_glob[0, 0])),
                       "sigma_dec": float(np.sqrt(Cc_glob[1, 1])),
                       "cov": Cc_glob.tolist()},
            "local_25_31": {"pmra": float(mu_loc[0]), "pmdec": float(mu_loc[1]),
                            "n_members": int(loc.sum()),
                            "sigma_ra": float(np.sqrt(Cc_loc[0, 0])),
                            "sigma_dec": float(np.sqrt(Cc_loc[1, 1])),
                            "cov": Cc_loc.tolist()},
            "local_rotation_corrected": {"pmra": float(mu_loc_rot[0]),
                                         "pmdec": float(mu_loc_rot[1]),
                                         "cov": Cc_loc.tolist()},
        },
        "chi2_grid": table,
        "chi2_measurement_only": {
            "note": "sigma_int = 0, the basis the draft quotes as 4.2",
            "local_25_31": C.chi2_2d(mu_s - mu_loc, Cs + Cc_loc),
            "global": C.chi2_2d(mu_s - mu_glob, Cs + Cc_glob),
        },
        "radial_tangential": rt,
        "rotation": {
            "bins": rot_rows,
            "amplitude_at_target": amp_target,
            "phi0_deg_nearest_bin": float(np.degrees(phi0)),
            "vector_at_target": [float(rot_vec[0]), float(rot_vec[1])],
            "magnitude_at_target": float(np.hypot(*rot_vec)),
            "global_fit_25_31": {"amplitude": glob_amp, "phi0_deg": glob_phi0,
                                 "n": int(selw.sum())},
            "profile_median_third_of_six": prof_rot_median,
        },
        "local_minus_global": {
            "delta": [float(d_lg[0]), float(d_lg[1])],
            "magnitude": float(np.hypot(*d_lg)),
            "in_local_dispersion": float(np.hypot(*d_lg) / 0.253),
            "chi2": chi2_lg,
            "p": C.p_two_dof(chi2_lg),
        },
        "perspective": {
            "v_los_km_s": C.RV_SYS,
            "distance_kpc": C.D_SSOT_KPC,
            "theta_deg": r_target,
            "vector": [float(persp_vec[0]), float(persp_vec[1])],
            "magnitude": persp_mag,
            "fraction_of_dispersion": persp_mag / 0.253,
            "delta_chi2_at_0p253": None,
        },
    }

    # effect of each correction on chi2 at the headline dispersion
    def chi2_at(mu_c, sg):
        return C.chi2_2d(mu_s - mu_c, Cs + Cc_loc + sg ** 2 * np.eye(2))

    base = chi2_at(mu_loc, 0.253)
    out["perspective"]["delta_chi2_at_0p253"] = chi2_at(mu_loc + persp_vec, 0.253) - base
    out["rotation"]["delta_chi2_at_0p253"] = chi2_at(mu_loc_rot, 0.253) - base
    out["local_minus_global"]["delta_chi2_at_0p253"] = chi2_at(mu_glob, 0.253) - base

    path = C.write_json("q1_chi2.json", out)
    print("wrote", path)

    for row in table:
        print(f"{row['mean']:26s} sigma={row['sigma_int']:.3f} "
              f"chi2={row['chi2']:.3f} p={row['p']:.4f} "
              f"off={row['offset_mas_yr']:.3f}")
    print("radial/tangential:", [(r['component'], round(r['offset'], 3),
                                  round(r['z'], 2)) for r in rt])
    print("rotation amp at target", round(amp_target, 4),
          "vector", np.round(rot_vec, 4))
    print("perspective", np.round(persp_vec, 5), persp_mag)
    print("local-global", np.round(d_lg, 4), "chi2", round(chi2_lg, 3))


if __name__ == "__main__":
    main()
