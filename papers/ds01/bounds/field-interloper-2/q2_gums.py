"""Q2: field-interloper density from the GUMS synthetic catalogue.

Angle 2 of row 5. Same six centres, same radius, same selection as the Gaia
control cones, but on the noiseless synthetic population of VizieR VI/137.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from common import (A_ANN, A_ANN_B, A_CONE, AREA_RATIO, CONES, G_HI, G_LO,
                    MU_A, MU_D, R_WIN, bootstrap_cones, jeffreys_interval,
                    load_gums_cone, poisson_interval, select_gums, write_json)


def main():
    per_cone = []
    for dl, ra, dec in CONES:
        tab = load_gums_cone(dl)
        n_all = len(tab["Gmag"])
        sel = select_gums(tab)
        box = select_gums(tab, radius=1e9)
        g = tab["Gmag"]
        c = tab["GBmag"] - tab["GRmag"]
        pm = np.hypot(tab["pmRA"] - MU_A, tab["pmDE"] - MU_D)
        b15 = (g >= 15.0) & (g <= 20.0) & (c > 0.0) & (c < 0.4)
        pops = tab["Pop"]
        per_cone.append(dict(
            dl=dl, ra=ra, dec=dec, n_all=n_all,
            n_sel=int(sel.sum()), n_box=int(box.sum()),
            n_blue_15_20=int(b15.sum()),
            n_pm_blue_15_20=int((b15 & (pm <= R_WIN)).sum()),
            n_sel_thin=int((sel & (pops == 1)).sum()),
            n_sel_thick=int((sel & (pops == 2)).sum()),
            n_sel_halo=int((sel & (pops == 3)).sum()),
            n_box_thin=int((box & (pops == 1)).sum()),
            n_box_thick=int((box & (pops == 2)).sum()),
            n_box_halo=int((box & (pops == 3)).sum()),
        ))

    counts = np.array([c["n_sel"] for c in per_cone], dtype=float)
    total = float(counts.sum())
    sigma = total / A_CONE / len(CONES)
    n_exp = sigma * A_ANN
    n_exp_b = sigma * A_ANN_B

    lo, hi = poisson_interval(int(total))
    jlo, jhi = jeffreys_interval(int(total))
    scale = A_ANN / (A_CONE * len(CONES))
    blo, bhi = bootstrap_cones(counts, np.ones_like(counts))

    box_total = int(sum(c["n_box"] for c in per_cone))
    box_density = box_total / A_CONE / len(CONES) * A_ANN

    n_blue = int(sum(c["n_blue_15_20"] for c in per_cone))
    n_pm_blue = int(sum(c["n_pm_blue_15_20"] for c in per_cone))
    f_pm_blue = n_pm_blue / n_blue if n_blue else float("nan")
    fac_n_exp = box_density * f_pm_blue

    out = dict(
        method="GUMS VI/137 synthetic cones, frozen selection S, area scaled",
        catalogue="VizieR VI/137/gum_mw (Robin et al. 2012), J2010 positions,"
                  " noiseless astrometry, no scan law",
        per_cone=per_cone,
        counts=dict(total=int(total), per_cone=counts.astype(int).tolist(),
                    by_population=dict(
                        thin=int(sum(c["n_sel_thin"] for c in per_cone)),
                        thick=int(sum(c["n_sel_thick"] for c in per_cone)),
                        halo=int(sum(c["n_sel_halo"] for c in per_cone)))),
        box=dict(total_no_pm_cut=box_total, N_exp_A_no_pm_cut=box_density),
        factorised=dict(n_blue_15_20=n_blue, n_pm_blue_15_20=n_pm_blue,
                        f_pm_blue=f_pm_blue, N_exp_A=fac_n_exp),
        density=dict(sigma_per_deg2=sigma * 3600.0),
        expected=dict(
            N_exp_A=n_exp, N_exp_B=n_exp_b,
            poisson95_A=dict(lo=lo * scale, hi=hi * scale),
            jeffreys95_A=dict(lo=jlo * scale, hi=jhi * scale),
            bootstrap95_A=[blo, bhi]),
    )
    write_json("q2_gums.json", out)
    print(f"counts {counts.astype(int).tolist()} total {int(total)}")
    print(f"populations thin/thick/halo "
          f"{out['counts']['by_population']}")
    print(f"N_exp A {n_exp:.4f}  poisson95 {lo*scale:.4f} {hi*scale:.4f}")
    print(f"box total {box_total} N_exp box {box_density:.3f}")
    print(f"f_pm_blue {f_pm_blue:.4f} factorised {fac_n_exp:.4f}")


if __name__ == "__main__":
    main()
