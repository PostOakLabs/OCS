#!/usr/bin/env python3
"""Q1f: locate spectral-survey tables in VizieR, and test MAST/Data Central TAP."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

for kw in ["6df", "lamost", "apogee", "galah", "desi", "rave", "segue", "sdss", "southern", "vphas"]:
    q = ("SELECT table_name, description FROM TAP_SCHEMA.tables WHERE "
         f"LOWER(table_name) LIKE '%{kw}%' OR LOWER(description) LIKE '%{kw}%'")
    st, txt, dt = tap("vizier", q, save=f"q1f-vizier-{kw}.csv", timeout=120)
    rows = csv_rows(txt) or []
    print(f"\n--- vizier keyword '{kw}': {len(rows)} tables (status {st}) ---")
    for r in rows[:25]:
        print("   ", r.get("table_name"), "|", (r.get("description") or "")[:95])

print("\n=== MAST TAP test ===")
for ep in ["https://mast.stsci.edu/vo/tap/sync", "https://mast.stsci.edu/vo/tap"]:
    st, txt, dt = tap(ep, "SELECT TOP 1 1 AS one FROM TAP_SCHEMA.tables", timeout=90)
    report(f"mast {ep}", st, txt, dt)

print("\n=== Data Central (AAO) TAP test ===")
for ep in ["https://datacentral.org.au/tap/sync", "https://datacentral.org.au/vo/tap/sync"]:
    st, txt, dt = tap(ep, "SELECT TOP 1 1 AS one FROM TAP_SCHEMA.tables", timeout=90)
    report(f"dc {ep}", st, txt, dt)
