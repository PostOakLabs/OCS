"""Q5: the proper-motion window used for field counts, re-derived at 0.253.

Row 5 (window) and part of row 19 of the DS-01 rigor campaign. The draft's
field count uses a PM-offset circle of 1.2 mas/yr with bp_rp < 0.4 and
18 <= G <= 20. This script re-derives the radius at the measured dispersion,
reports the half-width a downstream lane should use, and counts what the two
windows contain in the Gaia cone.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

R_OLD = 1.2
SIGMA_OLD = 0.65
SIGMA_NEW = 0.253
BPRP_MAX = 0.4
G_LO, G_HI = 18.0, 20.0


def poisson_interval(k, z=1.959963985):
    if k == 0:
        return [0.0, float(0.5 * z * z)]
    lo = k * (1 - 1 / (9 * k) - z / (3 * np.sqrt(k))) ** 3
    hi = (k + 1) * (1 - 1 / (9 * (k + 1)) + z / (3 * np.sqrt(k + 1))) ** 3
    return [float(max(lo, 0.0)), float(hi)]


def main():
    v = C.vb21()
    i = int(np.where(v["source_id"] == C.TARGET_ID)[0][0])
    memb = v["memberprob"] >= 0.9
    cov_v = C.cov2(v["pmrae"], v["pmdece"], v["pmcorr"])
    y_v = np.stack([v["pmra"], v["pmdec"]], axis=-1)
    mu_g, _ = C.wmean(cov_v[memb], y_v[memb])

    f_old = 1.0 - np.exp(-R_OLD ** 2 / (2 * SIGMA_OLD ** 2))
    r_fixed_containment = SIGMA_NEW * np.sqrt(2 * np.log(1.0 / (1.0 - f_old)))
    k_old = R_OLD / SIGMA_OLD
    r_fixed_k = k_old * SIGMA_NEW
    r_2sigma = 2.0 * SIGMA_NEW
    r_3sigma = 3.0 * SIGMA_NEW

    g = C.gaia_cone()
    ok = (np.isfinite(g["pmra"]) & np.isfinite(g["pmdec"])
          & np.isfinite(g["phot_g_mean_mag"]) & np.isfinite(g["bp_rp"]))
    d = np.stack([g["pmra"] - mu_g[0], g["pmdec"] - mu_g[1]], axis=-1)
    r_pm = np.hypot(d[:, 0], d[:, 1])
    phot = (g["bp_rp"] < BPRP_MAX) & (g["phot_g_mean_mag"] >= G_LO) & (g["phot_g_mean_mag"] <= G_HI)
    base = ok & phot

    def counts(radius):
        inwin = base & (r_pm < radius)
        return {"full_cone": int(inwin.sum()),
                "full_cone_poisson95": poisson_interval(int(inwin.sum())),
                "annulus_25_31": int((inwin & (g["r_arcmin"] >= 25) & (g["r_arcmin"] <= 31)).sum()),
                "annulus_24_32": int((inwin & (g["r_arcmin"] >= 24) & (g["r_arcmin"] <= 32)).sum()),
                "annulus_26_30": int((inwin & (g["r_arcmin"] >= 26) & (g["r_arcmin"] <= 30)).sum())}

    area_full = np.pi * (35.0 / 60.0) ** 2  # deg^2
    area_ann = np.pi * ((31.0 ** 2 - 25.0 ** 2)) / 3600.0

    out = {
        "old_window": {"radius_mas_yr": R_OLD, "bp_rp_max": BPRP_MAX,
                       "g_range": [G_LO, G_HI], "sigma_assumed": SIGMA_OLD,
                       "k_sigma": k_old,
                       "enclosed_member_fraction_rayleigh": f_old,
                       "source": "D60 referee report F9; draft line 14"},
        "new_window": {
            "sigma_measured": SIGMA_NEW,
            "radius_fixed_containment_mas_yr": float(r_fixed_containment),
            "radius_fixed_k_mas_yr": float(r_fixed_k),
            "radius_2sigma_mas_yr": float(r_2sigma),
            "radius_3sigma_mas_yr": float(r_3sigma),
            "k_sigma_at_measured_dispersion": float(R_OLD / SIGMA_NEW),
            "recommended_half_width_mas_yr": float(r_fixed_containment),
            "recommended_basis": "fixed member containment (81.8 per cent), the quantity a field count needs",
        },
        "area": {"full_cone_deg2": float(area_full),
                 "annulus_25_31_deg2": float(area_ann)},
        "counts": {
            "old_1p2": counts(R_OLD),
            "new_fixed_containment": counts(r_fixed_containment),
            "new_2sigma": counts(r_2sigma),
            "new_3sigma": counts(r_3sigma),
        },
        "expected_field_count": {
            "quoted_0p05": 0.05,
            "area_ratio": float((r_fixed_containment / R_OLD) ** 2),
            "rescaled": float(0.05 * (r_fixed_containment / R_OLD) ** 2),
            "rescaled_2sigma": float(0.05 * (r_2sigma / R_OLD) ** 2),
            "rescaled_3sigma": float(0.05 * (r_3sigma / R_OLD) ** 2),
        },
        "target_in_windows": {
            "offset_mas_yr": float(np.hypot(*(y_v[i] - mu_g))),
            "inside_old_1p2": bool(np.hypot(*(y_v[i] - mu_g)) < R_OLD),
            "inside_new_fixed_containment": bool(np.hypot(*(y_v[i] - mu_g)) < r_fixed_containment),
        },
    }
    path = C.write_json("q5_window.json", out)
    print("wrote", path)
    print("R_new fixed containment", round(r_fixed_containment, 4),
          "fixed k", round(r_fixed_k, 4))
    for kk, vv in out["counts"].items():
        print(kk, vv)


if __name__ == "__main__":
    main()
