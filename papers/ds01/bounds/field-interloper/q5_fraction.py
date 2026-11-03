"""Q5: combine the angles into the two headline bounds.

Field-interloper fraction, proper-motion window fraction, and the probability
that DS-01 is a field CV.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy import stats

from common import (A_ANN, A_CONE, CONES, DEC_C, G_HI, G_LO, MU_A, MU_D, OUT,
                    RA_C, R_WIN, load_annulus, load_gaia_cone, poisson_interval,
                    write_json)


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def load(name):
    with open(os.path.join(OUT, name)) as fh:
        return json.load(fh)


def main():
    q1 = load("q1_control_cones.json")
    q2 = load("q2_gums.json")
    q3 = load("q3_cv_empirical.json")
    q4 = load("q4_cv_model.json")

    # f_pm from the control cones, blue box at 18 to 20
    n_box = 0
    n_win = 0
    n_box_15 = 0
    n_win_15 = 0
    for dl, _, _ in CONES:
        tab = load_gaia_cone(dl)
        g, c = tab["phot_g_mean_mag"], tab["bp_rp"]
        ps = tab["astrometric_params_solved"]
        five = (ps == 31) | (ps == 95)
        pm = np.hypot(tab["pmra"] - MU_A, tab["pmdec"] - MU_D)
        b = five & np.isfinite(g) & np.isfinite(c) & (g >= G_LO) & (g <= G_HI) \
            & (c > 0) & (c < 0.4)
        b15 = five & np.isfinite(g) & np.isfinite(c) & (g >= 15) & (g <= 20) \
            & (c > 0) & (c < 0.4)
        n_box += int(b.sum())
        n_win += int((b & (pm <= R_WIN)).sum())
        n_box_15 += int(b15.sum())
        n_win_15 += int((b15 & (pm <= R_WIN)).sum())

    f_pm = n_win / n_box
    f_pm_lo, f_pm_hi = wilson(n_win, n_box)
    f_pm_15 = n_win_15 / n_box_15
    f_pm_15_lo, f_pm_15_hi = wilson(n_win_15, n_box_15)

    # field expectation in a proper-motion shell at DS-01's own offset
    n_shell = 0
    for dl, _, _ in CONES:
        tab = load_gaia_cone(dl)
        g, c = tab["phot_g_mean_mag"], tab["bp_rp"]
        ps = tab["astrometric_params_solved"]
        five = (ps == 31) | (ps == 95)
        pm = np.hypot(tab["pmra"] - MU_A, tab["pmdec"] - MU_D)
        b = five & np.isfinite(g) & np.isfinite(c) & (g >= G_LO) & (g <= G_HI) \
            & (c > 0) & (c < 0.4)
        n_shell += int((b & (pm >= 0.55) & (pm <= 0.68)).sum())
    # equivalent area of the shell in proper-motion space, for the density
    shell_area_ratio = (0.68 ** 2 - 0.55 ** 2) / R_WIN ** 2
    n_exp_shell = n_shell * A_ANN / (len(CONES) * A_CONE)

    # crowding proxy: density of stars at 15 <= G < 17, complete in both places
    def bright_density(tab, area_arcmin2):
        g = tab["phot_g_mean_mag"]
        ps = tab["astrometric_params_solved"]
        five = (ps == 31) | (ps == 95)
        m = five & np.isfinite(g) & (g >= 15) & (g < 17)
        return int(m.sum()) / area_arcmin2

    cone_bright = float(np.mean([bright_density(load_gaia_cone(dl), A_CONE)
                                 for dl, _, _ in CONES]))
    ann = load_annulus()
    ra, dec = ann["ra"], ann["dec"]
    cosd = (np.sin(np.radians(DEC_C)) * np.sin(np.radians(dec))
            + np.cos(np.radians(DEC_C)) * np.cos(np.radians(dec))
            * np.cos(np.radians(ra - RA_C)))
    sep = np.degrees(np.arccos(np.clip(cosd, -1.0, 1.0))) * 60.0
    in_a = (sep >= 25.0) & (sep <= 30.0)
    ann_bright = int(((ann["phot_g_mean_mag"] >= 15)
                      & (ann["phot_g_mean_mag"] < 17) & in_a
                      & ((ann["astrometric_params_solved"] == 31)
                         | (ann["astrometric_params_solved"] == 95))).sum()) \
        / A_ANN

    # field-interloper fraction
    n_obs_a = q1["annulus"]["N_obs_A"]
    n_obs_a_old = q1["annulus"]["N_obs_A_old_window"]
    n_exp_w = q1["expected"]["N_exp_A_weighted"]
    n_exp_u = q1["expected"]["N_exp_A_unweighted"]
    pois = q1["expected"]["poisson95_A"]
    jeff = q1["expected"]["jeffreys95_A"]

    f_int = n_exp_w / n_obs_a if n_obs_a else float("nan")
    f_int_lo = pois["lo"] / n_obs_a if n_obs_a else float("nan")
    f_int_hi = pois["hi"] / n_obs_a if n_obs_a else float("nan")
    f_int_old = n_exp_u / n_obs_a_old if n_obs_a_old else float("nan")

    # field CV
    sig_emp = q3["density"]["sigma_per_deg2"]
    sig_mod = q4["sigma_colour_cut_per_deg2"]
    sig_mod_hi = max(q4["sensitivity"].values())
    sig_mod_lo = min(q4["sensitivity"].values())

    def p_field(sigma, fpm):
        n = sigma * (A_ANN / 3600.0) * fpm
        return n, 1.0 - np.exp(-n)

    n_emp, p_emp = p_field(sig_emp, f_pm)
    n_mod, p_mod = p_field(sig_mod, f_pm)
    n_mod_hi, p_mod_hi = p_field(sig_mod_hi, f_pm_hi)
    n_mod_lo, p_mod_lo = p_field(sig_mod_lo, f_pm_lo)
    n_emp_hi, p_emp_hi = p_field(
        q3["density"]["poisson95"]["hi"], f_pm_hi)

    out = dict(
        f_pm=dict(k=n_win, n=n_box, value=f_pm, wilson95=[f_pm_lo, f_pm_hi],
                  k_15_20=n_win_15, n_15_20=n_box_15, value_15_20=f_pm_15,
                  wilson95_15_20=[f_pm_15_lo, f_pm_15_hi]),
        ds01_shell=dict(pm_range=[0.55, 0.68], n_control=n_shell,
                        N_exp_in_aperture=n_exp_shell,
                        pm_area_ratio_to_window=shell_area_ratio),
        crowding=dict(cone_bright_per_arcmin2=cone_bright,
                      annulus_bright_per_arcmin2=ann_bright,
                      ratio=ann_bright / cone_bright if cone_bright else None),
        interloper=dict(
            N_exp_weighted=n_exp_w, N_exp_unweighted=n_exp_u,
            poisson95=pois, jeffreys95=jeff,
            N_obs_new_window=n_obs_a, N_obs_old_window=n_obs_a_old,
            f_int=f_int, f_int_interval=[f_int_lo, f_int_hi],
            f_int_old_window=f_int_old,
            draft_claim=dict(N_obs=4, N_exp=0.05,
                             fraction_best=0.0127, fraction_ul95=0.0604)),
        cv=dict(
            sigma_empirical=sig_emp,
            sigma_empirical_95=q3["density"]["poisson95"],
            sigma_model=sig_mod,
            sigma_model_range=[sig_mod_lo, sig_mod_hi],
            N_exp_no_pm_emp=n_emp / f_pm if f_pm else None,
            N_exp_no_pm_model=n_mod / f_pm if f_pm else None,
            N_exp_emp=n_emp, P_field_emp=p_emp,
            N_exp_model=n_mod, P_field_model=p_mod,
            N_exp_model_hi=n_mod_hi, P_field_model_hi=p_mod_hi,
            N_exp_model_lo=n_mod_lo, P_field_model_lo=p_mod_lo,
            P_field_emp_hi=p_emp_hi,
            conservative_P=float(max(p_mod_hi, p_emp_hi))),
    )
    write_json("q5_fraction.json", out)

    print(f"f_pm {n_win}/{n_box} = {f_pm:.4f} [{f_pm_lo:.4f},{f_pm_hi:.4f}]"
          f"  15-20 {n_win_15}/{n_box_15} = {f_pm_15:.4f}")
    print(f"N_exp {n_exp_w:.4f} N_obs {n_obs_a} f_int {f_int:.4f} "
          f"[{f_int_lo:.4f},{f_int_hi:.4f}]")
    print(f"old window N_obs {n_obs_a_old} f_int {f_int_old:.4f}")
    print(f"CV sigma emp {sig_emp:.4f} model {sig_mod:.4f} "
          f"[{sig_mod_lo:.4f},{sig_mod_hi:.4f}]")
    print(f"P(field CV) emp {p_emp:.5f} model {p_mod:.5f} "
          f"model_hi {p_mod_hi:.5f} conservative {out['cv']['conservative_P']:.5f}")
    print(f"DS-01 shell n={n_shell} N_exp={n_exp_shell:.4f}")
    print(f"crowding annulus/cone {ann_bright / cone_bright:.3f}")


if __name__ == "__main__":
    main()
