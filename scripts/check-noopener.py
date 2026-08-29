#!/usr/bin/env python3
"""check-noopener.py - every target="_blank" anchor must carry rel="noopener".

Follows AUDIT-HY4-REPO §1.2: 81 anchors opened new tabs without rel="noopener",
leaving the opened page a window.opener handle back into this site (reverse-
tabnabbing). Strict-zero gate, matching the style of check-links.py /
check-orphans.py.

Run: python3 scripts/check-noopener.py
Exit 0 clean, 1 on any target="_blank" anchor missing rel="noopener".
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

TAG_RE = re.compile(r'<a\b[^>]*target="_blank"[^>]*>')
REL_NOOPENER_RE = re.compile(r'rel="[^"]*\bnoopener\b[^"]*"')


def main():
    offenders = []
    for path in glob.glob(os.path.join(REPO, "**", "*.html"), recursive=True):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in TAG_RE.finditer(text):
            tag = m.group(0)
            if not REL_NOOPENER_RE.search(tag):
                line = text.count("\n", 0, m.start()) + 1
                offenders.append((os.path.relpath(path, REPO), line, tag))

    if offenders:
        print(f"::error::{len(offenders)} target=\"_blank\" anchor(s) missing rel=\"noopener\":")
        for f, line, tag in offenders:
            print(f"  {f}:{line}: {tag}")
        return 1

    print("  all target=\"_blank\" anchors carry rel=\"noopener\".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
