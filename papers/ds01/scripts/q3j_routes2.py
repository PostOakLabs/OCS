#!/usr/bin/env python3
"""Q3j: alternative HEASARC routes that return readable tables."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import get_text

RA, DEC = 201.41849, -47.05715

cands = {
    "cone_cgi_2sxps": f"https://heasarc.gsfc.nasa.gov/cgi-bin/vo/cone/coneGet.pl?table=swift2sxps&RA={RA}&DEC={DEC}&SR=0.05&verb=3",
    "cone_cgi_swiftmastr": f"https://heasarc.gsfc.nasa.gov/cgi-bin/vo/cone/coneGet.pl?table=swiftmastr&RA={RA}&DEC={DEC}&SR=0.3&verb=3",
    "w3query_swift2sxps": f"https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/w3query.pl?tablehead=name%3Dswift2sxps&RA={RA}&DEC={DEC}&Radius=3&Action=Query&ResultMax=10&displaymode=Text",
    "w3query_swiftmastr": f"https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/w3query.pl?tablehead=name%3Dswiftmastr&RA={RA}&DEC={DEC}&Radius=30&Action=Query&ResultMax=20&displaymode=Text",
}
for k, u in cands.items():
    try:
        st, body = get_text(u, timeout=180)
        print(f"=== {k}: status {st} len {len(body)}")
        print(body[:900].replace("\n", " "))
        print()
    except Exception as e:
        print(f"=== {k}: {type(e).__name__} {str(e)[:180]}\n")
