#!/usr/bin/env python3
"""Q1h: 6dF / 2dF / GALAH cones (Data Central) + VizieR table lookup for LAMOST/APOGEE/DESI/RAVE."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715
DC = "https://datacentral.org.au/vo/tap/sync"

print("=== Data Central: 6dFGS SPECTRA cone 5 arcmin ===")
q = ("SELECT TOP 20 * FROM 6dfgs_fdr.SPECTRA WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
     f"CIRCLE('ICRS',{RA},{DEC},0.0833))")
st, txt, dt = tap(DC, q, save="q1h-6dfgs-cone.csv", timeout=180)
report("6dfgs.SPECTRA", st, txt, dt)
print(txt[:900])

print("\n=== Data Central: 6dFGS TARGET cone 5 arcmin ===")
q = ("SELECT TOP 20 * FROM 6dfgs_fdr.TARGET WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
     f"CIRCLE('ICRS',{RA},{DEC},0.0833))")
st, txt, dt = tap(DC, q, save="q1h-6dfgs-target.csv", timeout=180)
report("6dfgs.TARGET", st, txt, dt)
print(txt[:900])

print("\n=== Data Central: 2dFGRS spec_all cone 5 arcmin ===")
q = ("SELECT TOP 20 * FROM 2dfgrs_fdr.spec_all WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
     f"CIRCLE('ICRS',{RA},{DEC},0.0833))")
st, txt, dt = tap(DC, q, save="q1h-2dfgrs-cone.csv", timeout=180)
report("2dfgrs.spec_all", st, txt, dt)
print(txt[:900])

print("\n=== Data Central: GALAH DR3 main_star cone 5 arcmin ===")
st, txt, dt = tap(DC, "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name='main_star'",
                  timeout=120)
print("galah cols status", st, txt[:400])
q = ("SELECT TOP 20 * FROM galah_dr3.main_star WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
     f"CIRCLE('ICRS',{RA},{DEC},0.0833))")
st, txt, dt = tap(DC, q, save="q1h-galah-cone.csv", timeout=180)
report("galah.main_star", st, txt, dt)
print(txt[:900])

print("\n=== VizieR TAP_SCHEMA keyword search (no LOWER) ===")
for kw in ["lamost", "apogee", "rave", "desi", "6df"]:
    q = ("SELECT TOP 15 table_name, description FROM TAP_SCHEMA.tables WHERE "
         f"table_name LIKE '%{kw}%' OR description LIKE '%{kw.upper()}%'")
    st, txt, dt = tap("vizier", q, save=f"q1h-viz-{kw}.csv", timeout=180)
    rows = csv_rows(txt) or []
    print(f"-- {kw}: status {st}, {len(rows)} rows")
    for r in rows:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:80])
