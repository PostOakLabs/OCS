#!/usr/bin/env python3
"""Q1g: fix VizieR TAP_SCHEMA access; test MAST REST API; list Data Central tables."""
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report, get_text, TAP

print("=== VizieR TAP_SCHEMA.tables raw sample ===")
st, txt, dt = tap("vizier", "SELECT TOP 3 * FROM TAP_SCHEMA.tables", save="q1g-vizier-tapschema.csv", timeout=120)
report("vizier/schema", st, txt, dt)
print(txt[:1200])

print("\n=== VizieR TAP_SCHEMA.columns sample ===")
st, txt, dt = tap("vizier", "SELECT TOP 5 * FROM TAP_SCHEMA.columns", timeout=120)
report("vizier/cols", st, txt, dt)
print(txt[:800])

print("\n=== VizieR: direct cone on a known table (6dFGS III/259/6dfgs) ===")
q = ("SELECT TOP 5 * FROM \"III/259/6dfgs\" WHERE 1=CONTAINS(POINT('ICRS',RAJ2000,DEJ2000),"
     "CIRCLE('ICRS',201.41849,-47.05715,0.05))")
st, txt, dt = tap("vizier", q, timeout=180)
report("vizier/6dfgs", st, txt, dt)
print(txt[:800])

print("\n=== MAST REST API cone (anonymous) ===")
try:
    st, body = get_text("https://mast.stsci.edu/api/v0/invoke", timeout=60)
    print("GET invoke:", st, body[:200])
except Exception as e:
    print("GET invoke err:", e)

req = {
    "service": "Mast.Caom.Cone",
    "params": {"ra": 201.41849, "dec": -47.05715, "radius": 0.05},
    "format": "json",
    "pagesize": 50,
    "page": 1,
}
url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.parse.quote(json.dumps(req))
try:
    st, body = get_text(url, timeout=120)
    print("MAST cone status:", st)
    print(body[:1500])
except Exception as e:
    print("MAST cone err:", type(e).__name__, e)

print("\n=== Data Central TAP tables ===")
st, txt, dt = tap("https://datacentral.org.au/vo/tap/sync", "SELECT table_name, description FROM TAP_SCHEMA.tables", timeout=120)
report("dc/tables", st, txt, dt)
print(txt[:3000])
