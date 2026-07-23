#!/usr/bin/env python3
"""check-sitemap.py - every tools/ page must be listed in BOTH sitemaps.

Companion to check-orphans.py. That gate proves a tool is reachable and in the
tools/index.html registry; this one proves it is also discoverable through the
two published sitemaps:
  - sitemap.xml  (machine sitemap, submitted to search engines)
  - sitemap.html (human sitemap page)

Rule: for every tools/*.html on disk except index.html (the hub itself) and the
data/ + lib/ subtrees, a /tools/<file> link must appear in each sitemap. Drift
in either direction (a new tool nobody added, a deleted tool still listed) fails
the build. Mirrors the additive-count philosophy of the other Job-1 gates.

Run: python3 scripts/check-sitemap.py
Exit 0 clean, 1 on any missing/stale entry.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, "tools")

# Pages that are not standalone tool pages and are listed elsewhere (Main pages
# section) or are not meant to appear in the tool listings.
HUB_EXEMPT = {"index.html"}


def disk_tools():
    return {f for f in os.listdir(TOOLS)
            if f.endswith(".html") and f not in HUB_EXEMPT}


def linked_in(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    return set(re.findall(r"/tools/([A-Za-z0-9_-]+\.html)", text))


def main():
    disk = disk_tools()
    problems = []
    for label, rel in (("sitemap.xml", "sitemap.xml"),
                       ("sitemap.html", "sitemap.html")):
        path = os.path.join(REPO, rel)
        listed = linked_in(path)
        missing = sorted(disk - listed)
        stale = sorted(f for f in (listed - disk)
                       if os.path.sep not in f and f not in HUB_EXEMPT
                       and not os.path.exists(os.path.join(TOOLS, f)))
        if missing:
            problems.append(f"{label}: {len(missing)} tool page(s) not listed:\n    "
                            + "\n    ".join(missing))
        if stale:
            problems.append(f"{label}: {len(stale)} listed page(s) no longer on disk:\n    "
                            + "\n    ".join(stale))

    if problems:
        print("[FAIL] sitemap coverage drift:")
        for p in problems:
            print("  " + p)
        print("\nAdd the missing /tools/<file> entries to the sitemap(s), or remove "
              "stale ones. Both sitemap.xml and sitemap.html must list every "
              "tools/*.html page (except the index.html hub).")
        return 1

    print(f"[OK] Both sitemaps list all {len(disk)} tools/ pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
