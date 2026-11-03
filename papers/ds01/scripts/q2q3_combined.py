#!/usr/bin/env python3
"""Q2/Q3/Q4/Q5 combined: Swift UVOT footprint, CSC, NSC DR2, SkyMapper, VPHAS+/VVV,
NEOWISE single exposure, radio (CASDA/SUMSS/MGPS), 4FGL-DR4."""
import json
import math
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, tap_vot, get_text, csv_rows, heasarc_rows

RA, DEC = 201.41849, -47.05715


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def show(label, rows, txt=None, maxrows=8, cols=None):
    n = "ERR" if rows is None else len(rows)
    print(f"[{label}] rows={n}")
    if rows is None:
        if txt:
            i = txt.find("QUERY_STATUS")
            print("    ERR:", txt[i:i + 220].replace("\n", " ") if i >= 0 else txt[:170])
        return
    if rows:
        if cols is None:
            cols = [c for c in list(rows[0].keys())[:22]]
        print("    cols:", ", ".join(cols))
        items = rows
        try:
            items = sorted(rows, key=lambda r: sep(float(r["ra"]), float(r["dec"])))
        except Exception:
            pass
        for r in items[:maxrows]:
            try:
                sd = f"sep={sep(float(r['ra']), float(r['dec'])):8.1f}\""
            except Exception:
                sd = "sep=?     "
            print(f"     {sd} {str(r)[:250]}")


# ------------------------------------------------------------------ Swift UVOT footprint
print("### Swift UVOT: does any UVOT image contain DS-01? (s_region point-in-polygon) ###")
req = {"service": "Mast.Caom.Cone", "params": {"ra": RA, "dec": DEC, "radius": 0.35},
       "format": "json", "pagesize": 500, "page": 1}
url = "https://mast.stsci.edu/api/v0/invoke?request=" + urllib.parse.quote(json.dumps(req))
st, body = get_text(url, timeout=240)
d = json.loads(body)
swift = [x for x in d.get("data", []) if x.get("obs_collection") == "SWIFT"]
print("SWIFT rows within 0.35 deg:", len(swift))
json.dump(swift, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "out", "q2-swift-cone.json"), "w", encoding="utf-8"), indent=1)
for x in sorted(swift, key=lambda y: y.get("distance") or 0):
    print(f"  d={x.get('distance',0):8.1f}\" {x.get('instrument_name')} {x.get('obs_id')} "
          f"t={x.get('t_min'):.2f} expt={x.get('t_exptime')} filt={x.get('filters')} "
          f"type={x.get('dataproduct_type')}")


def in_poly(ra, dec, s_region):
    if not s_region or not s_region.upper().startswith("POLYGON"):
        return None
    nums = [float(v) for v in s_region.split()[1:]]
    pts = list(zip(nums[0::2], nums[1::2]))
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if ((y1 > dec) != (y2 > dec)) and (ra < (x2 - x1) * (dec - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


print("  point-in-polygon test (s_region):")
for x in sorted(swift, key=lambda y: y.get("distance") or 0)[:12]:
    r = in_poly(RA, DEC, x.get("s_region"))
    print(f"    {x.get('obs_id')} {x.get('instrument_name'):6s} d={x.get('distance'):8.1f}\" inside={r}")

# ------------------------------------------------------------------ Swift XRT pointings
print("\n### Swift pointings within 30 arcmin (XRT FOV radius 23.6') ###")
st, txt, dt, rows = tap_vot("heasarc", "SELECT name,obsid,ra,dec,start_time,xrt_exposure,uvot_exposure "
                            "FROM swiftmastr WHERE ra BETWEEN 201.0 AND 201.9 AND dec BETWEEN -47.5 AND -46.6",
                            timeout=300, save="q2-swift-30arcmin.xml")
show("swiftmastr 30'", rows, txt, 30, ["name", "obsid", "ra", "dec", "xrt_exposure", "uvot_exposure"])

# ------------------------------------------------------------------ Chandra Source Catalog
print("\n### Chandra Source Catalog cone (2 arcmin) ###")
for t in ["csc", "csc21", "csc2"]:
    st, txt, dt, rows = tap_vot("heasarc", f"SELECT * FROM {t} WHERE ra BETWEEN 201.35 AND 201.49 "
                                "AND dec BETWEEN -47.10 AND -47.01", timeout=300, save=f"q3-{t}.xml")
    show(f"{t} 2'", rows, txt, 6)
    if rows:
        break

# ------------------------------------------------------------------ NSC DR2
print("\n### NOIRLab Source Catalog DR2 (2 arcmin) ###")
st, txt, dt = tap("datalab", "SELECT TOP 20 * FROM nsc_dr2.object WHERE ra BETWEEN 201.39 AND 201.45 "
                  "AND dec BETWEEN -47.09 AND -47.02", save="q2-nsc-object.csv", timeout=300)
show("nsc_dr2.object", csv_rows(txt), txt, 8)
st, txt, dt = tap("datalab", "SELECT TOP 30 id,ra,dec,mjd,flux,g,r,i,z,y FROM nsc_dr2.measure WHERE ra BETWEEN 201.415 AND 201.422 "
                  "AND dec BETWEEN -47.062 AND -47.053", save="q2-nsc-measure.csv", timeout=300)
show("nsc_dr2.measure", csv_rows(txt), txt, 12)

# ------------------------------------------------------------------ SkyMapper DR4
print("\n### SkyMapper DR4 tables + cone ###")
st, txt, dt = tap("datalab", "SELECT table_name FROM TAP_SCHEMA.tables WHERE table_name LIKE 'skymapper_dr4%'",
                  timeout=120)
rows = csv_rows(txt) or []
print("tables:", [r["table_name"].strip("'") for r in rows][:20])
for t in [r["table_name"].strip("'") for r in rows][:3]:
    st, txt, dt = tap("datalab", f"SELECT TOP 10 * FROM {t} WHERE ra BETWEEN 201.41 AND 201.43 AND dec BETWEEN "
                      "-47.07 AND -47.05", save=f"q2-{t.replace('.', '-')}.csv", timeout=240)
    show(t, csv_rows(txt), txt, 6)

# ------------------------------------------------------------------ VPHAS+ / VVV (VizieR)
print("\n### VizieR: VPHAS+ / VVV / VVVX cones ###")
for tbl, racol, deccol in [('"II/348/vphas"', "RAJ2000", "DEJ2000"),
                           ('"II/376/vvv"', "RAJ2000", "DEJ2000"),
                           ('"II/348/vvv"', "RAJ2000", "DEJ2000")]:
    st, txt, dt = tap("vizier", f"SELECT TOP 5 * FROM {tbl} WHERE {racol} BETWEEN 201.40 AND 201.44 AND "
                      f"{deccol} BETWEEN -47.08 AND -47.04", timeout=180)
    show(f"vizier {tbl}", csv_rows(txt), txt, 3)
