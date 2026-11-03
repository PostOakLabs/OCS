"""Q1: field-interloper density and expected count from the Gaia control cones.

Angle 1 of row 5. Counts stars in the frozen selection S in six control cones
at fixed galactic latitude, normalises by solid angle, and puts Poisson,
Jeffreys and bootstrap intervals on the expected count in the 25 to 30 arcmin
annulus.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from common import (A_ANN, A_ANN_B, A_CONE, AREA_RATIO, CONES, G_HI, G_LO,
                    MU_A, MU_D, RA_C, DEC_C, R_WIN, SEED, NBOOT, bootstrap_cones,
                    deg2, jeffreys_interval, load_annulus, load_gaia_cone,
                    poisson_interval, select_gaia, write_json)


def median_vpu(tab, mask):
    v = tab["visibility_periods_used"][mask]
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


def main():
    per_cone = []
    for dl, ra, dec in CONES:
        tab = load_gaia_cone(dl)
        n_all = len(tab["source_id"])
        five = (tab["astrometric_params_solved"] == 31) | \
               (tab["astrometric_params_solved"] == 95)
        vpu = median_vpu(tab, five & (tab["phot_g_mean_mag"] >= G_LO)
                         & (tab["phot_g_mean_mag"] <= G_HI))

        n_sel = int(select_gaia(tab).sum())
        n_old = int(select_gaia(tab, radius=1.2).sum())
        n_box = int((select_gaia(tab, radius=1e9)).sum())

        # factorised ingredients on 15 <= G <= 20
        g = tab["phot_g_mean_mag"]
        c = tab["bp_rp"]
        base = five & np.isfinite(g) & np.isfinite(c) & (g >= 15.0) & (g <= 20.0)
        n_base = int(base.sum())
        blue = base & (g >= G_LO) & (g <= G_HI) & (c > 0.0) & (c < 0.4)
        n_blue = int(blue.sum())
        pm_all = np.hypot(tab["pmra"] - MU_A, tab["pmdec"] - MU_D)
        n_pm = int((base & (pm_all <= R_WIN)).sum())
        blue15 = base & (c > 0.0) & (c < 0.4)
        n_blue15 = int(blue15.sum())
        n_pm_blue15 = int((blue15 & (pm_all <= R_WIN)).sum())

        per_cone.append(dict(dl=dl, ra=ra, dec=dec, n_all=n_all, med_vpu=vpu,
                             n_sel=n_sel, n_old_1p2=n_old, n_box=n_box,
                             n_base_15_20=n_base, n_blue=n_blue,
                             n_pm_all=n_pm, n_blue_15_20=n_blue15,
                             n_pm_blue_15_20=n_pm_blue15))

    counts = np.array([c["n_sel"] for c in per_cone], dtype=float)
    vpus = np.array([c["med_vpu"] for c in per_cone], dtype=float)
    f_w = vpus / np.nanmean(vpus)
    weights = f_w.copy()
    spread_vpu = float(np.nanmax(vpus) / np.nanmin(vpus) - 1.0)

    total = float(counts.sum())

    # unweighted density: pooled count over pooled area
    sigma_unw = total / A_CONE / len(CONES)          # per arcmin^2
    # scan-weighted density: mean of per-cone density divided by the weight
    sigma_w = float(np.mean(counts / (A_CONE * weights)))  # per arcmin^2

    n_exp_unw = sigma_unw * A_ANN
    n_exp_w = sigma_w * A_ANN
    n_exp_unw_b = sigma_unw * A_ANN_B
    n_exp_w_b = sigma_w * A_ANN_B

    # intervals on the total count, scaled by the area ratio
    lo, hi = poisson_interval(int(total))
    jlo, jhi = jeffreys_interval(int(total))
    scale = A_ANN / (A_CONE * len(CONES))
    pois = dict(lo=lo * scale, hi=hi * scale)
    jeff = dict(lo=jlo * scale, hi=jhi * scale)

    # one-sided 95 per cent upper limit on a zero count, for reference
    ul_zero = poisson_interval(0, two_sided=False)[1] * scale

    blo, bhi = bootstrap_cones(counts, weights)
    blo_u, bhi_u = bootstrap_cones(counts, np.ones_like(counts))

    # factorised estimate, per cone, then pooled
    fac = []
    for c in per_cone:
        f_blue = c["n_blue"] / c["n_base_15_20"] if c["n_base_15_20"] else np.nan
        f_pm = (c["n_pm_blue_15_20"] / c["n_blue_15_20"]
                if c["n_blue_15_20"] else np.nan)
        dens = c["n_base_15_20"] / A_CONE * f_blue * f_pm
        fac.append(dict(dl=c["dl"], f_blue=f_blue, f_pm_blue=f_pm,
                        density_per_arcmin2=dens,
                        n_exp_A=dens * A_ANN))
    fac_n_exp = float(np.nanmean([f["n_exp_A"] for f in fac]))

    # aperture A count of the target annulus
    ann = load_annulus()
    ra, dec = ann["ra"], ann["dec"]
    cosd = (np.sin(np.radians(DEC_C)) * np.sin(np.radians(dec))
            + np.cos(np.radians(DEC_C)) * np.cos(np.radians(dec))
            * np.cos(np.radians(ra - RA_C)))
    sep = np.degrees(np.arccos(np.clip(cosd, -1.0, 1.0))) * 60.0
    in_a = (sep >= 25.0) & (sep <= 30.0)
    in_b = (sep >= 25.0) & (sep <= 31.0)
    n_obs_a = int(select_gaia(ann, aperture=in_a).sum())
    n_obs_b = int(select_gaia(ann, aperture=in_b).sum())
    n_obs_a_old = int(select_gaia(ann, radius=1.2, aperture=in_a).sum())
    n_obs_b_old = int(select_gaia(ann, radius=1.2, aperture=in_b).sum())
    n_obs_box_a = int(select_gaia(ann, radius=1e9, aperture=in_a).sum())

    out = dict(
        method="Gaia DR3 control cones, frozen selection S, area scaled",
        inputs=dict(cones=[dict(dl=c[0], ra=c[1], dec=c[2]) for c in CONES],
                    cone_radius_arcmin=30.0,
                    area_cone_arcmin2=A_CONE,
                    area_annulus_A_arcmin2=A_ANN,
                    area_annulus_B_arcmin2=A_ANN_B,
                    area_ratio_A=AREA_RATIO,
                    window_radius_mas_yr=R_WIN,
                    mean_pm=[MU_A, MU_D],
                    g_range=[G_LO, G_HI], bp_rp_range=[0.0, 0.4]),
        per_cone=per_cone,
        weights=dict(med_vpu=vpus.tolist(), f_w=f_w.tolist(),
                     relative_spread=spread_vpu,
                     immaterial=bool(spread_vpu < 0.10)),
        counts=dict(total=int(total), per_cone=counts.astype(int).tolist(),
                    n_old_window_1p2=int(sum(c["n_old_1p2"] for c in per_cone))),
        density=dict(sigma_unweighted_per_deg2=sigma_unw * 3600.0,
                     sigma_scan_weighted_per_deg2=sigma_w * 3600.0,
                     note="per deg^2, from the per-arcmin^2 densities"),
        expected=dict(
            N_exp_A_unweighted=n_exp_unw,
            N_exp_A_weighted=n_exp_w,
            N_exp_B_unweighted=n_exp_unw_b,
            N_exp_B_weighted=n_exp_w_b,
            poisson95_A=pois, jeffreys95_A=jeff,
            poisson95_zero_count_A=ul_zero,
            bootstrap95_A_weighted=[blo, bhi],
            bootstrap95_A_unweighted=[blo_u, bhi_u]),
        factorised=dict(per_cone=fac, N_exp_A=fac_n_exp),
        annulus=dict(N_obs_A=n_obs_a, N_obs_B=n_obs_b,
                     N_obs_A_old_window=n_obs_a_old,
                     N_obs_B_old_window=n_obs_b_old,
                     N_obs_A_no_pm_cut=n_obs_box_a),
    )
    write_json("q1_control_cones.json", out)

    print(f"counts per cone {counts.astype(int).tolist()}  total {int(total)}")
    print(f"med VPU {np.round(vpus, 1).tolist()}  spread {spread_vpu:.3f}")
    print(f"N_exp A weighted {n_exp_w:.4f} unweighted {n_exp_unw:.4f}")
    print(f"poisson95 {pois}  jeffreys95 {jeff}")
    print(f"bootstrap {blo:.4f} {bhi:.4f}")
    print(f"factorised {fac_n_exp:.4f}")
    print(f"N_obs A {n_obs_a} B {n_obs_b} old {n_obs_a_old}")


if __name__ == "__main__":
    main()
