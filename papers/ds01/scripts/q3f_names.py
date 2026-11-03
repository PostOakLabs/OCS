#!/usr/bin/env python3
"""Q3f: HEASARC observation-log table names + UVOT/GALEX/eROSITA catalogue names."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import OUT

body = open(os.path.join(OUT, "heasarc-tables.html"), encoding="utf-8").read()
pairs = re.findall(r"<table>\s*<name>([^<]+)</name>\s*<description>(.*?)</description>", body, re.S)
by_name = {n: d.replace("\n", " ").strip() for n, d in pairs}

print("--- observation logs (name contains 'master') ---")
for n, d in pairs:
    if "master" in n.lower():
        print(f"  {n:22s} {d[:75]}")

print("\n--- tables with 'swift' or 'uvot' in the NAME ---")
for n, d in pairs:
    if re.search(r"swift|uvot", n, re.I):
        print(f"  {n:22s} {d[:75]}")

print("\n--- tables with 'galex' in the NAME ---")
for n, d in pairs:
    if re.search(r"galex", n, re.I):
        print(f"  {n:22s} {d[:75]}")

print("\n--- tables with 'erass' or 'erosita' in the NAME ---")
for n, d in pairs:
    if re.search(r"erass|erosita", n, re.I):
        print(f"  {n:22s} {d[:75]}")

print("\n--- tables with 'rosat' in the NAME ---")
for n, d in pairs:
    if re.search(r"rosat", n, re.I):
        print(f"  {n:22s} {d[:75]}")

print("\n--- XMM observation log candidates ---")
for n, d in pairs:
    if re.search(r"^xmm|^xsa|xmmmaster|observation", n, re.I) or "XMM-Newton Observations" in d:
        print(f"  {n:22s} {d[:75]}")

print("\n--- radio tables on HEASARC (sumss/mrc/racs/nvss) ---")
for n, d in pairs:
    if re.search(r"sumss|racs|nvss|mrc|first|vlass|gleam", n, re.I):
        print(f"  {n:22s} {d[:75]}")
