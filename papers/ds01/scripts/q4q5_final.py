#!/usr/bin/env python3
"""Q4/Q5/Q6 final: CASDA RACS+EMU cones, SUMSS/MGPS, 4FGL-DR4, AllWISE, SkyMapper."""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, tap_vot, csv_rows, OUT

RA, DEC = 201.41849, -47.05715


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def show(label, rows, txt=None, maxrows=6, sort=True):
    n = "ERR" if rows is None else len(rows)
    print(f"[{label}] rows={n}")
    if rows is None:
        if txt:
            i = txt.find("QUERY_STATUS")
            print("    ERR:", txt[i:i + 200].replace("\n", " ") if i >= 0 else txt[:150])
        return
    if rows:
        print("    cols:", ", ".join(list(rows[0].keys())[:18]))
        items = rows
        if sort:
            for k in ("ra", "RAJ2000"):
                if k in rows[0]:
                    try:
                        items = sorted(rows, key=lambda r: sep(float(r[k]), float(r.get("dec", r.get("DEJ2000")))))
                    except Exception:
                        pass
                    break
        for r in items[:maxrows]:
            print("     ", str(r)[:250])


BOX_2 = "ra BETWEEN 201.385 AND 201.452 AND dec BETWEEN -47.091 AND -47.023"

print("### CASDA: RACS + EMU pilot catalogue cones (2 arcmin) ###")
for t in ["AS110.racs_mid_sources_v01", "AS110.racs_mid_components_v01", "AS110.racs_low2_v02",
          "AS110.racs_high_sources_v01", "AS101.emu_ps_catalog_v01"]:
    st, txt, dt = tap("casda", f"SELECT TOP 20 * FROM {t} WHERE {BOX_2}",
                      save=f"q4-{t.replace('.', '-')}.csv", timeout=300)
    show(t, csv_rows(txt), txt, 4)

print("\n### VizieR: find SUMSS / MGPS / RACS / Fermi table names ###")
for kw in ["SUMSS", "MGPS", "RACS", "Fermi", "4FGL", "NVSS"]:
    st, txt, dt = tap("vizier", "SELECT TOP 8 table_name, description FROM TAP_SCHEMA.tables WHERE "
                      f"description LIKE '%{kw}%'", timeout=180)
    rows = csv_rows(txt) or []
    print(f"-- {kw}: {len(rows)}")
    for r in rows:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:80])

print("\n### HEASARC: Fermi-LAT catalogue tables ###")
body = open(os.path.join(OUT, "heasarc-tables.html"), encoding="utf-8").read()
pairs = re.findall(r"<table>\s*<name>([^<]+)</name>\s*<description>(.*?)</description>", body, re.S)
for n, d in pairs:
    if re.search(r"fermi|4fgl|lat", n, re.I):
        print(f"  {n:20s} {d.replace(chr(10),' ')[:80]}")

print("\n### AllWISE source at 9.6 arcsec (full row) ###")
st, txt, dt = tap("irsa", "SELECT * FROM allwise_p3as_psd WHERE ra BETWEEN 201.415 AND 201.422 AND "
                  "dec BETWEEN -47.060 AND -47.054", save="q6-allwise.csv", timeout=240)
show("allwise", csv_rows(txt), txt, 2, sort=False)

print("\n### SkyMapper DR4 master columns ###")
st, txt, dt = tap("datalab", "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name='master' AND "
                  "schema_name='skymapper_dr4'", timeout=180)
rows = csv_rows(txt) or []
cols = [r["column_name"].strip("'") for r in rows]
print("n cols:", len(cols), cols[:40])
