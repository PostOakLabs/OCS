"""R7-CALC-H / H-CALC-3 (+ P-12): three record tables from existing JSONs, no new fits.

Pre-committed in 0xAlpha/results/R7-CALC-H.md section 0.3 (commit 77cb23f).
Read-only on every source file. Output: fH_calc7_records.json (this directory).

Embargo constraints honoured: no inner quantiles anywhere; no abstract or
conclusion text proposed; numbers only.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # repo root (calc7 -> h -> paper -> root)
PAPER_H = os.path.join(ROOT, "paper", "h")

out = {}

# ---------------------------------------------------------------------------
# 1. Per-pulsar DM comparison (H-n2 / H-P1) + pulsar B derivative sign
# ---------------------------------------------------------------------------
psr = json.load(open(os.path.join(PAPER_H, "data", "pulsars.json"), encoding="utf-8"))
letters = "ABCDE"
rows = []
for L in letters:
    dai = psr["dai2023_crosscheck"]["pulsars"][L]["DM"]
    tp = next(p for p in psr["pulsars"] if p["letter"] == L)["DM"]
    d, ed = dai["value"], dai["uncertainty"]
    t, et = tp["value"], tp["uncertainty"]
    comb = math.hypot(ed, et)
    rows.append(dict(letter=L,
                     dai_dm=d, dai_err=ed, trapum_dm=t, trapum_err=et,
                     delta=t - d, combined_sigma=comb,
                     significance_sigma=abs(t - d) / comb))
out["dm_comparison"] = dict(
    unit="pc cm^-3", source_dai="Dai2023 Table 1 (via pulsars.json dai2023_crosscheck)",
    source_trapum="TRAPUM2026 Tables D.1-D.3/Table 1 (via pulsars.json pulsars[*].DM)",
    rows=rows,
    delta_range=[min(r["delta"] for r in rows), max(r["delta"] for r in rows)],
    abs_delta_min=min(abs(r["delta"]) for r in rows),
    abs_delta_max=max(abs(r["delta"]) for r in rows),
    sign_counts={"+": sum(1 for r in rows if r["delta"] > 0),
                 "-": sum(1 for r in rows if r["delta"] < 0)},
    min_significance_sigma=min(r["significance_sigma"] for r in rows))

# pulsar B derivative sign comparison
b_tr = next(p for p in psr["pulsars"] if p["letter"] == "B")
b_dai = psr["dai2023_crosscheck"]["pulsars"]["B"]
out["pulsar_B_derivative_sign"] = dict(
    dai_Pdot=b_dai.get("Pdot"), trapum_Pdot=b_tr.get("Pdot"),
    trapum_A_bound=b_tr.get("a_LOS_c"),
    note="TRAPUM bound sign carried in the verbatim table entry; Dai tabulates "
         "Pdot directly. Recorded verbatim; no repair attempted.")

# ---------------------------------------------------------------------------
# 2. Minority-sign ledger (H-n5 / H-P9): both released records
# ---------------------------------------------------------------------------
fr = json.load(open(os.path.join(PAPER_H, "fit2", "results", "fit2_results.json"),
                    encoding="utf-8"))
fr_msp = json.load(open(os.path.join(PAPER_H, "flagd", "results", "fit2_msp",
                                     "fit2_results.json"), encoding="utf-8"))
ga = json.load(open(os.path.join(PAPER_H, "fit2", "results", "gates_a2.json"),
                    encoding="utf-8"))
ga_msp_path = os.path.join(PAPER_H, "flagd", "results", "fit2_msp", "gates_a2.json")
ga_msp = json.load(open(ga_msp_path, encoding="utf-8")) if os.path.exists(ga_msp_path) else None


def tally(data, profile_only=True):
    """Mirror gate_a2.gate_b: profile-leg configurations only unless asked otherwise."""
    matrix, minority, cell_ids = [], [], None
    n_def = n_minus = n_plus = 0
    for lab in sorted(data["configs"]):
        c = data["configs"][lab]
        if cell_ids is None:
            cell_ids = [(x["bracket"], x["M_range"], x["a_range"])
                        for x in c["cells"]]
        if profile_only and not c["config"]["use_profile"]:
            continue
        cells = c["cells"]
        signs, lns = [], []
        for x, cid in zip(cells, cell_ids):
            lk = x["lnK_compact_extended"]
            fin = lk is not None and math.isfinite(lk)
            sgn = (1 if lk > 0 else -1) if fin else 0
            signs.append(sgn); lns.append(lk)
            if fin:
                n_def += 1
                n_minus += sgn < 0; n_plus += sgn > 0
                if sgn < 0:
                    minority.append(dict(config=lab, bracket=cid[0],
                                         M_range=cid[1], a_range=cid[2], lnK=lk))
        matrix.append(dict(config=lab, use_profile=bool(c["config"]["use_profile"]),
                           signs=signs, lnk=lns))
    return dict(matrix=matrix, minority=minority,
                tally=dict(defined=n_def, minus=n_minus, plus=n_plus)), cell_ids


rec_fit2, cell_ids = tally(fr)
rec_msp, _ = tally(fr_msp)
gb = ga["A2-G-b"]
gb_msp = ga_msp["A2-G-b"] if ga_msp else None

out["sign_ledger"] = dict(
    cell_order=[{"bracket": b, "M_range": m, "a_range": a} for b, m, a in cell_ids],
    rows=rec_fit2["matrix"],
    rows_flagd_msp=rec_msp["matrix"],
    fit2_record=dict(tally=rec_fit2["tally"],
                     gate_file=dict(defined=gb["n_defined_cells"],
                                    minus=gb["sign_counts"]["-1"]),
                     reproduced=(rec_fit2["tally"]["defined"] == gb["n_defined_cells"]
                                 and rec_fit2["tally"]["minus"] == gb["sign_counts"]["-1"])),
    flagd_msp_record=dict(tally=rec_msp["tally"],
                          gate_file=(dict(defined=gb_msp["n_defined_cells"],
                                          minus=gb_msp["sign_counts"]["-1"])
                                     if gb_msp else None),
                          reproduced=((gb_msp is not None)
                                      and rec_msp["tally"]["defined"] == gb_msp["n_defined_cells"]
                                      and rec_msp["tally"]["minus"] == gb_msp["sign_counts"]["-1"])),
    paper_printed_minority=52,
    minority_examples_all=rec_msp["minority"] or rec_fit2["minority"])

# ---------------------------------------------------------------------------
# 3. Per-pulsar jerk decade margins (H-n3 CALC half)
# ---------------------------------------------------------------------------
jd = json.load(open(os.path.join(PAPER_H, "flagd", "results", "jerk_deltas.json"),
                    encoding="utf-8"))
variant = jd["sigma_kms"]["paper-set 21 km/s"]["FLAG D fiducial"]["rows"]
jrows = []
floors = [r["a0_floor"] for r in variant]
floor_med = float(np.median(floors))
for r in variant:
    ratio = abs(r["jerk_over_floor"])
    jrows.append(dict(name=r["name"], R_pc=r["R_pc"],
                      jerk_m_s3=r["jerk"], a0_floor_m_s3=r["a0_floor"],
                      decades_vs_own_floor=float(np.log10(ratio)),
                      decades_vs_median_floor=float(math.log10(abs(r["jerk"]) / floor_med)),
                      in_likelihood=(r["name"] != "C")))
dec_own = [r["decades_vs_own_floor"] for r in jrows]
dec_med = [r["decades_vs_median_floor"] for r in jrows]
out["jerk_margins"] = dict(
    convention="paper-set 21 km/s dispersion, FLAG D fiducial MSP kernel "
               "(released FLAG D record choice)",
    median_floor_m_s3=floor_med,
    rows=jrows,
    decades_vs_own_floor_range=[min(dec_own), max(dec_own)],
    decades_vs_median_floor_range=[min(dec_med), max(dec_med)],
    tick_set_includes_C=True,
    likelihood_set="seven pulsars (C excluded per mass-tension-paper.tex :74)",
    caption_claim="ticks sit two to three decades above the floor (:131), the floor "
                  "there being evaluated at the median of the eight per-pulsar floors",
    aggregate_reproduced=bool(min(dec_med) >= 2.0 and max(dec_med) <= 3.0))

# variant sweep: does ANY released variant reproduce the caption's 2-3 decades?
variant_sweep = {}
for sig_key, sk in jd["sigma_kms"].items():
    for conv_key, rows_v in sk.items():
        rows_x = rows_v["rows"] if isinstance(rows_v, dict) else rows_v
        fl = np.median([r["a0_floor"] for r in rows_x])
        decs = [math.log10(abs(r["jerk"]) / fl) for r in rows_x]
        variant_sweep[f"{sig_key} | {conv_key}"] = dict(
            range=[round(min(decs), 3), round(max(decs), 3)],
            two_to_three=bool(min(decs) >= 2.0 and max(decs) <= 3.0))
out["jerk_margins"]["variant_sweep_vs_median_floor"] = variant_sweep

# ---------------------------------------------------------------------------
# 4. P-12: flat-1.0 versus range readings of the profile-leg budget
# ---------------------------------------------------------------------------
gd = ga["A2-G-d"]
p12 = []
for lab in sorted(gd):
    entry = gd[lab]
    if not isinstance(entry, dict):
        continue
    dmax = entry.get("max_abs_delta_kms")
    dmax_knots = entry.get("max_abs_delta_within_knots_kms")
    row = dict(config=lab, budget_kms=entry.get("budget_kms"),
               max_abs_delta_kms=dmax,
               max_abs_delta_within_knots_kms=dmax_knots,
               gate_fires_as_recorded=entry.get("fires"),
               fires_flat_thr2_0=(dmax > 2.0) if dmax is not None else None,
               fires_range_low_thr1_0=(dmax > 1.0) if dmax is not None else None,
               fires_range_high_thr3_2=(dmax > 3.2) if dmax is not None else None)
    p12.append(row)
out["p12_budget_trigger"] = dict(
    readings=dict(flat="1.0 km/s single budget (:205); kill threshold 2x budget = 2.0",
                  range="0.5-1.6 km/s physics range (:273); kill thresholds 1.0 / 3.2 "
                        "at the range ends"),
    per_config=p12,
    note=("Firing status recomputed under each reading from the recorded fitted "
          "discrepancies; WHICH reading governs is panel question P-12 and is not "
          "decided here."))

with open(os.path.join(HERE, "fH_calc7_records.json"), "w") as fh:
    json.dump(out, fh, indent=1)

print("DM comparison (pc cm^-3):")
for r in rows:
    print(f"  {r['letter']}: Dai {r['dai_dm']:.4f}+-{r['dai_err']:.4f}  "
          f"TRAPUM {r['trapum_dm']:.5f}+-{r['trapum_err']:.5f}  "
          f"Delta {r['delta']:+.4f}  ({r['significance_sigma']:.0f} sigma)")
print(f"  |Delta| range {out['dm_comparison']['abs_delta_min']:.4f} - "
      f"{out['dm_comparison']['abs_delta_max']:.4f}; signs "
      f"{out['dm_comparison']['sign_counts']}")
print("\nsign ledger (profile-leg configurations, mirroring gate_a2.gate_b):")
f2, ms = out["sign_ledger"]["fit2_record"], out["sign_ledger"]["flagd_msp_record"]
print(f"  FIT-2 record:    defined {f2['tally']['defined']}, minority {f2['tally']['minus']}  |  gate file {f2['gate_file']['defined']}/{f2['gate_file']['minus']}  reproduced={f2['reproduced']}")
if ms["gate_file"]:
    print(f"  FLAG-D MSP set:  defined {ms['tally']['defined']}, minority {ms['tally']['minus']}  |  gate file {ms['gate_file']['defined']}/{ms['gate_file']['minus']}  reproduced={ms['reproduced']}")
print("  paper prints 52 of 288 (:194)")

print("\njerk margins (FLAG D fiducial, paper-set 21 km/s):")
for r in jrows:
    tag = "   [C: ticks only]" if r["name"] == "C" else ""
    print(f"  {r['name']}  R={r['R_pc']:.3f} pc  vs own floor {r['decades_vs_own_floor']:.2f} dex  vs median floor {r['decades_vs_median_floor']:.2f} dex{tag}")
jm = out["jerk_margins"]
lo, hi = jm["decades_vs_median_floor_range"]
print(f"  median floor {jm['median_floor_m_s3']:.3e} m s^-3; vs-median range {lo:.2f}-{hi:.2f} dex; caption 'two-to-three' reproduced: {jm['aggregate_reproduced']}")

print("\nP-12 kill-switch firings (thresholds 2.0 / 1.0 / 3.2 km/s):")
for p in p12:
    d = p["max_abs_delta_kms"]
    dk = p["max_abs_delta_within_knots_kms"]
    print(f"  {p['config']:22s} max|delta|={d:.3f} (knots {dk:.3f})  fires: flat={p['fires_flat_thr2_0']} low={p['fires_range_low_thr1_0']} high={p['fires_range_high_thr3_2']}  recorded={p['gate_fires_as_recorded']}")
