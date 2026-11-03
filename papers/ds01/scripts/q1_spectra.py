#!/usr/bin/env python3
"""Q1: spectrum or RV anywhere?  ESO TAP + Gaia DR3 + VizieR/other spectral archives."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import TAP, tap, csv_rows, report, OUT

RA, DEC = 201.41849, -47.05715
ID = 6083772968079356544


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# ---------------------------------------------------------------- Gaia DR3
hdr("Gaia DR3 target row (RV, XP, RVS availability)")
q = (
    "SELECT source_id, ra, dec, phot_g_mean_mag, bp_rp, parallax, pmra, pmdec, ruwe, "
    "radial_velocity, radial_velocity_error, rv_template_teff, rv_nb_transits, "
    "has_xp_continuous, has_xp_sampled, has_rvs, has_epoch_photometry, "
    "phot_variable_flag, ipd_gof_harmonic_amplitude, astrometric_excess_noise, "
    "teff_gspphot, logg_gspphot, distance_gspphot "
    f"FROM gaiadr3.gaia_source WHERE source_id = {ID}"
)
st, txt, dt = tap("gaia", q, save="q1-gaia-target.csv")
report("gaia/target", st, txt, dt)
rows = csv_rows(txt)
if rows:
    for k, v in rows[0].items():
        print(f"    {k:32s} {v}")

# ---------------------------------------------------------------- ESO TAP
hdr("ESO TAP: which tables exist (spectra-related)")
st, txt, dt = tap(
    "eso",
    "SELECT table_name, description FROM TAP_SCHEMA.tables WHERE "
    "table_name LIKE '%raw%' OR table_name LIKE '%spec%' OR table_name LIKE '%cube%'",
    save="q1-eso-tables.csv",
)
report("eso/tables", st, txt, dt)
rows = csv_rows(txt)
if rows:
    for r in rows:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:70])

# ---------------------------------------------------------------- ESO raw cone
hdr("ESO TAP dbo.raw cone search r=90 arcsec")
q = (
    "SELECT TOP 200 ra, dec, mjd_obs, instrument, dp_id, dp_cat, exptime, object, "
    "target_name, prog_id, s_ra, s_dec "
    "FROM dbo.raw "
    f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {RA}, {DEC}, 0.025))"
)
st, txt, dt = tap("eso", q, save="q1-eso-raw-cone.csv")
report("eso/raw cone 90as", st, txt, dt)
rows = csv_rows(txt)
if rows:
    for r in rows:
        print("    ", json.dumps(r)[:220])

# ---------------------------------------------------------------- ESO obscore
hdr("ESO TAP ivoa.obscore cone search r=120 arcsec (spectra only)")
q = (
    "SELECT TOP 300 obs_id, obs_collection, instrument_name, dataproduct_type, calib_level, "
    "s_ra, s_dec, s_fov, t_min, t_max, em_min, em_max, access_url, access_estsize "
    "FROM ivoa.obscore "
    f"WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), CIRCLE('ICRS', {RA}, {DEC}, 0.0333))"
)
st, txt, dt = tap("eso", q, save="q1-eso-obscore-cone.csv")
report("eso/obscore cone 120as", st, txt, dt)
rows = csv_rows(txt)
if rows:
    print(f"    {len(rows)} rows")
    for r in rows[:40]:
        print("    ", json.dumps(r)[:230])
