#!/usr/bin/env python3
"""Q2+Q3+Q4: X-ray/UV/time-domain/radio cones across the free archives."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def show(label, st, txt, save=None, maxrows=8, key=None):
    rows = csv_rows(txt)
    n = "n/a" if rows is None else len(rows)
    print(f"[{label}] status={st} rows={n}")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 240].replace("\n", " ") if i >= 0 else txt[:180])
        return None
    if rows:
        print("    hdr:", txt.splitlines()[0][:220])
        for r in rows[:maxrows]:
            print("    ", str(r)[:240])
    return rows


# ---------------------------------------------------------------- HEASARC inventory
print("### HEASARC table inventory ###")
for kw in ["swift", "xmm", "chandra", "csc", "galex", "rosat", "erass", "erosita", "nustar", "uvot"]:
    st, txt, dt = tap("heasarc", "SELECT table_name, description FROM TAP_SCHEMA.tables WHERE "
                      f"LOWER(table_name) LIKE '%{kw}%'", timeout=120)
    rows = csv_rows(txt) or []
    print(f"-- {kw}: {len(rows)}")
    for r in rows[:14]:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:70])
