#!/usr/bin/env python3
"""Q1c: ESO cone searches done the slow-but-sure way."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


hdr("dbo.raw sample row (to learn the column names)")
st, txt, dt = tap("eso", "SELECT TOP 1 * FROM dbo.raw", save="q1c-eso-raw-1row.csv", timeout=180)
report("eso/raw-1row", st, txt, dt)

hdr("ESO ObsCore: count of rows in a 2 arcmin cone (all types)")
q = ("SELECT COUNT(*) AS n FROM ivoa.obscore WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), "
     f"CIRCLE('ICRS', {RA}, {DEC}, 0.0333))")
st, txt, dt = tap("eso", q, save="q1c-eso-obscore-count.csv", timeout=420)
report("eso/obscore-count", st, txt, dt)
