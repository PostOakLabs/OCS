#!/usr/bin/env python3
"""Q1b: ESO TAP schema discovery, then a correct cone search."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


hdr("ESO TAP_SCHEMA.tables (all)")
st, txt, dt = tap("eso", "SELECT table_name, schema_name FROM TAP_SCHEMA.tables ORDER BY schema_name, table_name",
                  save="q1b-eso-all-tables.csv")
report("eso/tables-all", st, txt, dt)
rows = csv_rows(txt)
if rows:
    print("   count:", len(rows))
    for r in rows:
        print("    ", r.get("schema_name"), ".", r.get("table_name"), sep="")

hdr("ESO dbo.raw columns")
st, txt, dt = tap("eso", "SELECT column_name, datatype FROM TAP_SCHEMA.columns WHERE table_name='raw' ORDER BY column_name",
                  save="q1b-eso-raw-cols.csv")
report("eso/raw-cols", st, txt, dt)
rows = csv_rows(txt)
if rows:
    print("   ", ", ".join(r["column_name"] for r in rows))
