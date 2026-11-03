#!/usr/bin/env python3
"""Q1d: the 2 ESO ObsCore rows in the cone, plus a dbo.raw cone."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


hdr("ESO ObsCore rows within 2 arcmin")
q = ("SELECT obs_id, obs_collection, obs_creator_name, instrument_name, dataproduct_type, "
     "calib_level, s_ra, s_dec, s_fov, t_min, t_max, em_min, em_max, access_url, access_estsize "
     "FROM ivoa.obscore WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), "
     f"CIRCLE('ICRS', {RA}, {DEC}, 0.0333))")
st, txt, dt = tap("eso", q, save="q1d-eso-obscore-rows.csv", timeout=420)
report("eso/obscore-rows", st, txt, dt)
print(txt[:3000])

hdr("ESO ObsCore rows within 10 arcmin (context: is the field observed at all?)")
q = ("SELECT COUNT(*) AS n FROM ivoa.obscore WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), "
     f"CIRCLE('ICRS', {RA}, {DEC}, 0.1667))")
st, txt, dt = tap("eso", q, save="q1d-eso-obscore-count10.csv", timeout=420)
report("eso/obscore-count-10as", st, txt, dt)

hdr("ESO dbo.raw cone 2 arcmin")
q = ("SELECT TOP 100 ra, dec, mjd_obs, instrument, dp_id, dp_cat, dp_tech, exposure, ob_id "
     "FROM dbo.raw WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
     f"CIRCLE('ICRS', {RA}, {DEC}, 0.0333))")
st, txt, dt = tap("eso", q, save="q1d-eso-raw-cone.csv", timeout=300)
report("eso/raw-cone", st, txt, dt)
print(txt[:2500])
