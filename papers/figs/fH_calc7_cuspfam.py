"""R7-CALC-FIN / S5 item 1 (H-P10 injection half): coverage and bias under two
tracer-cusp families, on the shipped G1 injection machinery.

Pre-committed scope (evaluation §8.1 S5 item 1; embargo-bound — numbers only):
  * Injection: G1's point injection (M_true = 4e4 Msun at a = 1e-4, the validated
    point-mass configuration), n_real = 50 per family, seeds 20250001 + k
    (G1's own seed base), full three-leg shipped likelihood (loglike_total),
    fiducial bracket, r_a marginalised — exactly run_g1.run_injection's
    per-realization recipe.
  * Families: A = shipped Bahcall-Wolf tracer cusp (gamma = 1.75, generation and
    fit); B = shallow tracer cusp (gamma = 1.30 — the GP2025 stellar-cusp slope,
    the physically motivated alternative) used for GENERATION only; the fit
    always assumes the shipped 1.75. That asymmetry is the point: it measures
    the bias when the true tracer cusp is shallower than the assumed one.
  * Metrics: 90 per cent coverage (covers_truth_exact, fiducial bracket), median
    posterior M_dark, bias = median(Mmed)/M_true - 1, per family.
  * Family A doubles as the validation gate: its coverage should reproduce
    G1's published point-injection value (~0.86-0.88).

The shipped mock_cluster is patched in _GAMMA_BW during generation of family B
only, and restored before each fit. Nothing outside paper/h/calc7 is written.
Output: fH_calc7_cuspfam.json (this directory).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HDIR = os.path.abspath(os.path.join(HERE, ".."))
for p in (os.path.join(HDIR, "mock"), os.path.join(HDIR, "fit"),
          os.path.join(HDIR, "flagd")):
    sys.path.insert(0, p)

import mock_cluster as mc            # noqa: E402
import mock_observables as mo        # noqa: E402
import fit_joint as fj               # noqa: E402
import run_g1 as G1                  # noqa: E402  (read-only: FIDUCIAL, seeds)

N_REAL = 50
M_TRUE, A_TRUE = 4.0e4, 1.0e-4       # G1's validated point injection
SEED_BASE = G1.SEED_BASE["point_4e4"]
FAMILIES = {"A_bw175": 1.75, "B_shallow130": 1.30}

cfg = mo.ObsConfig()
grid = fj.PriorGrid()
model = G1.build_model(cfg, grid, verbose=True)

p_true = mc.ClusterParams(M_dark=M_TRUE, a_dark=A_TRUE, **G1.FIDUCIAL)
tmodel = fj.truth_model(G1.FIDUCIAL, mo.asdict(cfg), np.array(cfg.prof_R),
                        grid, M_TRUE, A_TRUE)

orig_gamma = mc._GAMMA_BW
results = {"meta": dict(wu="R7-CALC-FIN", part="H-P10 injection half",
                        date="2026-08-24", n_real=N_REAL,
                        truth=dict(M=M_TRUE, a=A_TRUE),
                        families=FAMILIES,
                        note="generation-cusp patched per family; fit always assumes "
                             "the shipped BW 1.75; full three-leg shipped likelihood"),
           "families": {}}

for fam, gamma in FAMILIES.items():
    print(f"== family {fam} (generation gamma = {gamma})", flush=True)
    cov, mmed, mapM = [], [], []
    for k in range(N_REAL):
        mc._GAMMA_BW = gamma                      # generation-side patch
        data = mo.generate_dataset(p_true, cfg, seed=SEED_BASE + k)
        mc._GAMMA_BW = orig_gamma                 # restored before any fit step
        lnL = fj.loglike_total(model, data)
        lnLt = fj.loglike_total(tmodel, data)
        P = fj.posterior(lnL, grid, bracket=1)
        cov.append(bool(fj.covers_truth_exact(lnL, lnLt, 1, 0.90)))
        iM, ia = np.unravel_index(int(np.argmax(P)), P.shape)
        mapM.append(float(grid.M_dark[iM]))
        pm = fj.marginal_M(P, grid)
        mmed.append(float(np.exp(np.interp(0.5, np.cumsum(pm) / pm.sum(),
                                           np.log(grid.M_dark)))))
        if (k + 1) % 10 == 0:
            print(f"   {k + 1}/{N_REAL}  running coverage {np.mean(cov):.3f}  "
                  f"median Mmed {np.median(mmed):.3e}", flush=True)
    results["families"][fam] = dict(
        gamma_generation=gamma,
        coverage90=float(np.mean(cov)),
        coverage90_stderr=float(np.std(cov) / np.sqrt(N_REAL)),
        median_Mmed=float(np.median(mmed)),
        bias_frac=float(np.median(mmed) / M_TRUE - 1.0),
        median_MAP_M=float(np.median(mapM)),
        map_bias_frac=float(np.median(mapM) / M_TRUE - 1.0),
        per_realization_Mmed=mmed, per_realization_cov90=cov)

mc._GAMMA_BW = orig_gamma

fA = results["families"]["A_bw175"]
fB = results["families"]["B_shallow130"]
gate_ok = 0.80 <= fA["coverage90"] <= 0.93
results["gate_validation_pass"] = bool(gate_ok)
print(f"\nfamily A (shipped BW): coverage90 = {fA['coverage90']:.3f} +- {fA['coverage90_stderr']:.3f}"
      f"  | median Mmed = {fA['median_Mmed']:.4e}  bias {100 * fA['bias_frac']:+.1f}%")
print(f"family B (shallow 1.30): coverage90 = {fB['coverage90']:.3f} +- {fB['coverage90_stderr']:.3f}"
      f"  | median Mmed = {fB['median_Mmed']:.4e}  bias {100 * fB['bias_frac']:+.1f}%")
print("validation gate (A coverage in [0.80, 0.93], cf. G1 published ~0.86-0.88):",
      "PASS" if gate_ok else "FAIL")

with open(os.path.join(HERE, "fH_calc7_cuspfam.json"), "w") as fh:
    json.dump(results, fh, indent=1)
if not gate_ok:
    raise SystemExit(1)
