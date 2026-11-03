#!/usr/bin/env python3
"""Q3c: HEASARC X-ray/UV cones via VOTable (inventory + pointings + catalogues)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap_vot

RA, DEC = 201.41849, -47.05715


def sep(ra, dec):
    return math.hypot((ra - RA) * 3600 * math.cos(math.radians(DEC)), (dec - DEC) * 3600)


def q(label, adql, save=None, maxrows=10, verbose=False):
    st, txt, dt, rows = tap_vot("heasarc", adql, timeout=300, save=save)
    n = "ERR" if rows is None else len(rows)
    print(f"[{label}] status={st} rows={n} dt={dt:.0f}s")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 200].replace("\n", " ") if i >= 0 else txt[:160])
    elif rows:
        print("    cols:", ", ".join(list(rows[0].keys())[:18]))
        for r in rows[:maxrows]:
            if verbose:
                print("    ", str(r)[:300])
            else:
                try:
                    s = sep(float(r.get("ra", "nan")), float(r.get("dec", "nan")))
                    print(f"     sep={s:8.1f}\" {str(r)[:220]}")
                except Exception:
                    print("    ", str(r)[:240])
    return rows


print("### HEASARC inventory ###")
st, txt, dt, rows = tap_vot("heasarc", "SELECT table_name, description FROM TAP_SCHEMA.tables", timeout=300,
                            save="q3c-heasarc-tables.xml")
print("inventory status", st, "rows", "ERR" if rows is None else len(rows))
if rows:
    keys = list(rows[0].keys())
    print("keys:", keys)
    import re
    want = re.compile(r"swift|xmm|chandra|csc|galex|rosat|erass|erosita|uvot|first|nvss|sumss|racs", re.I)
    hits = [r for r in rows if want.search(str(r.get("table_name", "")))]
    print(f"{len(hits)} matching tables")
    for r in hits[:80]:
        print("    ", r.get("table_name"), "|", (r.get("description") or "")[:65])
