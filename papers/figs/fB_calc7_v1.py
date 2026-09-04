"""Paper B falsifiability-scorecard robustness under pre-committed alternative
half-grade codings. Deterministic; no randomness. Originally R7-CALC-AB (run
plan in 0xAlpha/results/R7-CALC-AB.md section 0.2); K4 retargeted under
R9-B-1 (B-R9-01/B-R9-02) once the original K4 (Migration C5 withdrawal)
became a no-op against the table's own R8 fix. Output: fB_calc7_scorecard.json
(this directory).
"""
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEX = os.path.join(ROOT, "paper", "inward-review.tex")

MEMBERS = ["Migration", "Transcension", "Stellivores", "Aestivation", "BH computing", "MTH"]
CRITERIA = ["C1", "C2", "C3", "C4", "C5", "C6"]

failures = []


def check(name, ok, detail):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}: {detail}")
    if not ok:
        failures.append(name)


# ---------------------------------------------------------------- gate G-B1: transcribe from source
def parse_scorecard():
    sym = {r"\sfull": "F", r"\shalf": "H", r"\snone": "N"}
    rows = {}
    for ln in open(TEX, encoding="utf-8").read().split("\n"):
        name = next((m for m in MEMBERS if ln.startswith(m)), None)
        if name is None or not ln.rstrip().endswith("\\\\"):
            continue
        cells = ln.split("&")
        vals = []
        for cell in cells[1:]:
            hit = [v for k, v in sym.items() if k in cell]
            vals.append(hit[0] if len(hit) == 1 else None)
        if len(vals) == 6 and all(vals):
            rows[name] = vals
    return rows


grid = parse_scorecard()
check("G-B1 transcription", sorted(grid) == sorted(MEMBERS) and all(len(v) == 6 for v in grid.values()),
      f"{len(grid)} rows x 6 symbols parsed from tab:scorecard")

# ---------------------------------------------------------------- codings (pre-committed)
VAL = {"F": 1.0, "H": 0.5, "N": 0.0}


def apply_coding(grid, coding):
    g = {k: list(v) for k, v in grid.items()}
    if coding == "K1_strict_floor":
        for k in g:
            g[k] = ["N" if v == "H" else v for v in g[k]]
    elif coding == "K2_generous_ceil":
        for k in g:
            g[k] = ["F" if v == "H" else v for v in g[k]]
    elif coding == "K3_two_leg_min":
        # documented split cell(s): Aestivation-C3 (none leg + full leg, averaged to half at :298)
        g["Aestivation"][CRITERIA.index("C3")] = "N"
    elif coding == "K4_mth_c5_contingent_withdraw":
        # R9-B-1 (B-R9-01/B-R9-02): the printed table already carries Migration's
        # C5 as none (the v1 K4 -- Migration C5 H->N -- became a no-op once the
        # table itself was fixed under R8; a withdrawal coding needs a live target).
        # The remaining contingent half-grade in tab:scorecard is MTH's C5, credited
        # only via the limit-tightening restatement of Paper A's T1 (:299). This
        # coding withdraws that contingent credit to test the ranking as-registered.
        g["MTH"][CRITERIA.index("C5")] = "N"
    return g


CODINGS = ["B0_printed", "K1_strict_floor", "K2_generous_ceil", "K3_two_leg_min", "K4_mth_c5_contingent_withdraw"]
results = {}
for code in CODINGS:
    g = apply_coding(grid, code)
    sums = {k: sum(VAL[v] for v in g[k]) for k in MEMBERS}
    order = sorted(MEMBERS, key=lambda k: (-sums[k], MEMBERS.index(k)))
    ranks = {}
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and sums[order[j + 1]] == sums[order[i]]:
            j += 1
        for kk in order[i:j + 1]:
            ranks[kk] = f"{i + 1}-{j + 1}" if j > i else str(i + 1)
        i = j + 1
    col_leaders = {}
    for ci, cr in enumerate(CRITERIA):
        best = max(VAL[g[k][ci]] for k in MEMBERS)
        col_leaders[cr] = [k for k in MEMBERS if VAL[g[k][ci]] == best and best > 0] or ["(all zero)"]
    c6_order = sorted(MEMBERS, key=lambda k: -VAL[g[k][5]])
    results[code] = dict(grid=g, sums=sums, rank_order=order, ranks=ranks,
                         column_leaders=col_leaders, c6_top=c6_order[0],
                         c6_tied=[k for k in MEMBERS if VAL[g[k][5]] == VAL[g[c6_order[0]][5]]])
    print(f"\n=== {code}")
    for k in MEMBERS:
        print(f"  {k:14s} {''.join({'F': '#', 'H': 'o', 'N': '.'}[v] for v in g[k])}  sum={sums[k]:.1f}  rank={ranks[k]}")
    print(f"  order: {' > '.join(order)}")
    print(f"  C6 top: {results[code]['c6_tied']}")

# pairwise relation changes vs baseline
print("\n--- pairwise order/tie changes vs B0 ---")


def rel(x, y):
    return "<" if x < y else (">" if x > y else "=")


base_sums = results["B0_printed"]["sums"]
flips = []
for code in CODINGS[1:]:
    s = results[code]["sums"]
    fl = [(a, b) for a in MEMBERS for b in MEMBERS
          if a < b and rel(base_sums[a], base_sums[b]) != rel(s[a], s[b])]
    flips.append((code, fl))
    print(f"{code}: {len(fl)} pair(s) changed: {fl}")

check("G-B2 C6 distribution", VAL[grid["MTH"][5]] == 0.5
      and sum(1 for k in MEMBERS if grid[k][5] == "H") == 4
      and sum(1 for k in MEMBERS if grid[k][5] == "N") == 2,
      "max achieved C6 grade is half; four members at half, two at none "
      "(reproduces the B-M6 evidence)")

json.dump(dict(
    meta=dict(wu="R9-B-1", part="Paper B scorecard robustness (supersedes R7-CALC-AB)", date="2026-09-03",
              source="paper/inward-review.tex tab:scorecard :314-319",
              metric="row sums, full=1 half=0.5 none=0"),
    printed_grid={k: grid[k] for k in MEMBERS},
    codings=results,
    pairwise_flips_vs_B0={code: fl for code, fl in flips},
), open(os.path.join(HERE, "fB_calc7_scorecard.json"), "w"), indent=1)

print("\n" + "=" * 72)
if failures:
    print("FAILURES:", failures)
raise SystemExit(1 if failures else 0)
