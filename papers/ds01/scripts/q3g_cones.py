#!/usr/bin/env python3
"""Q3g: HEASARC cones at DS-01 — Swift, XMM, Chandra, ROSAT, GALEX, eROSITA, UVOT."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap_vot

RA, DEC = 201.41849, -47.05715


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def q(label, adql, save=None, maxrows=12, sortsep=False):
    st, txt, dt, rows = tap_vot("heasarc", adql, timeout=300, save=save)
    n = "ERR" if rows is None else len(rows)
    print(f"[{label}] status={st} rows={n} dt={dt:.0f}s")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 220].replace("\n", " ") if i >= 0 else txt[:160])
        return None
    if rows:
        print("    cols:", ", ".join(list(rows[0].keys())[:20]))
        items = rows
        if sortsep:
            def s(r):
                try:
                    return sep(float(r["ra"]), float(r["dec"]))
                except Exception:
                    return 9e9
            items = sorted(rows, key=s)
        for r in items[:maxrows]:
            try:
                sd = f"sep={sep(float(r['ra']), float(r['dec'])):8.1f}\""
            except Exception:
                sd = "sep=?    "
            print(f"     {sd} {str(r)[:280]}")
    return rows


BOX = (f"ra BETWEEN {RA - 0.75:.5f} AND {RA + 0.75:.5f} AND "
       f"dec BETWEEN {DEC - 0.5:.5f} AND {DEC + 0.5:.5f}")

print("### HEASARC MASTER_TABLE positional view (all missions) ###")
q("MASTER_TABLE.pos_small", f"SELECT * FROM MASTER_TABLE.pos_small WHERE {BOX}", "q3g-master-pos.xml",
  maxrows=40)

print("\n### Swift master log (pointings) 0.5 deg ###")
q("swiftmastr", f"SELECT * FROM swiftmastr WHERE {BOX}", "q3g-swiftmastr.xml", 15, True)

print("\n### Swift UVOT instrument log 0.5 deg ###")
q("swiftuvlog", f"SELECT * FROM swiftuvlog WHERE {BOX}", "q3g-swiftuvlog.xml", 15, True)

print("\n### Swift/UVOT serendipitous source catalog v1.1 (2 arcmin) ###")
q("swuvotssc", f"SELECT * FROM swuvotssc WHERE ra BETWEEN {RA - 0.03:.5f} AND {RA + 0.03:.5f} "
               f"AND dec BETWEEN {DEC - 0.0333:.5f} AND {DEC + 0.0333:.5f}", "q3g-swuvotssc.xml", 20, True)

print("\n### XMM master log 0.5 deg ###")
q("xmmmaster", f"SELECT * FROM xmmmaster WHERE {BOX}", "q3g-xmmmaster.xml", 15, True)

print("\n### XMM serendipitous source catalog 5XMM-DR15 (2 arcmin) ###")
q("xmmssc", f"SELECT * FROM xmmssc WHERE ra BETWEEN {RA - 0.03:.5f} AND {RA + 0.03:.5f} "
            f"AND dec BETWEEN {DEC - 0.0333:.5f} AND {DEC + 0.0333:.5f}", "q3g-xmmssc.xml", 20, True)

print("\n### Chandra observations 0.5 deg ###")
q("chanmaster", f"SELECT * FROM chanmaster WHERE {BOX}", "q3g-chanmaster.xml", 15, True)

print("\n### ROSAT log 0.5 deg ###")
q("rosatlog", f"SELECT * FROM rosatlog WHERE {BOX}", "q3g-rosatlog.xml", 15, True)

print("\n### GALEX observation log 0.5 deg ###")
q("galexlog", f"SELECT * FROM galexlog WHERE {BOX}", "q3g-galexlog.xml", 15, True)

print("\n### eROSITA master / eRASS1 main (2 arcmin) ###")
q("erassmastr", f"SELECT * FROM erassmastr WHERE {BOX}", "q3g-erassmastr.xml", 15, True)
q("erass1main", f"SELECT * FROM erass1main WHERE ra BETWEEN {RA - 0.05:.5f} AND {RA + 0.05:.5f} "
                f"AND dec BETWEEN {DEC - 0.05:.5f} AND {DEC + 0.05:.5f}", "q3g-erass1main.xml", 20, True)

print("\n### Already-in-hand catalogues re-checked (2SXPS / LSXPS) ###")
q("swift2sxps", f"SELECT * FROM swift2sxps WHERE ra BETWEEN {RA - 0.03:.5f} AND {RA + 0.03:.5f} "
                f"AND dec BETWEEN {DEC - 0.0333:.5f} AND {DEC + 0.0333:.5f}", "q3g-2sxps.xml", 10, True)
q("swiftlsxps", f"SELECT * FROM swiftlsxps WHERE ra BETWEEN {RA - 0.03:.5f} AND {RA + 0.03:.5f} "
                f"AND dec BETWEEN {DEC - 0.0333:.5f} AND {DEC + 0.0333:.5f}", "q3g-lsxps.xml", 10, True)
