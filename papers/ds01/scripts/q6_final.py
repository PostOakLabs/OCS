#!/usr/bin/env python3
"""Q6 final: full NSC photometry of DS-01, SkyMapper DR4, EMU pilot cone."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows

RA, DEC = 201.41849, -47.05715

print("### NSC DR2 object row for DS-01 (full) ###")
st, txt, dt = tap("datalab", "SELECT * FROM nsc_dr2.object WHERE ra BETWEEN 201.4183 AND 201.4187 AND "
                  "dec BETWEEN -47.0573 AND -47.0570", save="q6-nsc-ds01-full.csv", timeout=240)
rows = csv_rows(txt)
if rows:
    for k, v in rows[0].items():
        print(f"   {k:24s} {v}")
else:
    i = txt.find("QUERY_STATUS")
    print("ERR:", txt[i:i + 200].replace("\n", " "))

print("\n### SkyMapper DR4 master cone (raj2000/dej2000) ###")
st, txt, dt = tap("datalab", "SELECT TOP 10 * FROM skymapper_dr4.master WHERE raj2000 BETWEEN 201.41 AND "
                  "201.43 AND dej2000 BETWEEN -47.07 AND -47.05", save="q6-sm2.csv", timeout=240)
rows = csv_rows(txt)
print("rows:", "ERR" if rows is None else len(rows))
if rows:
    print("  cols:", ", ".join(list(rows[0].keys())[:40]))
    for r in rows[:5]:
        print("   ", str(r)[:330])
elif txt:
    i = txt.find("QUERY_STATUS")
    print("ERR:", txt[i:i + 220].replace("\n", " "))

print("\n### EMU pilot catalogue cone (AS101, 2 arcmin) ###")
st, txt, dt = tap("casda", "SELECT TOP 20 * FROM \"AS101.emu_ps_catalog_v01\" WHERE ra_deg BETWEEN "
                  "201.385 AND 201.452 AND dec_deg BETWEEN -47.091 AND -47.023",
                  save="q4-emu-pilot.csv", timeout=300)
rows = csv_rows(txt)
print("rows:", "ERR" if rows is None else len(rows))
if rows:
    print("  cols:", ", ".join(list(rows[0].keys())[:22]))
    for r in rows[:6]:
        print("   ", str(r)[:280])
elif txt:
    i = txt.find("QUERY_STATUS")
    print("ERR:", txt[i:i + 200].replace("\n", " "))
