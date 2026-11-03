#!/usr/bin/env python3
"""Q1j: box-based cone checks (robust on any TAP) for the remaining spectral surveys."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, report

RA, DEC = 201.41849, -47.05715
DC = "https://datacentral.org.au/vo/tap/sync"


def box(rad_deg):
    dra = rad_deg / math.cos(math.radians(DEC))
    return (RA - dra, RA + dra, DEC - rad_deg, DEC + rad_deg)


def boxq(table, cols="*", rad=0.0833, n=30, racol="ra", deccol="dec"):
    r0, r1, d0, d1 = box(rad)
    return (f"SELECT TOP {n} {cols} FROM {table} WHERE {racol} BETWEEN {r0:.6f} AND {r1:.6f} "
            f"AND {deccol} BETWEEN {d0:.6f} AND {d1:.6f}")


def run(ep, label, q, save=None, verbose=False):
    st, txt, dt = tap(ep, q, save=save, timeout=180)
    rows = csv_rows(txt)
    n = "n/a" if rows is None else len(rows)
    print(f"[{label}] status={st} rows={n} dt={dt:.1f}s")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 300].replace("\n", " ") if i >= 0 else txt[:200])
    elif verbose and rows:
        print("    hdr:", txt.splitlines()[0][:220])
        for r in rows[:6]:
            print("    ", str(r)[:250])
    return rows


print("### Data Central: 6dFGS / 2dFGRS / GALAH (box, 5 arcmin) ###")
run(DC, "6dfgs.SPECTRA", boxq('"6dfgs_fdr".SPECTRA'), "q1j-6dfgs-spectra.csv", True)
run(DC, "6dfgs.TARGET", boxq('"6dfgs_fdr".TARGET'), "q1j-6dfgs-target.csv", True)
run(DC, "2dfgrs.spec_all", boxq('"2dfgrs_fdr".spec_all'), "q1j-2dfgrs.csv", True)
run(DC, "galah.main_star", boxq("galah_dr3.main_star"), "q1j-galah.csv", True)

print("\n### VizieR: APOGEE DR17 column names ###")
st, txt, dt = tap("vizier", "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name LIKE '%286/catalog%'",
                  save="q1j-apogee-cols.csv", timeout=120)
rows = csv_rows(txt) or []
print("cols:", [r["column_name"] for r in rows][:40])

print("\n### VizieR: APOGEE DR17 box 30 arcmin (if column names known) ###")
if rows:
    names = [r["column_name"] for r in rows]
    ra_c = next((c for c in names if c.lower() in ("ra", "raj2000")), None)
    de_c = next((c for c in names if c.lower() in ("dec", "dej2000")), None)
    print("using", ra_c, de_c)
    if ra_c and de_c:
        run("vizier", "apogee", boxq('"III/286/catalog"', f"{ra_c},{de_c}", 0.5, 50, ra_c, de_c),
            "q1j-apogee.csv", True)

print("\n### VizieR: hunt for LAMOST / DESI / RAVE / SDSS tables by description ###")
for kw in ["LAMOST", "DESI", "RAVE", "SEGUE", "SDSS"]:
    st, txt, dt = tap("vizier", "SELECT TOP 10 table_name, description FROM TAP_SCHEMA.tables WHERE "
                      f"description LIKE '%{kw}%'", timeout=120)
    rows = csv_rows(txt) or []
    print(f"-- {kw}: {len(rows)}")
    for r in rows:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:75])

print("\n### Data Lab: DESI iron tables ###")
for kw in ["desi_dr", "iron", "desi_edr", "skymapper_dr4"]:
    st, txt, dt = tap("datalab", "SELECT table_name, description FROM TAP_SCHEMA.tables WHERE "
                      f"LOWER(table_name) LIKE '%{kw}%'", timeout=120)
    rows = csv_rows(txt) or []
    print(f"-- datalab '{kw}': {len(rows)}")
    for r in rows[:15]:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:70])
