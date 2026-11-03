"""Shared constants, loaders and interval estimators for the field-interloper WU.

Frozen values come from METHOD.md. Nothing here decides a cut.
"""

import json
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CACHE = r"C:\farm\cache\omegacen\ds01-bounds-field-interloper\raw"
D189 = r"C:\farm\cache\omegacen\ds01-bounds-pm-member\raw\gaia_dr3_cone35.csv"

SEED = 20261019
NBOOT = 10000

L_C, B_C = 309.101888687704, 14.968236020672741
RA_C, DEC_C = 201.696833, -47.479583
DS01 = dict(ra=201.418492, dec=-47.057149, pmra=-3.4642, pmdec=-7.3160,
            pmra_err=0.3436, pmdec_err=0.3198, corr=-0.1908)

CONES = [(-6, 193.104407, -47.903188), (-4, 195.984182, -47.850843),
         (-3, 197.420239, -47.791195), (3, 205.899272, -46.972709),
         (4, 207.278117, -46.761474), (6, 209.996618, -46.277392)]

MU_A, MU_D = -3.2486, -6.7398      # V&B local mean, D189 section 1
SIGMA_INT = 0.253                  # measured V&B dispersion
R_WIN = 0.46707692307692306        # 81.8 per cent containment at 0.253

G_LO, G_HI = 18.0, 20.0
COL_LO, COL_HI = 0.0, 0.4

ARCMIN2_PER_DEG2 = 3600.0
A_ANN = 863.9379797371931          # arcmin^2, 25-30 arcmin
A_ANN_B = 1055.5                   # arcmin^2, 25-31 arcmin (D189)
A_CONE = np.pi * 30.0 ** 2         # arcmin^2, r = 30 arcmin
N_CONE = len(CONES)
A_TOT = N_CONE * A_CONE
AREA_RATIO = A_ANN / A_TOT


def deg2(arcmin2):
    return arcmin2 / ARCMIN2_PER_DEG2


def load_csv(path):
    """Whitespace or comma separated table with one header line."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        head = fh.readline().strip()
        sep = "\t" if head.count("\t") > head.count(",") else ","
        names = [c.strip().strip('"') for c in head.split(sep)]
        rows = []
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [c.strip().strip('"') for c in line.split(sep)]
            if len(parts) != len(names):
                continue
            rows.append(parts)
    cols = {n: [] for n in names}
    for r in rows:
        for n, v in zip(names, r):
            cols[n].append(v)
    out = {}
    for n in names:
        vals = cols[n]
        try:
            out[n] = np.array([float(v) if v not in ("", "null", "NaN") else np.nan
                               for v in vals])
        except ValueError:
            out[n] = np.array(vals, dtype=object)
    return out


def load_gaia_cone(dl):
    return load_csv(os.path.join(CACHE, f"control_dl{dl:+d}.csv"))


def load_gums_cone(dl):
    return load_csv(os.path.join(CACHE, f"gums_dl{dl:+d}.csv"))


def load_annulus():
    return load_csv(D189)


def select_gaia(tab, radius=R_WIN, aperture=None):
    """Selection S of METHOD.md section 2. Returns a boolean mask."""
    g = tab["phot_g_mean_mag"]
    c = tab["bp_rp"]
    ok = np.isfinite(g) & np.isfinite(c)
    ok &= (g >= G_LO) & (g <= G_HI)
    ok &= (c > COL_LO) & (c < COL_HI)
    if "astrometric_params_solved" in tab:
        # 31 = five-parameter, 95 = six-parameter; both carry a proper motion.
        ps = tab["astrometric_params_solved"]
        ok &= (ps == 31) | (ps == 95)
    pm_a, pm_d = tab["pmra"], tab["pmdec"]
    ok &= np.isfinite(pm_a) & np.isfinite(pm_d)
    ok &= np.isfinite(tab["pmra_error"]) & np.isfinite(tab["pmdec_error"])
    off = np.hypot(pm_a - MU_A, pm_d - MU_D)
    ok &= off <= radius
    if aperture is not None:
        ok &= aperture
    return ok


def select_gums(tab, radius=R_WIN):
    g = tab["Gmag"]
    c = tab["GBmag"] - tab["GRmag"]
    ok = np.isfinite(g) & np.isfinite(c)
    ok &= (g >= G_LO) & (g <= G_HI)
    ok &= (c > COL_LO) & (c < COL_HI)
    off = np.hypot(tab["pmRA"] - MU_A, tab["pmDE"] - MU_D)
    ok &= off <= radius
    return ok


def poisson_interval(n, level=0.95, two_sided=True):
    """Garwood exact interval on a Poisson mean."""
    a = (1.0 - level) / 2.0 if two_sided else 1.0 - level
    lo = 0.0 if n == 0 else stats.chi2.ppf(a, 2 * n) / 2.0
    hi = stats.chi2.ppf(1.0 - a, 2 * n + 2) / 2.0
    return lo, hi


def jeffreys_interval(n, level=0.95):
    """Equal-tail credible interval for a Poisson mean, Jeffreys prior."""
    a = (1.0 - level) / 2.0
    lo = stats.gamma.ppf(a, n + 0.5)
    hi = stats.gamma.ppf(1.0 - a, n + 0.5)
    return lo, hi


def bootstrap_cones(counts, weights, nboot=NBOOT, seed=SEED):
    """Bootstrap the six cones; return the 2.5 and 97.5 percentiles of N_exp."""
    rng = np.random.default_rng(seed)
    counts = np.asarray(counts, dtype=float)
    weights = np.asarray(weights, dtype=float)
    k = len(counts)
    idx = rng.integers(0, k, size=(nboot, k))
    dens = (counts[idx] * weights[idx]).mean(axis=1) / A_CONE
    n_exp = dens * A_ANN
    return float(np.percentile(n_exp, 2.5)), float(np.percentile(n_exp, 97.5))


def polygon_area_deg2(lon, lat):
    """Area of a spherical polygon on the unit sphere, converted to deg^2."""
    lon = np.radians(np.asarray(lon, dtype=float))
    lat = np.radians(np.asarray(lat, dtype=float))
    x = np.cos(lat) * np.cos(lon)
    y = np.cos(lat) * np.sin(lon)
    z = np.sin(lat)
    v = np.stack([x, y, z], axis=1)
    v_next = np.roll(v, -1, axis=0)
    cross = np.cross(v, v_next)
    num = np.linalg.norm(cross, axis=1)
    den = 1.0 + (v * v_next).sum(axis=1)
    omega = np.arctan2(num, den).sum()
    return float(omega * (180.0 / np.pi) ** 2)


def write_json(name, payload):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print("wrote", path)
    return path
