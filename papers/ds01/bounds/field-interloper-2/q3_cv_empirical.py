"""Q3: empirical field-CV surface density from the Gaia DR3 variability classes.

Angle 1 of row 6. Counts CV-class sources at matched galactic latitude and
matched magnitude and colour, and converts to a surface density with Poisson
and Jeffreys intervals.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

from common import (B_C, CACHE, CONES, G_HI, G_LO, jeffreys_interval,
                    load_csv, polygon_area_deg2, poisson_interval, write_json)

L_LO, L_HI = 300.0, 320.0
DB = 2.0
R_CONE_DEG = 0.5


def band_area():
    """Area of a galactic longitude-latitude rectangle, exact integral."""
    dl = np.radians(L_HI - L_LO)
    b_lo, b_hi = np.radians(B_C - DB), np.radians(B_C + DB)
    omega = dl * (np.sin(b_hi) - np.sin(b_lo))
    return float(omega * (180.0 / np.pi) ** 2)


def main():
    cv = load_csv(os.path.join(CACHE, "gaia_cv_class.csv"))
    ra, dec = cv["ra"], cv["dec"]
    g, c = cv["phot_g_mean_mag"], cv["bp_rp"]
    n_total = len(ra)

    coord = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs")
    gal = coord.galactic
    l, b = gal.l.deg, gal.b.deg

    in_band = (l >= L_LO) & (l <= L_HI) & (np.abs(b - B_C) <= DB)
    mag = (g >= G_LO) & (g <= G_HI)
    col = (c > 0.0) & (c < 0.4)

    n_band_all = int(in_band.sum())
    n_band_mag = int((in_band & mag).sum())
    n_band_sel = int((in_band & mag & col).sum())
    n_mag_sky = int(mag.sum())
    n_sel_sky = int((mag & col).sum())

    omega = band_area()
    sigma = n_band_sel / omega
    lo, hi = poisson_interval(n_band_sel)
    jlo, jhi = jeffreys_interval(n_band_sel)

    # control cones, the most closely matched region
    cone_counts = []
    for dl, cra, cdec in CONES:
        sep = coord.separation(SkyCoord(cra * u.deg, cdec * u.deg, frame="icrs"))
        m = sep.deg <= R_CONE_DEG
        cone_counts.append(dict(dl=dl, n_all=int(m.sum()),
                                n_mag=int((m & mag).sum()),
                                n_sel=int((m & mag & col).sum())))
    n_cone_sel = int(sum(x["n_sel"] for x in cone_counts))
    omega_cone = 6 * np.pi * R_CONE_DEG ** 2
    sigma_cone = n_cone_sel / omega_cone
    clo, chi = poisson_interval(n_cone_sel)

    # absolute magnitude distribution, for the population model
    par = cv["parallax"]
    pe = cv["parallax_error"]
    ok = np.isfinite(par) & np.isfinite(pe) & (pe > 0) & (par > 0.5) & \
         (par / pe > 5.0) & np.isfinite(g)
    mg = np.full(g.shape, np.nan)
    mg[ok] = g[ok] - 5.0 * np.log10(1000.0 / par[ok]) + 5.0
    mg = mg[np.isfinite(mg)]
    mg = mg[(mg > 0.0) & (mg < 20.0)]
    mg_stats = dict(n=int(mg.size),
                    mean=float(np.mean(mg)) if mg.size else None,
                    sd=float(np.std(mg, ddof=1)) if mg.size > 1 else None,
                    p16=float(np.percentile(mg, 16)) if mg.size else None,
                    p50=float(np.percentile(mg, 50)) if mg.size else None,
                    p84=float(np.percentile(mg, 84)) if mg.size else None)

    out = dict(
        method="Gaia DR3 vari_classifier_result best_class_name = CV, "
               "matched galactic latitude band, area normalised",
        region=dict(l_range=[L_LO, L_HI], b_centre=B_C, b_half_width=DB,
                    area_deg2=omega),
        selection=dict(g_range=[G_LO, G_HI], bp_rp_range=[0.0, 0.4]),
        counts=dict(n_cv_class_total=n_total,
                    n_in_band=n_band_all,
                    n_in_band_mag=n_band_mag,
                    n_in_band_sel=n_band_sel,
                    n_mag_sky=n_mag_sky, n_sel_sky=n_sel_sky),
        density=dict(
            sigma_per_deg2=sigma,
            poisson95=dict(lo=lo / omega, hi=hi / omega),
            jeffreys95=dict(lo=jlo / omega, hi=jhi / omega),
            note="lower bound: DR3 CV class completeness is 15 per cent"),
        control_cones=dict(per_cone=cone_counts, n_sel=n_cone_sel,
                           area_deg2=omega_cone,
                           sigma_per_deg2=sigma_cone,
                           poisson95=dict(lo=clo / omega_cone,
                                          hi=chi / omega_cone)),
        absolute_magnitude=dict(cuts="parallax > 0.5 mas, parallax/error > 5",
                                **mg_stats),
    )
    write_json("q3_cv_empirical.json", out)
    print(f"CV total {n_total}, band {n_band_all}, band+mag {n_band_mag}, "
          f"band+mag+colour {n_band_sel}")
    print(f"band area {omega:.2f} deg2, sigma {sigma:.4f} per deg2 "
          f"[{lo/omega:.4f}, {hi/omega:.4f}]")
    print(f"cones {n_cone_sel} in {omega_cone:.2f} deg2 -> {sigma_cone:.4f}")
    print(f"M_G {mg_stats}")


if __name__ == "__main__":
    main()
