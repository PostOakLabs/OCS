#!/usr/bin/env python3
"""Q1e: every ESO product within 10 arcmin, with separations, to test for coverage of DS-01."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715


def sep_arcsec(ra, dec):
    dra = (ra - RA) * 3600.0 * math.cos(math.radians(DEC))
    ddec = (dec - DEC) * 3600.0
    return math.hypot(dra, ddec)


q = ("SELECT obs_id, obs_collection, instrument_name, dataproduct_type, calib_level, "
     "s_ra, s_dec, s_fov, t_min, em_min, em_max, access_estsize "
     "FROM ivoa.obscore WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), "
     f"CIRCLE('ICRS', {RA}, {DEC}, 0.1667))")
st, txt, dt = tap("eso", q, save="q1e-eso-10arcmin.csv", timeout=420)
report("eso/obscore-10arcmin", st, txt, dt)
rows = csv_rows(txt) or []
print(f"rows={len(rows)}")
print(f"{'sep_arcsec':>10} {'fov_as':>8} {'type':<10} {'instr':<12} {'coll':<8} {'estsize':>9}  obs_id")
out = []
for r in rows:
    try:
        s = sep_arcsec(float(r["s_ra"]), float(r["s_dec"]))
    except Exception:
        continue
    try:
        fov = float(r["s_fov"]) * 3600.0
    except Exception:
        fov = float("nan")
    out.append((s, fov, r))
out.sort(key=lambda t: t[0])
for s, fov, r in out:
    covers = "  <== COULD COVER" if (fov == fov and s < fov / 2.0 + 1.2) else ""
    print(f"{s:10.1f} {fov:8.1f} {r.get('dataproduct_type',''):<10} {r.get('instrument_name',''):<12} "
          f"{r.get('obs_collection',''):<8} {r.get('access_estsize',''):>9}  {r.get('obs_id','')}{covers}")
