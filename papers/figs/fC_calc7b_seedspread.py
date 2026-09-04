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

import fC_calc7b_d2forecast as M   # noqa: E402  (shipped module, read-only import)

JSON_PATH = os.path.join(M.HERE, "fC_calc7b_d2forecast.json")
SHIPPED = open(JSON_PATH, "rb").read()
shipped_doc = json.loads(SHIPPED)
shipped_cells = {(c["truth"], c["sigma"], c["N"]): c for c in shipped_doc["cells"]}

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
              date="2026-08-24", N_REAL=200,
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
