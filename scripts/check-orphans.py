#!/usr/bin/env python3
"""
check-orphans.py — stranded-page gate (strict-zero).

Companion to check-links.py. That script catches links pointing at files that do
not exist; this one catches the mirror bug: files that exist but nothing links to.
A page nobody can reach is invisible to readers and to crawlers, and the failure is
silent — the site builds, deploys, and looks fine.

Two independent checks:

  1. REACHABILITY — breadth-first walk from the site roots (index.html, sitemap.html)
     following internal href/src refs. Any tracked .html not reached is an orphan.
     Catches whole stranded clusters: an island hub plus its members is unreachable
     even though every page in it is well linked internally.

  2. TOOL REGISTRY — every tools/*.html calculator must be linked from
     tools/index.html directly. Transitive reachability is not enough here: a tool
     linked only from a narrative page is absent from the tool index that readers
     and the MCP manifest treat as the registry. This is the drift that ships tools
     nobody can find from the hub.

Exits 1 on any orphan. Run from the repo root:
    python3 scripts/check-orphans.py

Deliberate exceptions go in ALLOW below, each with a reason. Stdlib only.
"""
import os, re, sys, glob
from collections import deque

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Site entry points. Anything the public can reach must hang off one of these.
ROOTS = ["index.html", "sitemap.html"]

# Hub/dashboard pages in tools/ that are NOT calculators (mirrors verify-counts.py).
TOOL_HUBS = {"index.html", "falsification-hub.html", "imbh-evidence-dashboard.html",
             "imbh-narrative.html", "pathways.html"}

# Deliberate exceptions — path relative to repo root -> reason. Keep this short;
# an entry here is a promise that the page is unreachable on purpose.
ALLOW = {
    "papers/figs/index.html":   "directory listing for the figure-source mirror; reached as /papers/figs/",
    "papers/source/index.html": "directory listing for the paper-source mirror; reached as /papers/source/",
    "404.html":                 "served by the host on miss, never linked",
}

ATTR = re.compile(r'(?:href|src)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', re.I)
SKIP_PREFIX = re.compile(r'^(https?:|mailto:|tel:|data:|javascript:|//|#)', re.I)
# Strip script/style/comments so runtime-built and commented-out hrefs don't count
# as real links (mirrors check-links.py).
STRIP = re.compile(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->', re.I | re.S)
SKIP_DIRS = {'.git', '.github', 'node_modules'}


def all_html():
    """Every .html file in the repo, as repo-relative posix paths."""
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.lower().endswith(('.html', '.htm')):
                rel = os.path.relpath(os.path.join(root, f), REPO)
                out.append(rel.replace(os.sep, '/'))
    return sorted(out)


def links_from(rel):
    """Repo-relative .html targets linked from the given page."""
    src = STRIP.sub(' ', open(os.path.join(REPO, rel), encoding='utf-8', errors='replace').read())
    here = os.path.dirname(rel)
    out = set()
    for m in ATTR.finditer(src):
        url = (m.group(1) or m.group(2)).split('#', 1)[0].split('?', 1)[0].strip()
        if not url or SKIP_PREFIX.match(url) or '${' in url or '{{' in url:
            continue
        # A directory link resolves to that directory's index.html.
        if url.endswith('/'):
            url += 'index.html'
        if not url.lower().endswith(('.html', '.htm')):
            continue
        tgt = url.lstrip('/') if url.startswith('/') else os.path.normpath(os.path.join(here, url))
        out.add(tgt.replace(os.sep, '/'))
    return out


def main():
    pages = all_html()
    known = set(pages)

    # ── Check 1: reachability from the roots ────────────────────────────────
    seen, queue = set(), deque()
    for r in ROOTS:
        if r not in known:
            print(f"[FAIL] root page missing: {r}")
            return 1
        seen.add(r); queue.append(r)
    while queue:
        for tgt in links_from(queue.popleft()):
            if tgt in known and tgt not in seen:
                seen.add(tgt); queue.append(tgt)
    orphans = [p for p in pages if p not in seen and p not in ALLOW]

    # ── Check 2: every calculator is in the tool registry ───────────────────
    registry = links_from("tools/index.html")
    unregistered = []
    for fp in sorted(glob.glob(os.path.join(REPO, "tools", "*.html"))):
        name = os.path.basename(fp)
        rel = f"tools/{name}"
        if name in TOOL_HUBS or rel in ALLOW:
            continue
        if rel not in registry:
            unregistered.append(rel)

    # ── Report ──
    print(f"Scanned {len(pages)} HTML files; {len(seen)} reachable from {', '.join(ROOTS)}.")
    if orphans:
        print(f"\n[FAIL] {len(orphans)} page(s) unreachable from any site root:")
        for p in orphans:
            print(f"  {p}")
        print("\n  Link each from a hub (sitemap.html, tools/index.html, or a topic page),")
        print("  or add it to ALLOW in this script with a reason.")
    if unregistered:
        print(f"\n[FAIL] {len(unregistered)} tool(s) not linked from tools/index.html:")
        for p in unregistered:
            print(f"  {p}")
        print("\n  Add a tool-card for each, then run: python3 scripts/verify-counts.py --fix")
    if not orphans and not unregistered:
        print("[OK] No stranded pages; every tool is in the registry.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
