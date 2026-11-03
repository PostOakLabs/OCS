#!/usr/bin/env python3
"""Q3d: find the HEASARC access route that works, and locate X-ray table names."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import get_text, OUT

RA, DEC = 201.41849, -47.05715

st, body = get_text("https://heasarc.gsfc.nasa.gov/xamin/vo/tap/tables", timeout=120)
open(os.path.join(OUT, "heasarc-tables.html"), "w", encoding="utf-8").write(body)
print("tables page:", st, len(body))

for kw in ["swiftxrt", "swiftuvotssc", "xmm", "chanmaster", "galex", "rosat", "erass"]:
    n = len(re.findall(kw, body, re.I))
    m = re.search(kw, body, re.I)
    ctx = body[max(0, m.start() - 120):m.start() + 60].replace("\n", " ") if m else ""
    print(f"  {kw:14s} n={n:5d} ctx={ctx[:170]}")

print("\n=== VO cone search endpoint test (swiftxrt) ===")
urls = [
    f"https://heasarc.gsfc.nasa.gov/cgi-bin/vo/cone/coneGet.pl?table=swiftxrt&RA={RA}&DEC={DEC}&SR=0.05&verb=3&display=0",
    f"https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/w3query.pl?tablehead=name%3Dswiftxrt&RA={RA}&DEC={DEC}&Radius=3&Action=Query&ResultMax=20",
]
for u in urls:
    try:
        st, body = get_text(u, timeout=120)
        print(f"-- {u[:95]} -> {st} len {len(body)}")
        print("   ", body[:500].replace("\n", " "))
    except Exception as e:
        print(f"-- {u[:95]} -> {type(e).__name__} {str(e)[:150]}")
