#!/usr/bin/env python3
"""Q1k: finish Q1 — 2dFGRS/APOGEE column names, DESI schemas, LAMOST coverage."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows

DC = "https://datacentral.org.au/vo/tap/sync"


def cols(ep, pat, label):
    st, txt, dt = tap(ep, "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name LIKE "
                      f"'{pat}'", timeout=120)
    rows = csv_rows(txt) or []
    names = [r["column_name"].strip("'") for r in rows]
    print(f"[{label}] {len(names)} cols: {', '.join(names[:60])}")
    return names


print("### 2dFGRS spec_all columns ###")
n1 = cols(DC, "%spec_all", "2dfgrs.spec_all")
print("### 6dFGS SPECTRA columns ###")
n2 = cols(DC, "%SPECTRA", "6dfgs.SPECTRA")

print("\n### APOGEE DR17: RA/DEC-like columns ###")
n3 = cols("vizier", "%286/catalog%", "apogee")
print("RA/DEC candidates:", [c for c in n3 if c.upper().startswith(("RA", "DE"))][:20])

print("\n### Data Lab schemas ###")
st, txt, dt = tap("datalab", "SELECT schema_name FROM TAP_SCHEMA.schemas", timeout=120)
rows = csv_rows(txt) or []
names = [r["schema_name"].strip("'") for r in rows]
print(len(names), "schemas")
for n in sorted(names):
    if any(k in n.lower() for k in ("desi", "nsc", "sky", "vvv", "vphas", "smash", "gaia", "splus")):
        print("   ", n)
