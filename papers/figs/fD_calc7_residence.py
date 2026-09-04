"""R7-CALC-C2D / D-CALC-1: residence-survival propagation for Paper D.

Pre-committed spec: 0xAlpha/results/R7-CALC-C2D.md section 0.2.
Closed form; no Monte Carlo.  Output: paper/figs/fD_calc7_residence.json

Mixture survival at radius a (Paper E fig1_results.json):
  S(t|a) = p_bnd(a) + (1 - p_bnd(a)) exp(-t / t_imp(a)),
  p_bnd(a) = p_bh_present * f_cap * p_surv_1e8   (bound_fid channel)
  t_imp(a) = t_med of the fbh_0.01 impulsive envelope.
Discounted-payoff retention at kappa = rho + lambda:
  F_res(kappa|a) = p_bnd + (1 - p_bnd) kappa t_imp / (1 + kappa t_imp).
Corrected threshold: rho* solves rho = ln(G p_s F_res(rho)) / tau (iterate).
P-9: everything at tau = 1e5 yr and tau = 1.19e5 yr.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))

G_FID = 1.0e9
P_S = 0.5
KAPPA_GRID = [1e-6, 1e-5, 1e-4]
TAU_COLS = {"tau_1e5": 1.0e5, "tau_1.19e5": 1.19e5}
RADII_ANCHOR_UJ = [10.0, 100.0, 1000.0]

def main():
    with open(os.path.join(HERE, "fig1_results.json")) as f:
        d = json.load(f)
    bnd = d["per_config"]["bound_fid"]
    imp = d["per_config"]["fbh_0.01"]
    a_au = bnd["a_AU"]

    # gate G-D: README headline row
    t10 = imp["t_med"][a_au.index(min(a_au, key=lambda x: abs(x - 10.0)))]

    rows = []
    for a_target in RADII_ANCHOR_UJ:
        i = min(range(len(a_au)), key=lambda k: abs(a_au[k] - a_target))
        p_bnd = (bnd["p_bh_present"][i] * bnd["f_cap"][i]
                 * bnd["p_surv_1e8"][i])
        t_imp = imp["t_med"][i]
        for kappa in KAPPA_GRID:
            F = p_bnd + (1.0 - p_bnd) * (kappa * t_imp) / (1.0 + kappa * t_imp)
            rows.append({"a_AU": a_au[i], "kappa_per_yr": kappa,
                         "p_bnd": p_bnd, "t_imp_yr": t_imp,
                         "F_res": F, "debit": 1.0 - F})
    # envelope-minimum row (worst case)
    i_min = int(np_argmin(imp["t_med"]))
    p_bnd_min = (bnd["p_bh_present"][i_min] * bnd["f_cap"][i_min]
                 * bnd["p_surv_1e8"][i_min])
    t_imp_min = imp["t_med"][i_min]
    for kappa in KAPPA_GRID:
        F = p_bnd_min + (1.0 - p_bnd_min) * (kappa * t_imp_min) / (1.0 + kappa * t_imp_min)
        rows.append({"a_AU": a_au[i_min], "kappa_per_yr": kappa,
                     "p_bnd": p_bnd_min, "t_imp_yr": t_imp_min,
                     "F_res": F, "debit": 1.0 - F})

    # corrected threshold, iterated, per tau column and per radius
    thr = []
    for a_target in RADII_ANCHOR_UJ + [a_au[i_min]]:
        i = min(range(len(a_au)), key=lambda k: abs(a_au[k] - a_target))
        p_bnd = (bnd["p_bh_present"][i] * bnd["f_cap"][i]
                 * bnd["p_surv_1e8"][i])
        t_imp = imp["t_med"][i]
        for tname, tau in TAU_COLS.items():
            rho0 = math.log(G_FID * P_S) / tau
            rho = rho0
            for _ in range(200):
                kap = rho
                F = p_bnd + (1.0 - p_bnd) * (kap * t_imp) / (1.0 + kap * t_imp)
                rho_new = math.log(G_FID * P_S * F) / tau
                if abs(rho_new - rho) < 1e-12 * rho:
                    rho = rho_new
                    break
                rho = rho_new
            thr.append({"a_AU": a_au[i], "tau_yr": tau,
                        "rho_star_uncorrected": rho0,
                        "rho_star_residence": rho,
                        "debit_frac": 1.0 - rho / rho0})
    out = {"_meta": {"script": "paper/figs/fD_calc7_residence.py",
                     "G": G_FID, "p_s": P_S,
                     "model": "S = p_bnd + (1-p_bnd) exp(-t/t_imp); "
                              "bound branch survives horizon"},
           "gates": {"G_C_rho_star": math.log(G_FID * P_S) / 1e5,
                     "G_C_printed": "2.0e-4 yr^-1 (:229-232)",
                     "G_C_pass": abs(math.log(G_FID * P_S) / 1e5 - 2.003e-4)
                                 / 2.003e-4 < 0.01,
                     "G_D_t_med_10AU_yr": t10,
                     "G_D_readme": 6.6e7,
                     "G_D_pass": abs(t10 / 6.6e7 - 1.0) < 0.05},
           "debit_rows": rows,
           "threshold_rows": thr}
    with open(os.path.join(HERE, "fD_calc7_residence.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"gates": out["gates"], "debit_rows": rows,
                      "threshold_rows": thr}, indent=1))

def np_argmin(x):
    return min(range(len(x)), key=lambda k: x[k])

if __name__ == "__main__":
    main()


