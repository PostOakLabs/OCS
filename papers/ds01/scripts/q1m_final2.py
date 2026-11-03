#!/usr/bin/env python3
"""Q1m: 2dFGRS via string match, APOGEE separations, DESI DR1 box, NOIRLab POST, MAST HST spectra."""
import json
import math
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, get_text, CTX, UA

RA, DEC = 201.41849, -47.05715
DC = "https://datacentral.org.au/vo/tap/sync"


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


print("### 2dFGRS spec_all: string-prefix match ###")
q = ("SELECT TOP 50 name,OBSRAJ2000,OBSDECJ2000,Z,QUALITY FROM \"2dfgrs_fdr\".spec_all "
     "WHERE OBSRAJ2000 LIKE '201.4%' AND OBSDECJ2000 LIKE '-47.%'")
st, txt, dt = tap(DC, q, save="q1m-2dfgrs.csv", timeout=180)
rows = csv_rows(txt) or []
print(f"status={st} rows={len(rows)}")
for r in rows[:10]:
    print("   ", r)
print("  (total 2dFGRS rows overall for scale:)")
st, txt, dt = tap(DC, "SELECT COUNT(*) AS n FROM \"2dfgrs_fdr\".spec_all", timeout=120)
print("   ", txt.strip().replace("\n", " | ")[:200])
st, txt, dt = tap(DC, "SELECT MIN(OBSDECJ2000) AS dmin, MAX(OBSDECJ2000) AS dmax FROM \"2dfgrs_fdr\".spec_all",
                  timeout=180)
print("   2dFGRS dec range (string):", txt.strip().replace("\n", " | ")[:200])

print("\n### APOGEE DR17: nearest star to DS-01 ###")
q = ("SELECT RAJ2000,DEJ2000,APOGEE,Teff,SNR FROM \"III/286/catalog\" WHERE "
     "RAJ2000 BETWEEN 200.68 AND 202.16 AND DEJ2000 BETWEEN -47.56 AND -46.56")
st, txt, dt = tap("vizier", q, save="q1m-apogee.csv", timeout=180)
rows = csv_rows(txt) or []
print(f"status={st} rows={len(rows)}")
best = None
for r in rows:
    try:
        s = sep(float(r["RAJ2000"]), float(r["DEJ2000"]))
    except Exception:
        continue
    if best is None or s < best[0]:
        best = (s, r)
if best:
    print(f"   nearest APOGEE star: {best[0]:.1f} arcsec -> {best[1]}")
else:
    print("   no rows parsed")

print("\n### DESI DR1: zpix / target box (2 arcmin) ###")
for tbl, cols in [("desi_dr1.zpix", "*"), ("desi_dr1.target", "*"), ("desi_dr1.mws", "*")]:
    q = (f"SELECT TOP 10 * FROM {tbl} WHERE ra BETWEEN 201.35 AND 201.49 "
         f"AND dec BETWEEN -47.10 AND -47.01")
    st, txt, dt = tap("datalab", q, save=f"q1m-{tbl.replace('.', '-')}.csv", timeout=180)
    rows = csv_rows(txt)
    n = "n/a" if rows is None else len(rows)
    print(f"[{tbl}] status={st} rows={n}")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 220].replace("\n", " ") if i >= 0 else txt[:180])
    elif rows:
        print("    hdr:", txt.splitlines()[0][:200])
        for r in rows[:4]:
            print("    ", str(r)[:220])

print("\n### NOIRLab archive POST ###")
body = json.dumps({"outfields": ["ra", "dec", "instrument", "obs_type", "dateobs_center",
                                 "archive_filename", "md5sum", "proposal"],
                   "search": [["ra_center", RA], ["dec_center", DEC]],
                   "limit": 60}).encode()
req = urllib.request.Request("https://astroarchive.noirlab.edu/api/adv_search/find/", data=body,
                             headers={"User-Agent": UA, "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        out = r.read().decode("utf-8", "replace")
    print("status", r.status, "len", len(out))
    print(out[:2500])
    open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out",
                      "q1m-noirlab.json"), "w", encoding="utf-8").write(out)
except Exception as e:
    print("NOIRLab POST err:", type(e).__name__, str(e)[:300])

print("\n### MAST: HST spectra at the position ###")
req2 = {"service": "Mast.Caom.Cone",
        "params": {"ra": RA, "dec": DEC, "radius": 0.02},
        "format": "json", "pagesize": 200, "page": 1}
url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.parse.quote(json.dumps(req2))
st, body = get_text(url, timeout=180)
try:
    d = json.loads(body)
    data = d.get("data", [])
    print("MAST rows:", len(data))
    from collections import Counter
    print("  collections:", Counter(x.get("obs_collection") for x in data))
    print("  types:", Counter(x.get("dataproduct_type") for x in data))
    for x in data:
        if x.get("dataproduct_type") in ("spectrum", "cube"):
            print("   SPEC:", x.get("obs_collection"), x.get("instrument_name"), x.get("obs_id"),
                  x.get("t_min"), x.get("distance"))
except Exception as e:
    print("MAST parse err:", e, body[:300])
