"""Q6: eRASS rotation control at 5-degree steps under the re-derived window.

Row 19 of the DS-01 rigor campaign. Pairs eRASS:3 sources with Gaia DR3 stars,
keeps the pairs whose Gaia star passes the window of Q5, and rotates every
eRASS position about the cluster centre in 5-degree steps to see how often a
chance pair is at least as close as the real configuration.
"""
import os
import sys

import numpy as np
from astropy.table import Table
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

ERASS = r"C:\farm\cache\omegacen\omega-cen-erass-sweep\data\erass3_erass3-m_1p5deg.ecsv"
GAIA = r"C:\farm\cache\omegacen\omega-cen-erass-sweep\data\gaia_pmsel_1p5deg.ecsv"

PAIR_RADIUS_ARCSEC = 10.0
R_MAX_DEG = 1.4
STEP_DEG = 5.0
NROT = 21
BPRP_MAX = 0.4  # missing colours are stored as 0.0 and are excluded by the > 0 guard
G_LO, G_HI = 18.0, 20.0


def main():
    v = C.vb21()
    i = int(np.where(v["source_id"] == C.TARGET_ID)[0][0])
    memb = v["memberprob"] >= 0.9
    cov_v = C.cov2(v["pmrae"], v["pmdece"], v["pmcorr"])
    y_v = np.stack([v["pmra"], v["pmdec"]], axis=-1)
    mu_g, _ = C.wmean(cov_v[memb], y_v[memb])

    er = Table.read(ERASS)
    ga = Table.read(GAIA)

    cosd = np.cos(np.radians(C.CEN_DEC))
    ex = (np.asarray(er["RA_ICRS"]) - C.CEN_RA) * cosd
    ey = np.asarray(er["DE_ICRS"]) - C.CEN_DEC
    er_r = np.hypot(ex, ey)
    keep_e = er_r < R_MAX_DEG
    ex, ey = ex[keep_e], ey[keep_e]
    poserr = np.asarray(er["posErr"])[keep_e]
    ename = np.asarray(er["IAUName"])[keep_e]
    n_e = int(keep_e.sum())

    gx = (np.asarray(ga["ra"]) - C.CEN_RA) * cosd
    gy = np.asarray(ga["dec"]) - C.CEN_DEC
    g_r = np.hypot(gx, gy)
    keep_g = g_r < R_MAX_DEG
    gx, gy = gx[keep_g], gy[keep_g]
    gpm = np.stack([np.asarray(ga["pmra"])[keep_g], np.asarray(ga["pmdec"])[keep_g]], axis=-1)
    gg = np.asarray(ga["phot_g_mean_mag"])[keep_g]
    gbp = np.asarray(ga["bp_rp"])[keep_g]
    gid = np.asarray(ga["source_id"])[keep_g]
    n_g = int(keep_g.sum())

    area_deg2 = np.pi * R_MAX_DEG ** 2
    density = n_e / area_deg2  # sources per deg^2
    density_arcsec2 = density / 3600.0 ** 2

    gtree = cKDTree(np.column_stack([gx * 3600.0, gy * 3600.0]))  # arcsec

    def pairs(rot_deg, window):
        th = np.radians(rot_deg)
        ct, st = np.cos(th), np.sin(th)
        rx = (ex * ct - ey * st) * 3600.0
        ry = (ex * st + ey * ct) * 3600.0
        etree = cKDTree(np.column_stack([rx, ry]))
        out = []
        for ei, gi_list in enumerate(etree.query_ball_tree(gtree, PAIR_RADIUS_ARCSEC)):
            if not gi_list:
                continue
            for gi in gi_list:
                dpm = gpm[gi] - mu_g
                r_pm = float(np.hypot(*dpm))
                if r_pm >= window:
                    continue
                if not (0.0 < gbp[gi] < BPRP_MAX and G_LO <= gg[gi] <= G_HI):
                    continue
                sep = float(np.hypot(rx[ei] - gx[gi] * 3600.0,
                                     ry[ei] - gy[gi] * 3600.0))
                p = 1.0 - np.exp(-np.pi * sep ** 2 * density_arcsec2)
                out.append({"erass": str(ename[ei]), "gaia_id": int(gid[gi]),
                            "sep_arcsec": sep, "p": float(p),
                            "posErr": float(poserr[ei]),
                            "nsig": sep / float(poserr[ei]),
                            "r_pm": r_pm, "g": float(gg[gi]), "bp_rp": float(gbp[gi])})
        return out

    def summarise(window, label):
        real = pairs(0.0, window)
        real_min = min((p["p"] for p in real), default=1.0)
        control = []
        for k in range(NROT):
            pr = pairs(k * STEP_DEG, window)
            control.append(min((p["p"] for p in pr), default=1.0))
        control = np.array(control)
        rank = int(np.sum(control <= real_min))
        best = sorted(real, key=lambda p: p["p"])[:5]
        return {"label": label, "window_mas_yr": float(window),
                "n_pairs": len(real), "real_min_p": float(real_min),
                "control_min_p": control.tolist(),
                "control_median": float(np.median(control)),
                "n_control_at_least_as_close": rank,
                "n_rotations": NROT,
                "rank_fraction": rank / NROT,
                "best_pairs": best}

    windows = [0.4671, 1.2, 0.7587]
    results = [summarise(w, f"window_{w}") for w in windows]

    # rotation test for the DS-01 association alone, with no PM window: rotate
    # the same eRASS source and ask how often any Gaia star within the pair
    # radius gives a chance probability at least as small.
    ds_idx = None
    rx0 = ex * 3600.0
    ry0 = ey * 3600.0
    # locate the eRASS source nearest to DS-01 in the real configuration
    gsel = np.where(gid == C.TARGET_ID)[0]
    if gsel.size:
        dsep = np.hypot(rx0 - gx[gsel[0]] * 3600.0, ry0 - gy[gsel[0]] * 3600.0)
        ds_idx = int(np.argmin(dsep))

    target_test = None
    if ds_idx is not None:
        def min_p_for_source(theta_deg):
            th = np.radians(theta_deg)
            ct, st = np.cos(th), np.sin(th)
            rx = (ex[ds_idx] * ct - ey[ds_idx] * st) * 3600.0
            ry = (ex[ds_idx] * st + ey[ds_idx] * ct) * 3600.0
            idxs = gtree.query_ball_point([rx, ry], PAIR_RADIUS_ARCSEC)
            if not idxs:
                return 1.0, None
            best = 1.0
            bg = None
            for gi in idxs:
                sep = float(np.hypot(rx - gx[gi] * 3600.0, ry - gy[gi] * 3600.0))
                p = 1.0 - np.exp(-np.pi * sep ** 2 * density_arcsec2)
                if p < best:
                    best, bg = p, int(gid[gi])
            return best, bg

        real_p, real_g = min_p_for_source(0.0)
        ctl = [min_p_for_source(k * STEP_DEG)[0] for k in range(NROT)]
        target_test = {"erass_source": str(ename[ds_idx]),
                       "real_p": float(real_p), "real_gaia_id": real_g,
                       "control_p": ctl,
                       "n_control_at_least_as_close": int(np.sum(np.array(ctl) <= real_p)),
                       "n_rotations": NROT}

    out = {
        "inputs": {"erass_file": os.path.basename(ERASS), "gaia_file": os.path.basename(GAIA),
                   "n_erass_in_region": n_e, "n_gaia_in_region": n_g,
                   "r_max_deg": R_MAX_DEG, "area_deg2": float(area_deg2),
                   "erass_density_per_deg2": float(density),
                   "pair_radius_arcsec": PAIR_RADIUS_ARCSEC,
                   "step_deg": STEP_DEG, "n_rotations": NROT},
        "cluster_mean": [float(mu_g[0]), float(mu_g[1])],
        "results": results,
        "target_pair_rotation": target_test,
        "target_gaia_id": C.TARGET_ID,
    }
    path = C.write_json("q6_erass.json", out)
    print("wrote", path)
    for r in results:
        print(f"{r['label']:14s} n_pairs={r['n_pairs']:3d} min_p={r['real_min_p']:.3e} "
              f"rank={r['n_control_at_least_as_close']}/{NROT}")


if __name__ == "__main__":
    main()
