#!/usr/bin/env python3
"""Q3b: HEASARC TAP access pattern + first cones."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap, csv_rows

RA, DEC = 201.41849, -47.05715

print("### TAP_SCHEMA.tables sample ###")
st, txt, dt = tap("heasarc", "SELECT TOP 5 * FROM TAP_SCHEMA.tables", timeout=120)
print("status", st, txt[:600].replace("\n", " "))

for t in ["swiftxrt", "swiftuvotssc2", "xmm", "chandra", "csc", "galex", "rosat", "erass1"]:
    st, txt, dt = tap("heasarc", f"SELECT TOP 1 * FROM {t}", timeout=90)
    ok = not txt.lstrip().startswith("<VOTABLE") or "ERROR" not in txt[:400]
    print(f"[{t}] status={st} :: {txt[:180].replace(chr(10),' ')}")
