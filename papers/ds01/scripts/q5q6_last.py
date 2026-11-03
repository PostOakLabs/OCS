#!/usr/bin/env python3
"""Q5/Q6 last batch: 4FGL-DR4 source row, AllWISE colours, SkyMapper, EMU."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, tap_vot, csv_rows

RA, DEC = 201.41849, -47.05715

print("### 4FGL-DR4 (HEASARC fermilpsc): 4FGL J1325.4-4706 ###")
st, txt, dt, rows = tap_vot("heasarc", "SELECT * FROM fermilpsc WHERE ra BETWEEN 201.0 AND 202.0 AND "
                            "dec BETWEEN -47.6 AND -46.5", timeout=300, save="q5-4fgl.xml")
print("rows:", "ERR" if rows is None else len(rows))
if rows:
    for r in rows:
        print("  ---")
        for k, v in r.items():
            print(f"    {k:28s} {v}")

print("\n### AllWISE magnitudes for the 9.6 arcsec source ###")
st, txt, dt = tap("irsa", "SELECT designation,ra,dec,w1mpro,w1sigmpro,w1snr,w2mpro,w2sigmpro,w2snr,"
                  "w3mpro,w3sigmpro,w4mpro,w4sigmpro,cc_flags,ext_flg,var_flg,ph_qual FROM allwise_p3as_psd "
                  "WHERE ra BETWEEN 201.415 AND 201.422 AND dec BETWEEN -47.060 AND -47.054",
                  save="q6-allwise2.csv", timeout=240)
print(txt.strip()[:700])

print("\n### SkyMapper DR4 master: columns + cone ###")
st, txt, dt = tap("datalab", "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name LIKE '%master%' "
                  "AND table_name LIKE '%skymapper%'", timeout=180)
rows = csv_rows(txt) or []
print("cols:", [r["column_name"].strip("'") for r in rows][:35])
st, txt, dt = tap("datalab", "SELECT TOP 10 * FROM skymapper_dr4.master WHERE ra BETWEEN 201.41 AND 201.43 "
                  "AND dec BETWEEN -47.07 AND -47.05", save="q6-skymapper.csv", timeout=240)
r2 = csv_rows(txt)
print("skymapper rows:", "ERR" if r2 is None else len(r2))
if r2:
    print("  cols:", ", ".join(list(r2[0].keys())[:30]))
    for r in r2[:4]:
        print("   ", str(r)[:300])
elif txt:
    i = txt.find("QUERY_STATUS")
    print("   ERR:", txt[i:i + 200].replace("\n", " "))

print("\n### EMU pilot catalogue (AS101) columns ###")
st, txt, dt = tap("casda", "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name LIKE "
                  "'AS101.emu_ps_catalog_v01%'", timeout=180)
rows = csv_rows(txt) or []
print("cols:", [r["column_name"].strip("'") for r in rows][:30])
