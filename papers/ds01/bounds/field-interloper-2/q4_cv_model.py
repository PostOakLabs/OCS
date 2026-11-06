"""Q4: field-CV surface density from a thick disc plus halo population model.

Angle 2 of row 6. Integrates a three-component CV space density along the
line of sight at the cluster latitude, with a magnitude window set by the
absolute magnitude distribution measured in Q3.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy import stats

from common import (A_ANN, B_C, L_C, SEED, write_json)

RHO0 = 4.8e-6          # pc^-3, Pala et al. 2020 local CV space density
R_SUN = 8.15e3         # pc
H_R_THIN, H_R_THICK = 2.5e3, 3.5e3
H_Z_THIN, H_Z_THICK, H_Z_HALO = 0.30e3, 0.90e3, 2.5e3
F_THICK, F_HALO = 0.10, 0.0015
A_G_PER_KPC = 0.7
A_G_CAP_KPC = 3.0
G_LO, G_HI = 18.0, 20.0
NMC = 200000
SR_PER_DEG2 = (np.pi / 180.0) ** 2


def density(d_pc, f_thick=F_THICK, f_halo=F_HALO):
    """Total CV space density in pc^-3 along the line of sight."""
    s = d_pc * np.cos(np.radians(B_C))
    z = np.abs(d_pc * np.sin(np.radians(B_C)))
    r = np.sqrt(R_SUN ** 2 + s ** 2 - 2.0 * R_SUN * s * np.cos(np.radians(L_C)))
    f_thin = 1.0 - f_thick - f_halo
    thin = f_thin * np.exp(-(r - R_SUN) / H_R_THIN) * np.exp(-z / H_Z_THIN)
    thick = f_thick * np.exp(-(r - R_SUN) / H_R_THICK) * np.exp(-z / H_Z_THICK)
    halo = f_halo * np.exp(-(r - R_SUN) / H_R_THICK) * np.exp(-z / H_Z_HALO)
    return RHO0 * (thin + thick + halo)


def extinction(d_pc, a_per_kpc=A_G_PER_KPC):
    return a_per_kpc * np.minimum(d_pc / 1.0e3, A_G_CAP_KPC)


def integral_surface_density(mg_mean, mg_sd, f_thick=F_THICK, f_halo=F_HALO,
                             a_per_kpc=A_G_PER_KPC, d_max=60.0e3, n=4000):
    """Per deg^2, by direct quadrature over distance."""
    d = np.linspace(50.0, d_max, n)
    dd = d[1] - d[0]
    rho = density(d, f_thick, f_halo)
    a = extinction(d, a_per_kpc)
    mu = 5.0 * np.log10(d / 10.0)
    lo = G_LO - mu - a
    hi = G_HI - mu - a
    p = stats.norm.cdf(hi, mg_mean, mg_sd) - stats.norm.cdf(lo, mg_mean, mg_sd)
    per_sr = np.sum(d ** 2 * rho * p) * dd
    return per_sr * SR_PER_DEG2


def mc_surface_density(mg_mean, mg_sd, f_thick=F_THICK, f_halo=F_HALO,
                       a_per_kpc=A_G_PER_KPC, nmc=NMC, seed=SEED):
    """Monte Carlo version declared in METHOD.md section 3, Q4.

    Uniform draws in distance with an importance weight d^2 rho(d), and a
    magnitude drawn from the absolute magnitude distribution. The estimator
    is (dmax-dmin)/N * sum d^2 rho 1[G in window], which converges to the
    same integral as integral_surface_density.
    """
    rng = np.random.default_rng(seed)
    d = rng.uniform(50.0, 60.0e3, nmc)
    rho = density(d, f_thick, f_halo)
    mg = rng.normal(mg_mean, mg_sd, nmc)
    a = extinction(d, a_per_kpc)
    g = mg + 5.0 * np.log10(d / 10.0) + a
    inside = (g >= G_LO) & (g <= G_HI)
    dd = (60.0e3 - 50.0) / nmc
    per_sr = np.sum(d[inside] ** 2 * rho[inside]) * dd
    return per_sr * SR_PER_DEG2, int(inside.sum())


def main():
    mg_mean, mg_sd = 8.4718, 2.2040     # Q3 measured values
    sigma = integral_surface_density(mg_mean, mg_sd)
    sigma_mc, n_in = mc_surface_density(mg_mean, mg_sd)

    # independent cross-check of the Monte Carlo normalisation
    grid = dict()
    for f_t in (0.04, 0.10, 0.25):
        for a in (0.4, 0.7, 1.0):
            grid[f"f_thick={f_t}_A={a}"] = integral_surface_density(
                mg_mean, mg_sd, f_thick=f_t, a_per_kpc=a)
    for dm in (-1.0, 0.0, 1.0):
        for ds in (1.4, 2.2):
            grid[f"mg_mean={mg_mean+dm:.2f}_sd={ds}"] = \
                integral_surface_density(mg_mean + dm, ds)

    # contribution of each component separately, weighted by its own fraction
    comp = {}
    for name, ft, fh in (("thin", 0.0, 0.0), ("thick", 1.0, 0.0),
                         ("halo", 0.0, 1.0)):
        comp[name + "_unweighted"] = integral_surface_density(
            mg_mean, mg_sd, f_thick=ft, f_halo=fh)
    f_thin = 1.0 - F_THICK - F_HALO
    comp["thin"] = comp["thin_unweighted"] * f_thin
    comp["thick"] = comp["thick_unweighted"] * F_THICK
    comp["halo"] = comp["halo_unweighted"] * F_HALO

    # colour-pass fraction measured on the CV class in Q3
    import json
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out",
                           "q3_cv_empirical.json")) as fh:
        q3 = json.load(fh)
    f_col = q3["counts"]["n_sel_sky"] / q3["counts"]["n_mag_sky"]
    sigma_col = sigma * f_col

    n_exp = sigma_col * A_ANN / 3600.0
    out = dict(
        method="thick disc plus halo CV space density, integrated along the "
               "line of sight at b = 14.9682, with the Q3 absolute magnitude "
               "distribution and the Q3 colour-pass fraction",
        parameters=dict(rho0_pc3=RHO0, R_sun_pc=R_SUN,
                        h_R_thin_pc=H_R_THIN, h_R_thick_pc=H_R_THICK,
                        h_z_thin_pc=H_Z_THIN, h_z_thick_pc=H_Z_THICK,
                        h_z_halo_pc=H_Z_HALO, f_thick=F_THICK,
                        f_halo=F_HALO, A_G_per_kpc=A_G_PER_KPC,
                        A_G_cap_kpc=A_G_CAP_KPC,
                        mg_mean=mg_mean, mg_sd=mg_sd,
                        g_window=[G_LO, G_HI]),
        sigma_per_deg2=sigma,
        colour_pass_fraction=f_col,
        sigma_colour_cut_per_deg2=sigma_col,
        N_exp_A=n_exp,
        mc=dict(nmc=NMC, n_in_window=n_in, sigma_per_deg2=sigma_mc),
        components_per_deg2=comp,
        sensitivity={k: v * f_col for k, v in grid.items()},
        sensitivity_uncoloured=grid,
    )
    write_json("q4_cv_model.json", out)
    print(f"model sigma {sigma:.4f} per deg2, colour cut {sigma_col:.4f}")
    print(f"N_exp(A) {n_exp:.5f}")
    print(f"components {({k: round(float(v),4) for k,v in comp.items()})}")
    print(f"f_col {f_col:.4f}")


if __name__ == "__main__":
    main()
