#!/usr/bin/env python3
"""Q3e: extract HEASARC table names from the cached 10 MB table list."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import OUT

body = open(os.path.join(OUT, "heasarc-tables.html"), encoding="utf-8").read()
pairs = re.findall(r"<table>\s*<name>([^<]+)</name>\s*<description>(.*?)</description>", body, re.S)
print("total tables:", len(pairs))
want = re.compile(r"swift|xmm|chandra|chanmaster|cxo|galex|rosat|erass|erosita|nustar|suzaku|asca", re.I)
hits = [(n, d.replace("\n", " ")[:80]) for n, d in pairs if want.search(n) or want.search(d)]
print("matching tables:", len(hits))
for n, d in hits:
    print(f"  {n:28s} {d}")
