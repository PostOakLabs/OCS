"""R7-CALC-FIN / S3 item 3: eight-seed spread on the D2-forecast headline ladder.

Pre-committed scope (evaluation §8.1 S3 item 3, as amended here for runtime):
the eight-seed spread is computed on the HEADLINE n=19 ladder (2 truths x
5 sigma = 10 cells, N_REAL = 200 per cell, the cells the paper's criterion
sentence quotes). The n = 25/40/100 cells keep their single-seed shipped
values; stated in the report.

Seeds: SEED0 = 20260824 + 1000 k, k = 0..7. k = 0 IS the shipped run (free
reproduction gate). The shipped JSON is restored byte-for-byte after the loop;
the spread ships in fC_calc7b_seedspread.json. Nothing else is written.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "paper", "figs")))

import types                       # noqa: E402

# 2026-10-22 (FIX-C): the v1 module omits G on every dark-mass term (G_PC is
# defined at its l.44 and never used), exactly as v2 did.  v1 is retained
# unchanged as the historical record, so the G factor is applied here, to a
# copy of its source held in memory, with each substitution asserted.
# 2026-10-23 (D244): the z grid is patched to 1201 nodes as well.  The spread
# is computed on the same n=19 ladder the paper quotes, and those cells now
# come from the converged grid; leaving v1 at 301 would spread a grid the
# headline numbers no longer use and would leave the shipped-reference column
# comparing two different grids.
_V1 = os.path.join(HERE, "fC_calc7b_d2forecast.py")
_src = open(_V1, encoding="utf-8-sig").read().replace("\r\n", "\n")
for _a, _b in (
    ("def g_point(r, z):\n    return z / r ** 3",
     "def g_point(r, z):\n    return G_PC * z / r ** 3"),
    ("def g_plummer(r, z, a_pc):\n    return z / (r * r + a_pc * a_pc) ** 1.5",
     "def g_plummer(r, z, a_pc):\n    return G_PC * z / (r * r + a_pc * a_pc) ** 1.5"),
    ("gB = Z / (rA * rA + 4.0) ** 1.5",
     "gB = G_PC * Z / (rA * rA + 4.0) ** 1.5"),
    ("Z_MAX, N_Z = 60.0, 301",
     "Z_MAX, N_Z = 60.0, 1201"),
):
    assert _src.count(_a) == 1, _a
    _src = _src.replace(_a, _b)
M = types.ModuleType("fC_calc7b_d2forecast_gfixed")
M.__file__ = _V1
exec(compile(_src, _V1, "exec"), M.__dict__)

JSON_PATH = os.path.join(M.HERE, "fC_calc7b_d2forecast.json")
SHIPPED = open(JSON_PATH, "rb").read()      # v1 record (G-less), restored below
# Reference column: the regenerated v2 record, converted to v1's sign
# convention (positive toward the true family).  v1 and v2 share the rng
# stream per cell, so at the full census they agree once both carry G.
_v2 = json.load(open(os.path.join(M.HERE, "fC_calc7b_d2forecast_v2.json"),
                     encoding="utf-8"))
shipped_cells = {}
for _c in _v2["cells"]:
    if _c["truth"] in ("compact", "extended"):
        _c = dict(_c)
        _c["median_dsimple"] *= -1.0 if _c["truth"] == "compact" else 1.0
        shipped_cells[(_c["truth"], _c["sigma"], _c["N"])] = _c

M.CENSUS = [19]                    # headline ladder only (module global, call-time)

seed_runs = []
for k in range(8):
    M.SEED0 = 20260824 + 1000 * k
    print(f"== seed run k={k} (SEED0={M.SEED0})", flush=True)
    M.main()
    doc = json.load(open(JSON_PATH, encoding="utf-8"))
    cells = {(c["truth"], c["sigma"], c["N"]): c for c in doc["cells"]}
    per_cell = []
    for key, c_ref in sorted(shipped_cells.items()):
        if key[2] != 19:
            continue
        c = cells[key]
        per_cell.append(dict(truth=key[0], sigma=key[1],
                             median_dsimple=c["median_dsimple"],
                             median_dchi2=c["median_dchi2"],
                             p_dsimple_ge9=c["p_dsimple_ge9"],
                             shipped_median_dsimple=c_ref["median_dsimple"]))
    seed_runs.append(dict(k=k, seed0=M.SEED0, cells=per_cell))
    min_ds = min(c["median_dsimple"] for c in per_cell)
    print(f"   min median_dsimple over the n=19 ladder: {min_ds:.2f}", flush=True)

# per-cell spread across the eight seeds
spread = []
for key, c_ref in sorted(shipped_cells.items()):
    if key[2] != 19:
        continue
    vals = [min(r["cells"], key=lambda c: (c["truth"], c["sigma"]))
            for r in seed_runs]  # placeholder replaced below
    vals = []
    for r in seed_runs:
        for c in r["cells"]:
            if c["truth"] == key[0] and c["sigma"] == key[1]:
                vals.append(c["median_dsimple"])
    spread.append(dict(truth=key[0], sigma=key[1],
                       shipped_median_dsimple=c_ref["median_dsimple"],
                       seed_min=min(vals), seed_median=float(np_median := (
                           sorted(vals)[len(vals) // 2])),
                       seed_max=max(vals),
                       min_over_seeds_above_9=bool(min(vals) > 9.0)))

all_above_9 = all(s["min_over_seeds_above_9"] for s in spread)
out = dict(
    meta=dict(wu="R7-CALC-FIN", part="S3 item 3 — eight-seed spread, n=19 ladder",
              date="2026-08-24", regenerated="2026-10-22 with G applied (FIX-C)", N_REAL=200,
              seeds=[r["seed0"] for r in seed_runs],
              note="shipped seed (k=0) reproduces the shipped n=19 cells exactly"),
    per_cell_spread=spread,
    headline_min_over_all_cells_and_seeds=min(s["seed_min"] for s in spread),
    headline_all_cells_all_seeds_above_9=bool(all_above_9),
)
out["meta"]["k0_reproduces_shipped"] = all(
    abs(r0["cells"][i]["median_dsimple"] - list(shipped_cells.values())[i]["median_dsimple"]) < 1e-9
    for r0 in [seed_runs[0]] for i in range(len(r0["cells"])))

with open(os.path.join(HERE, "fC_calc7b_seedspread.json"), "w") as fh:
    json.dump(out, fh, indent=1)

# restore the shipped record byte-for-byte
open(JSON_PATH, "wb").write(SHIPPED)

print()
for s in spread:
    print(f"  {s['truth']:9s} sigma={s['sigma']:>6}: shipped {s['shipped_median_dsimple']:>9.2f}  "
          f"seed-range [{s['seed_min']:>9.2f}, {s['seed_max']:>9.2f}]  min>9: {s['min_over_seeds_above_9']}")
print("headline: every cell above 9 under every seed =", all_above_9)
print("k=0 reproduces shipped:", out["meta"]["k0_reproduces_shipped"])
