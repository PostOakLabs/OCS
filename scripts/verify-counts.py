#!/usr/bin/env python3
"""
verify-counts.py — OCS count-drift SSOT + gate (AINumbers 3-layer model).

Layer 1 (SSOT):  derive_counts() computes every canonical number from the
                 filesystem / manifest. The ONLY place a count is computed.
Layer 2 (marks): published counts are sentinel-marked so they are greppable
                 and the gate diffs only marked spans (no CSS-noise false hits):
                   - HTML: <span ... data-count="KEY">NN ...</span>
                   - JSON: a named field (manifest _meta.toolCount, agent-card tool_count)
                   - llms.txt: anchored regex on known phrases
Layer 3 (gate):  --check (default) re-derives, compares every sentinel, prints
                 'file: key expected N got M', exits 1 on any drift.
                 --fix rewrites every sentinel from derive_counts() (idempotent).

Usage (from repo root):
    python scripts/verify-counts.py            # check (CI default), exit 1 on drift
    python scripts/verify-counts.py --fix      # rewrite sentinels to match SSOT

Zero dependencies (stdlib only). Runs on the ubuntu-latest python3 in CI.

Coverage: global counts (calculators/workflows/scenarios/hubs/proposals/mcp_tools/
mcp_chains) via JSON/HTML/llms sentinels, AND per-section card-count consistency in
tools/index.html (each section's displayed count == tool-cards rendered in it;
scenarios/workflows card counts must also equal the filesystem file count).
"""
import json, re, sys, glob, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Hub/dashboard pages in tools/ that are NOT calculators.
HUBS = ["index.html", "falsification-hub.html", "imbh-evidence-dashboard.html",
        "imbh-narrative.html", "pathways.html"]


def _n(pattern):
    return len(glob.glob(os.path.join(REPO, pattern)))


def derive_counts():
    """Single source of truth — every canonical count derived from disk + manifest."""
    tools_all = _n("tools/*.html")
    workflows = _n("tools/workflow-*.html")
    scenarios = _n("tools/scenario-*.html")
    hubs = sum(1 for h in HUBS if os.path.isfile(os.path.join(REPO, "tools", h)))
    calculators = tools_all - workflows - scenarios - hubs
    proposals = _n("proposal*.html")  # proposals.html + proposal_*.html at repo root
    manifest = json.load(open(os.path.join(REPO, "tools/data/tools-manifest.json"), encoding="utf-8"))
    return {
        "calculators": calculators,
        "workflows": workflows,
        "scenarios": scenarios,
        "hubs": hubs,
        "proposals": proposals,
        "mcp_tools": len(manifest.get("tools", {})),
        "mcp_chains": len(manifest.get("chains", {})),
    }


# ── Sentinel registry ───────────────────────────────────────────────────────
# JSON field sentinels: (relative path, JSON field name, count-key). The field
# name must be UNIQUE in the file. Read via json (robust), but --fix does a
# surgical text replace of `"field": N` so original formatting is preserved
# (no full re-serialize / reformat).
JSON_SENTINELS = [
    ("tools/data/tools-manifest.json", "toolCount", "mcp_tools"),
    (".well-known/agent-card.json", "tool_count", "mcp_tools"),
]

# HTML files scanned for data-count="KEY" markers (KEY must be a derive_counts key).
HTML_SENTINEL_FILES = ["tools/index.html", "tools/falsification-hub.html"]

# llms.txt anchored regex sentinels: (compiled regex w/ ONE numeric group, count-key).
# The optional trailing '+' is consumed so --fix writes an exact number (no fuzzy '+').
LLMS_SENTINELS = [
    (re.compile(r"(\d+)\+?(?= calculators)"), "calculators"),
    (re.compile(r"(\d+)\+?(?= browser-based interactive calculators)"), "calculators"),
    (re.compile(r"(\d+)(?=(?: multi-stage)? workflow chains)"), "workflows"),
    (re.compile(r"(\d+)(?= scenario chains)"), "scenarios"),
    (re.compile(r"(\d+)(?= hubs/dashboards)"), "hubs"),
]

# data-count="KEY" then optional attrs then '>' then optional ws then the integer.
HTML_MARK = re.compile(r'(data-count="([a-z_]+)"[^>]*>\s*)(\d+)')


def _find_json_field(text, field):
    """Return (regex_match, int_value) for `"field": N` in raw JSON text, or (None, None)."""
    m = re.search(r'("%s"\s*:\s*)(\d+)' % re.escape(field), text)
    return (m, int(m.group(2))) if m else (None, None)


def run(fix=False):
    counts = derive_counts()
    drift = []   # (file, key, expected, got)
    fixed = []   # (file, key, newval)

    # JSON field sentinels — surgical text replace, no reformat
    for rel, field, key in JSON_SENTINELS:
        fp = os.path.join(REPO, rel)
        text = open(fp, encoding="utf-8").read()
        m, got = _find_json_field(text, field)
        if m is None:
            drift.append((rel, key, counts[key], "MISSING")); continue
        exp = counts[key]
        if got != exp:
            if fix:
                text = text[:m.start()] + m.group(1) + str(exp) + text[m.end():]
                open(fp, "w", encoding="utf-8").write(text)
                fixed.append((rel, key, exp))
            else:
                drift.append((rel, key, exp, got))

    # HTML data-count sentinels
    for rel in HTML_SENTINEL_FILES:
        fp = os.path.join(REPO, rel)
        src = open(fp, encoding="utf-8").read()
        changed = False
        def repl(m):
            nonlocal changed
            key = m.group(2)
            if key not in counts:
                drift.append((rel, key, "UNKNOWN-KEY", m.group(3))); return m.group(0)
            exp, got = counts[key], int(m.group(3))
            if got != exp:
                if fix:
                    changed = True; fixed.append((rel, key, exp))
                    return m.group(1) + str(exp)
                drift.append((rel, key, exp, got))
            return m.group(0)
        new = HTML_MARK.sub(repl, src)
        if fix and changed:
            open(fp, "w", encoding="utf-8").write(new)

    # llms.txt regex sentinels
    fp = os.path.join(REPO, "llms.txt")
    src = open(fp, encoding="utf-8").read()
    changed = False
    for rx, key in LLMS_SENTINELS:
        exp = counts[key]
        def repl(m, exp=exp, key=key):
            nonlocal changed
            got = int(m.group(1))
            if got != exp:
                if fix:
                    changed = True; fixed.append(("llms.txt", key, exp))
                    return str(exp)
                drift.append(("llms.txt", key, exp, got))
            return m.group(0)
        src = rx.sub(repl, src)
    if fix and changed:
        open(fp, "w", encoding="utf-8").write(src)

    # Phase 2 — per-section card-count consistency in tools/index.html.
    # Rule: the displayed section-count number must equal the number of tool-cards
    # rendered in that section. For tool-category/fiction sections (unit 'tools'/'pages')
    # the card count IS the SSOT, so --fix sets the displayed number to it. For
    # scenarios/workflows sections the card count must equal the filesystem file count
    # (report-only: a mismatch means a card is missing/extra and must be authored/removed
    # by hand — a number edit would just hide the gap).
    idx = os.path.join(REPO, "tools/index.html")
    src = open(idx, encoding="utf-8").read()
    SECT_SPAN = re.compile(r'<span class="section-count"[^>]*>(\d+)\s+(tools|pages|scenarios|workflows)</span>')
    GLOBAL_UNIT = {"scenarios": "scenarios", "workflows": "workflows"}
    parts = re.split(r'(<section\b)', src)
    out, changed, i = parts[0], False, 1
    while i < len(parts):
        block = parts[i] + parts[i + 1]
        m = SECT_SPAN.search(block)
        if m:
            disp, unit = int(m.group(1)), m.group(2)
            cards = len(re.findall(r'class="tool-card"', block))
            label = f"tools/index.html [{unit} section]"
            if unit in GLOBAL_UNIT:
                exp = counts[GLOBAL_UNIT[unit]]
                if cards != exp:
                    drift.append((label, "card_count", exp, cards))
            elif disp != cards:
                if fix:
                    s, e = m.span(1)
                    block = block[:s] + str(cards) + block[e:]
                    changed = True
                    fixed.append((label, "section_count", cards))
                else:
                    drift.append((label, "section_count", cards, disp))
        out += block
        i += 2
    if fix and changed:
        open(idx, "w", encoding="utf-8").write(out)

    # ── Report ──
    print("Derived counts (SSOT):")
    for k, v in counts.items():
        print(f"  {k:14} {v}")
    print()
    if fix:
        if fixed:
            print(f"Fixed {len(fixed)} sentinel(s):")
            for f, k, v in fixed:
                print(f"  {f}: {k} -> {v}")
        else:
            print("No sentinels needed fixing — already in sync.")
        return 0
    if drift:
        print(f"[FAIL] COUNT DRIFT -- {len(drift)} stale sentinel(s):")
        for f, k, exp, got in drift:
            print(f"  {f}: {k} expected {exp} got {got}")
        print("\nFix: python scripts/verify-counts.py --fix  (then commit)")
        return 1
    print("[OK] All count sentinels match the SSOT.")
    return 0


if __name__ == "__main__":
    sys.exit(run(fix="--fix" in sys.argv[1:]))
