#!/usr/bin/env python3
"""Q1n / Q2a: MAST inventory at the position (Swift UVOT, GALEX, TESS, HLSP), DESI columns,
2dFGRS format check, NOIRLab API variants."""
import json
import math
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows, get_text, CTX, UA, OUT

RA, DEC = 201.41849, -47.05715
DC = "https://datacentral.org.au/vo/tap/sync"


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def mast(service, params, pagesize=300):
    req = {"service": service, "params": params, "format": "json", "pagesize": pagesize, "page": 1}
    url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.parse.quote(json.dumps(req))
    st, body = get_text(url, timeout=240)
    return json.loads(body)


print("### MAST: everything within 1.2 arcmin of DS-01 ###")
d = mast("Mast.Caom.Cone", {"ra": RA, "dec": DEC, "radius": 0.02})
data = d.get("data", [])
print("rows:", len(data))
json.dump(data, open(os.path.join(OUT, "q1n-mast-cone.json"), "w", encoding="utf-8"), indent=1)
for x in sorted(data, key=lambda y: y.get("distance") or 0):
    print(f"  d={x.get('distance',0):7.1f}\" {x.get('obs_collection'):7s} "
          f"{str(x.get('instrument_name'))[:18]:18s} {x.get('dataproduct_type'):10s} "
          f"t={x.get('t_min')} id={x.get('obs_id')} filt={x.get('filters')}")

print("\n### MAST: Swift observation 00084743001 -> data products ###")
try:
    dd = mast("Mast.Caom.Products", {"obsid": "00084743001"})
    prods = dd.get("data", [])
    print("products:", len(prods))
    for p in prods[:40]:
        print("   ", p.get("productFilename"), "|", p.get("productSubGroupDescription"),
              "|", p.get("dataURI", "")[:110], "| size", p.get("size"))
    json.dump(prods, open(os.path.join(OUT, "q1n-swift-products.json"), "w", encoding="utf-8"), indent=1)
except Exception as e:
    print("products err:", type(e).__name__, str(e)[:200])

print("\n### DESI DR1 zpix columns ###")
st, txt, dt = tap("datalab", "SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name='zpix'",
                  timeout=120)
rows = csv_rows(txt) or []
names = [r["column_name"].strip("'") for r in rows]
print(len(names), "cols:", ", ".join(names[:80]))

print("\n### 2dFGRS: sample rows to check the coordinate string format ###")
st, txt, dt = tap(DC, "SELECT TOP 3 name,OBSRAJ2000,OBSDECJ2000 FROM \"2dfgrs_fdr\".spec_all", timeout=120)
print(txt.strip().replace("\n", " | ")[:400])

print("\n### NOIRLab archive: payload variants ###")
variants = [
    {"outfields": ["ra", "dec", "instrument"], "search": [["ra", "201.41849"], ["dec", "-47.05715"]],
     "limit": 20},
    {"outfields": ["ra", "dec", "instrument"],
     "search": [[["ra", "=", "201.41849"], ["dec", "=", "-47.05715"]]], "limit": 20},
    {"outfields": ["ra", "dec", "instrument"], "search": [["ra_center", 201.41849, "dec_center", -47.05715]],
     "limit": 20},
]
for i, v in enumerate(variants):
    body = json.dumps(v).encode()
    req = urllib.request.Request("https://astroarchive.noirlab.edu/api/adv_search/find/", data=body,
                                 headers={"User-Agent": UA, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
            out = r.read().decode("utf-8", "replace")
        print(f"variant {i}: status {r.status} len {len(out)}")
        print("   ", out[:600].replace("\n", " "))
    except Exception as e:
        print(f"variant {i}: {type(e).__name__} {str(e)[:160]}")
