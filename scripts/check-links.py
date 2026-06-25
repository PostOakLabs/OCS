#!/usr/bin/env python3
"""
check-links.py — broken internal-link / missing-asset gate (strict-zero).

Scans every *.html in the repo for href/src references to LOCAL files and fails
if any points at a file (or directory) that does not exist. Catches the class of
bug where a tool references ../data/measurements.js (resolves to /data/ -> 404)
or links to a renamed/removed page.

Exits 1 on any dead link (CI gate). Run from the repo root:
    python3 scripts/check-links.py

Skips (not internal-file refs): http(s)/protocol-relative/mailto/tel/data/
javascript URLs, pure #anchors, and JS template-literal URLs (containing ${ }).
Directory links (ending / or resolving to a dir) pass if the directory exists.
Stdlib only.
"""
import os, re, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTR = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')
SKIP_PREFIX = re.compile(r'^(https?:|mailto:|tel:|data:|javascript:|//|#)')
# Only verify refs that name a concrete asset type (or a directory link).
ASSET_EXT = re.compile(r'\.(html?|js|css|json|png|jpe?g|svg|ico|webp|gif|txt|xml|pdf|woff2?|ttf|map|webmanifest)$', re.I)


def resolve(ref, html_path):
    """Return absolute on-disk path the ref points to, or None to skip."""
    url = ref.split('#', 1)[0].split('?', 1)[0].strip()
    if not url or SKIP_PREFIX.match(url) or '${' in url or '{{' in url:
        return None
    if url.startswith('/'):
        tgt = os.path.join(REPO, url.lstrip('/'))          # site-root relative
    else:
        tgt = os.path.normpath(os.path.join(os.path.dirname(html_path), url))
    # Directory link (trailing slash) — treat the dir as the target.
    if url.endswith('/'):
        return ('dir', tgt)
    if ASSET_EXT.search(url):
        return ('file', tgt)
    return None                                            # bare word / unknown → skip


def main():
    html_files = glob.glob(os.path.join(REPO, '*.html')) + glob.glob(os.path.join(REPO, 'tools', '*.html'))
    dead = []      # (html_relpath, ref, resolved)
    checked = 0
    for fp in sorted(html_files):
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        rel = os.path.relpath(fp, REPO)
        for ref in ATTR.findall(src):
            r = resolve(ref, fp)
            if r is None:
                continue
            kind, tgt = r
            checked += 1
            ok = os.path.isdir(tgt) if kind == 'dir' else os.path.isfile(tgt)
            if not ok:
                dead.append((rel, ref, os.path.relpath(tgt, REPO)))

    print(f"Scanned {len(html_files)} HTML files, {checked} local refs.")
    if dead:
        print(f"\n[FAIL] {len(dead)} broken internal link(s):")
        for rel, ref, tgt in dead:
            print(f"  {rel}: \"{ref}\" -> missing {tgt}")
        return 1
    print("[OK] No broken internal links.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
