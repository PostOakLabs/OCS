#!/usr/bin/env python3
"""Q3i: debug the VOTable parser against a known-non-empty HEASARC response."""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap_vot, OUT, vot_rows

st, txt, dt, rows = tap_vot("heasarc", "SELECT COUNT(*) AS n FROM swift2sxps", timeout=300,
                            save="q3i-count.xml")
print("status", st, "parsed rows:", rows)
print("--- raw tail ---")
print(txt[-900:])
print("--- tag walk ---")
root = ET.fromstring(txt)
for el in root.iter():
    print("  ", el.tag, dict(el.attrib) if el.attrib else "")
