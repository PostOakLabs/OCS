#!/usr/bin/env python3
"""Q2/Q4/Q5/Q6: NSC measure, SkyMapper, VPHAS/VVV, WISE/2MASS, radio, 4FGL."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows

RA, DEC = 201.41849, -47.05715


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def show(label, rows, txt=None, maxrows=8, sort=True):
    n = "ERR" if rows is None else len(rows)
    print(f"[{label}] rows={n}")
    if rows is None:
        if txt:
            i = txt.find("QUERY_STATUS")
            print("    ERR:", txt[i:i + 200].replace("\n", " ") if i >= 0 else txt[:160])
        return
    if rows:
        print("    cols:", ", ".join(list(rows[0].keys())[:20]))
        items = rows
        if sort:
            try:
                items = sorted(rows, key=lambda r: sep(float(r["ra"]), float(r["dec"])))
            except Exception:
                pass
        for r in items[:maxrows]:
            try:
                sd = f"sep={sep(float(r['ra']), float(r['dec'])):8.1f}\""
            except Exception:
                sd = "sep=?     "
            print(f"     {sd} {str(r)[:230]}")


print("### NSC DR2 per-epoch measurements at DS-01 (0.5 arcmin) ###")
st, txt, dt = tap("datalab", "SELECT TOP 40 id,ra,dec,mjd,flux,g,r,i,z,y,imag FROM nsc_dr2.measure "
                  "WHERE ra BETWEEN 201.4165 AND 201.4205 AND dec BETWEEN -47.0595 AND -47.0548",
                  save="q2-nsc-measure2.csv", timeout=300)
show("nsc_dr2.measure", csv_rows(txt), txt, 12)

print("\n### NSC DR2 object nearest to DS-01 (search 1 arcmin, sort) ###")
st, txt, dt = tap("datalab", "SELECT TOP 200 ra,dec,pmra,pmdec,pmraerr,pmdecerr,imag,gmag,rmag,umag,"
                  "ymag,zmag,mjd,ndet FROM nsc_dr2.object WHERE ra BETWEEN 201.405 AND 201.432 AND "
                  "dec BETWEEN -47.068 AND -47.046", save="q2-nsc-object2.csv", timeout=300)
rows = csv_rows(txt)
show("nsc_dr2.object", rows, txt, 6)

print("\n### SkyMapper DR4 ###")
st, txt, dt = tap("datalab", "SELECT table_name FROM TAP_SCHEMA.tables WHERE table_name LIKE 'skymapper_dr4%'",
                  timeout=120)
tabs = [r["table_name"].strip("'") for r in (csv_rows(txt) or [])]
print("tables:", tabs)
for t in tabs:
    if "master" in t or "object" in t or "dr4" in t.split(".")[-1]:
        st, txt, dt = tap("datalab", f"SELECT TOP 5 * FROM {t} WHERE ra BETWEEN 201.41 AND 201.43 AND "
                          "dec BETWEEN -47.07 AND -47.05", save=f"q2-sm-{t.replace('.','-')}.csv", timeout=240)
        show(t, csv_rows(txt), txt, 4)
        break

print("\n### WISE / unWISE / 2MASS at DS-01 (IRSA TAP) ###")
for tbl in ["allwise_p3as_psd", "unwise_dr1.object", "fp_psc"]:
    st, txt, dt = tap("irsa", f"SELECT TOP 5 * FROM {tbl} WHERE ra BETWEEN 201.415 AND 201.422 AND "
                      "dec BETWEEN -47.060 AND -47.054", save=f"q6-{tbl.replace('.','-')}.csv", timeout=240)
    show(tbl, csv_rows(txt), txt, 3)

print("\n### NEOWISE-R single-exposure photometry (IRSA) ###")
for tbl in ["neowiser_p1bs_psd", "neowiser_p1fa_psd"]:
    st, txt, dt = tap("irsa", f"SELECT TOP 40 ra,dec,mjd,w1mpro,w1sigmpro,w2mpro,w2sigmpro,cc_flags,qi_fact "
                      "FROM " + tbl + " WHERE ra BETWEEN 201.4165 AND 201.4205 AND dec BETWEEN -47.0595 "
                      "AND -47.0548", save=f"q2-{tbl}.csv", timeout=300)
    show(tbl, csv_rows(txt), txt, 6)

print("\n### Radio: CASDA RACS catalogue cone (2 arcmin) ###")
st, txt, dt = tap("casda", "SELECT table_name FROM TAP_SCHEMA.tables", timeout=180)
tabs = [r["table_name"].strip("'") for r in (csv_rows(txt) or [])]
print("casda tables:", tabs[:40])
for t in ["casda.continuum_component", "casda.continuum_island"]:
    if t in tabs or True:
        st, txt, dt = tap("casda", f"SELECT TOP 20 * FROM {t} WHERE ra BETWEEN 201.385 AND 201.452 AND "
                          "dec BETWEEN -47.091 AND -47.023", save=f"q4-{t.split('.')[-1]}.csv", timeout=300)
        show(t, csv_rows(txt), txt, 6)

print("\n### Radio: VizieR SUMSS / MGPS-2 / RACS ###")
for tbl, racol, deccol in [('"VIII/81/sumss"', "RAJ2000", "DEJ2000"),
                           ('"VIII/82/mgps"', "RAJ2000", "DEJ2000"),
                           ('"VIII/92/racs"', "RAJ2000", "DEJ2000")]:
    st, txt, dt = tap("vizier", f"SELECT TOP 5 * FROM {tbl} WHERE {racol} BETWEEN 201.39 AND 201.45 AND "
                      f"{deccol} BETWEEN -47.09 AND -47.03", timeout=180)
    show(f"vizier {tbl}", csv_rows(txt), txt, 3)

print("\n### 4FGL-DR4 via VizieR ###")
st, txt, dt = tap("vizier", "SELECT TOP 20 table_name, description FROM TAP_SCHEMA.tables WHERE "
                  "description LIKE '%4FGL%'", timeout=180)
rows = csv_rows(txt) or []
for r in rows:
    print("   ", r.get("table_name"), "|", (r.get("description") or "")[:90])
