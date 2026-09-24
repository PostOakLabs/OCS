#!/usr/bin/env python3
"""
check-tag-balance.py — truncation gate for every non-archive HTML page (P0-01).

Born from the three truncated pages found 2026-09-24 (tools/index.html,
tools/optical-seti.html, tools/scenario-imbh-evidence.html each ended mid-token
with an unclosed <script> and no </html>; scripts/syntax-check.mjs:42-58 skips
unclosed script blocks, which is why all three shipped green).

Checks, byte-level only (bytes.count — the grep in this workspace is ugrep and
has returned silent 0 matches for '</html>' in a 710 KB file containing it):
  (a) file contains at least one '</html>'
  (b) count('<script') == count('</script>')
  (c) file ends with '</html>' modulo trailing whitespace

Scope: every *.html under the repo root except the archive/ directory and any
dot-directory (.git etc.). Zero dependencies (stdlib only). Runs on the
ubuntu-latest python3 in CI.

Usage (from repo root):
    python scripts/check-tag-balance.py            # scan, exit 1 on any failure
    python scripts/check-tag-balance.py --selftest # write a deliberately
        # truncated temp page into the repo root, assert the scan FAILS on it
        # (and names it), remove it, then assert the clean tree PASSES.
"""
import os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"archive"}  # archived pages are historical record, not served


def iter_html(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        )
        for name in sorted(filenames):
            if name.lower().endswith(".html"):
                yield os.path.join(dirpath, name)


def failures(root):
    bad = []
    scanned = 0
    for path in iter_html(root):
        scanned += 1
        with open(path, "rb") as f:
            data = f.read()
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        opens = data.count(b"<script")
        closes = data.count(b"</script>")
        if data.count(b"</html>") < 1:
            bad.append(f"{rel}: no </html> anywhere in file")
        if opens != closes:
            bad.append(
                f"{rel}: <script> count {opens} != </script> count {closes}"
            )
        if not data.rstrip().endswith(b"</html>"):
            bad.append(f"{rel}: does not end with </html>")
    return scanned, bad


def main():
    if "--selftest" in sys.argv:
        probe = os.path.join(REPO, "selftest-truncated-page.html")
        try:
            with open(probe, "wb") as f:
                f.write(
                    b"<!DOCTYPE html>\n<html><head><title>selftest</title>"
                    b"</head><body><script>\nvar x = 1;\nclr."
                )
            scanned, bad = failures(REPO)
            caught = [b for b in bad if b.startswith("selftest-truncated-page.html")]
            if not caught:
                print("[FAIL] selftest: truncated probe page was NOT caught")
                return 1
            print(f"[selftest] probe page caught, as required:")
            for line in caught:
                print(f"  {line}")
        finally:
            if os.path.exists(probe):
                os.remove(probe)
        scanned, bad = failures(REPO)
        if bad:
            print(f"[FAIL] selftest: clean tree still reports {len(bad)} failure(s)")
            for line in bad:
                print(f"  {line}")
            return 1
        print(f"[selftest] clean tree passes ({scanned} files scanned)")
        return 0

    scanned, bad = failures(REPO)
    print(f"Scanned {scanned} HTML files (byte-level tag-balance).")
    if bad:
        print(f"\n[FAIL] {len(bad)} truncation/tag-balance failure(s):")
        for line in bad:
            print(f"  {line}")
        print("\n  A page here is truncated or has unbalanced <script> tags.")
        print("  Restore the missing tail from git history; never hand-append.")
        return 1
    print("OK: every page contains </html>, script tags balance, all end </html>.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
