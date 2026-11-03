#!/usr/bin/env python3
"""Q1l: decisive Q1 checks — 6dF, 2dFGRS, APOGEE, DESI DR1, NOIRLab archive."""
import json
import math
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, get_text

RA, DEC = 201.41849, -47.05715
DC = "https://datacentral.org.au/vo/tap/sync"


def boxq(table, cols="*", rad=0.0833, n=30, racol="ra", deccol="dec"):
    dra = rad / math.cos(math.radians(DEC))
    return (f"SELECT TOP {n} {cols} FROM {table} WHERE {racol} BETWEEN {RA - dra:.6f} AND {RA + dra:.6f} "
            f"AND {deccol} BETWEEN {DEC - rad:.6f} AND {DEC + rad:.6f}")


def run(ep, label, q, save=None, verbose=True):
    st, txt, dt = tap(ep, q, save=save, timeout=180)
    rows = csv_rows(txt)
    n = "n/a" if rows is None else len(rows)
    print(f"[{label}] status={st} rows={n} dt={dt:.1f}s")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 260].replace("\n", " ") if i >= 0 else txt[:200])
    elif verbose and rows:
        print("    hdr:", txt.splitlines()[0][:200])
        for r in rows[:5]:
            print("    ", str(r)[:240])
    return rows


print("### 6dFGS SPECTRA (5') ###")
run(DC, "6dfgs.SPECTRA", boxq('"6dfgs_fdr".SPECTRA', "SPECID,TARGETNAME,OBSRA,OBSDEC,Z,QUALITY", 0.0833,
                              20, "OBSRA", "OBSDEC"), "q1l-6dfgs-spectra.csv")
print("### 2dFGRS spec_all (5') ###")
run(DC, "2dfgrs.spec_all", boxq('"2dfgrs_fdr".spec_all', "name,OBSRAJ2000,OBSDECJ2000,Z,QUALITY", 0.0833,
                                20, "OBSRAJ2000", "OBSDECJ2000"), "q1l-2dfgrs.csv")
print("### APOGEE DR17 (30') ###")
run("vizier", "apogee", boxq('"III/286/catalog"', "RAJ2000,DEJ2000,APOGEE,Teff,SNR", 0.5, 30,
                             "RAJ2000", "DEJ2000"), "q1l-apogee.csv")

print("\n### Data Lab desi_dr1 tables ###")
st, txt, dt = tap("datalab", "SELECT table_name FROM TAP_SCHEMA.tables WHERE table_name LIKE 'desi_dr1%'",
                  timeout=120)
rows = csv_rows(txt) or []
names = [r["table_name"].strip("'") for r in rows]
print(names)

print("\n### NOIRLab archive adv_search (cone, spectra+images) ###")
base = "https://astroarchive.noirlab.edu/api/adv_search/find/"
for search in [
    json.dumps([["ra_center", RA], ["dec_center", DEC], ["ifov_radius", 0.0333]]),
    json.dumps([["ra", RA], ["dec", DEC]]),
]:
    url = base + "?" + urllib.parse.urlencode({
        "outfields": "ra,dec,instrument,obs_type,dateobs_center,archive_filename,md5sum",
        "search": search, "limit": "50"})
    try:
        st, body = get_text(url, timeout=120)
        print(f"NOIRLab search={search[:70]} status={st}")
        print("   ", body[:800].replace("\n", " "))
    except Exception as e:
        print("NOIRLab err:", type(e).__name__, str(e)[:200])
