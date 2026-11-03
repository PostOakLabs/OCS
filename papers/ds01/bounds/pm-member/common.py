"""Shared loaders and geometry for OCS-DS01-BOUNDS-PM-MEMBER-1.

Every array is returned in the order the archive stores it. No analysis happens
in this module; it only reads the two catalogues and does small-angle geometry.
"""
import csv
import os

import numpy as np

CACHE = r"C:\farm\cache\omegacen\ds01-bounds-pm-member\raw"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

TARGET_ID = 6083772968079356544
CEN_RA, CEN_DEC = 201.696833, -47.479583

SEED = 20261019
D_SSOT_KPC = 5.49
RV_SYS = 232.0
ARCSEC_PER_RAD = 206264.80624709636


def vb21():
    """Vasiliev & Baumgardt (2021) catalogue for NGC 5139."""
    path = os.path.join(CACHE, "catalogues", "NGC_5139_oCen.txt")
    sid = np.loadtxt(path, comments="#", usecols=[0], dtype=np.int64)
    d = np.loadtxt(path, comments="#", usecols=range(1, 17))
    out = {
        "source_id": sid,
        "ra": d[:, 0], "dec": d[:, 1],
        "x": d[:, 2], "y": d[:, 3],
        "plx": d[:, 4], "pmra": d[:, 5], "pmdec": d[:, 6],
        "plxe": d[:, 7], "pmrae": d[:, 8], "pmdece": d[:, 9],
        "pmcorr": d[:, 10], "g": d[:, 11], "bprp": d[:, 12],
        "sigma": d[:, 13], "qflag": d[:, 14].astype(int),
        "memberprob": d[:, 15],
    }
    out["r_deg"] = np.hypot(out["x"], out["y"])
    out["r_arcmin"] = out["r_deg"] * 60.0
    return out


def profile():
    """VB21 radial profile: r[deg], five dispersion percentiles, six rotation cols."""
    p = np.loadtxt(os.path.join(CACHE, "profiles", "NGC_5139_oCen.txt"))
    return {
        "r_deg": p[:, 0],
        "disp": p[:, 1:6],
        "rot": p[:, 6:12],
    }


_GAIA_COLS = ["source_id", "ra", "dec", "parallax", "parallax_error",
              "parallax_over_error", "pmra", "pmdec", "pmra_error",
              "pmdec_error", "pmra_pmdec_corr", "phot_g_mean_mag",
              "phot_bp_mean_mag", "phot_rp_mean_mag", "bp_rp", "ruwe",
              "astrometric_excess_noise", "astrometric_excess_noise_sig",
              "phot_variable_flag", "ipd_gof_harmonic_amplitude",
              "ipd_frac_multi_peak", "visibility_periods_used",
              "astrometric_params_solved", "radial_velocity",
              "radial_velocity_error", "ref_epoch"]

_STR_COLS = {"phot_variable_flag"}


def gaia_cone():
    """Gaia DR3 cone, 35 arcmin about the Harris centre, 289,638 rows."""
    path = os.path.join(CACHE, "gaia_dr3_cone35.csv")
    cols = {c: [] for c in _GAIA_COLS}
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        for row in rd:
            for c in _GAIA_COLS:
                cols[c].append(row[c])
    out = {}
    for c in _GAIA_COLS:
        if c in _STR_COLS:
            out[c] = np.array(cols[c], dtype=object)
        elif c == "source_id":
            out[c] = np.array([int(v) for v in cols[c]], dtype=np.int64)
        else:
            out[c] = np.array([np.nan if v == "" else float(v)
                               for v in cols[c]], dtype=float)
    out["x"] = (out["ra"] - CEN_RA) * np.cos(np.radians(CEN_DEC))
    out["y"] = out["dec"] - CEN_DEC
    out["r_deg"] = np.hypot(out["x"], out["y"])
    out["r_arcmin"] = out["r_deg"] * 60.0
    return out


def cov2(sa, sd, rho):
    """Stack 2x2 covariance matrices from two errors and a correlation."""
    sa = np.asarray(sa, dtype=float)
    sd = np.asarray(sd, dtype=float)
    rho = np.broadcast_to(np.asarray(rho, dtype=float), sa.shape)
    c = np.empty(sa.shape + (2, 2))
    c[..., 0, 0] = sa ** 2
    c[..., 1, 1] = sd ** 2
    c[..., 0, 1] = rho * sa * sd
    c[..., 1, 0] = c[..., 0, 1]
    return c


def wmean(cov, y):
    """ML weighted mean and its covariance for measurements with 2x2 covariances."""
    p = np.linalg.inv(cov)
    a = p.sum(axis=0)
    b = np.einsum("nij,nj->i", p, y)
    c = np.linalg.inv(a)
    return c @ b, c


def chi2_2d(delta, cov):
    return float(delta @ np.linalg.solve(cov, delta))


def p_two_dof(chi2):
    return float(np.exp(-0.5 * chi2))


def z_from_chi2(chi2):
    """Equivalent one-dimensional Gaussian significance, labelled as such."""
    return float(np.sqrt(chi2))


def unit_vectors(x, y):
    r = np.hypot(x, y)
    er = np.stack([x / r, y / r], axis=-1)
    et = np.stack([-y / r, x / r], axis=-1)
    return er, et, r


def write_json(name, obj):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        import json
        json.dump(obj, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return path
