#!/usr/bin/env python3
"""Q1i: fixed Data Central cones; Data Lab + VizieR table inventory for DESI/NSC/SkyMapper."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715
DC = "https://datacentral.org.au/vo/tap/sync"
PT = f"POINT('ICRS', CAST(ra AS DOUBLE), CAST(dec AS DOUBLE))"
CIR = f"CIRCLE('ICRS', {RA}, {DEC}, 0.0833)"


def cone(ep, table, cols="*", rad=0.0833, n=20, save=None, tag=None, pt=None):
    pt = pt or PT
    cir = f"CIRCLE('ICRS', {RA}, {DEC}, {rad})"
    q = f"SELECT TOP {n} {cols} FROM {table} WHERE 1=CONTAINS({pt}, {cir})"
    st, txt, dt = tap(ep, q, save=save, timeout=180)
    report(tag or table, st, txt, dt)
    if txt.lstrip().startswith("<") and "ERROR" in txt[:600]:
        print("   ERR:", txt[txt.find("QUERY_STATUS"):txt.find("QUERY_STATUS") + 400].replace("\n", " ")[:400])
    return csv_rows(txt), txt


print("### Data Central 6dFGS / 2dFGRS / GALAH ###")
rows, txt = cone(DC, '"6dfgs_fdr".SPECTRA', "*", 0.0833, 20, "q1i-6dfgs-spectra.csv", "6dfgs.SPECTRA")
print("rows:", rows if rows is None else len(rows))
if rows:
    print(txt.splitlines()[0])
    for r in rows[:5]:
        print("   ", str(r)[:250])

rows, txt = cone(DC, '"6dfgs_fdr".TARGET', "*", 0.0833, 20, "q1i-6dfgs-target.csv", "6dfgs.TARGET")
print("rows:", rows if rows is None else len(rows))

rows, txt = cone(DC, '"2dfgrs_fdr".spec_all', "*", 0.0833, 20, "q1i-2dfgrs.csv", "2dfgrs.spec_all")
print("rows:", rows if rows is None else len(rows))

rows, txt = cone(DC, "galah_dr3.main_star", "*", 0.0833, 20, "q1i-galah.csv", "galah.main_star")
print("rows:", rows if rows is None else len(rows))

print("\n### Data Lab table inventory ###")
for kw in ["desi", "nsc", "skymapper", "gaia", "smash", "decam", "vphas"]:
    q = ("SELECT table_name, description FROM TAP_SCHEMA.tables WHERE "
         f"LOWER(table_name) LIKE '%{kw}%'")
    st, txt, dt = tap("datalab", q, save=f"q1i-datalab-{kw}.csv", timeout=120)
    rows = csv_rows(txt) or []
    print(f"-- datalab '{kw}': status {st}, {len(rows)}")
    for r in rows[:12]:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:70])

print("\n### VizieR: does table quoting work? try APOGEE DR17 ###")
st, txt, dt = tap("vizier", "SELECT TOP 1 table_name FROM TAP_SCHEMA.tables WHERE table_name LIKE '%286%'", timeout=120)
print("viz 286:", st, txt[:300])
q = ("SELECT TOP 5 ra, dec FROM \"III/286/catalog\" WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
     f"CIRCLE('ICRS',{RA},{DEC},0.5))")
st, txt, dt = tap("vizier", q, timeout=180)
report("vizier/apogee-dr17 30arcmin", st, txt, dt)
print(txt[:600])
