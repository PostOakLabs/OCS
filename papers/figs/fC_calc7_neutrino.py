"""R7-CALC-C1 / C-CALC-1: neutrino burst-search trials budget.
Conventions pre-committed in 0xAlpha/results/R7-CALC-C1.md section 0.1.
Gates G-1, G-2.  Output: paper/figs/fC_calc7_neutrino.json
"""
import json, math

YEAR = 3.15576e7
T = 10.0 * YEAR
SIZES = [100.0, 1000.0, 10000.0]
L_ENV, L_A = 1e-7, 0.15 / YEAR
P5 = 2.867e-7

def p3(mu):
    return 1.0 - math.exp(-mu) * (1.0 + mu + mu * mu / 2.0)

def p3_lead(mu):
    return mu ** 3 / 6.0

def sigma_eq(p):
    return None if p <= 0 or p >= 1 else abs(_z(p))

def _z(p):
    # rational approximation of inverse normal CDF (one-sided), Acklam
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

def main():
    n_per = {f"{int(dt)}s": T / dt for dt in SIZES}
    n_tot = sum(n_per.values())
    out = {"_meta": {"script": "paper/figs/fC_calc7_neutrino.py",
                     "T_s": T, "lambda_env": L_ENV, "lambda_A": L_A,
                     "p5": P5},
           "trials": {"nonoverlap_per_size": n_per,
                      "nonoverlap_total": n_tot,
                      "sliding_1s_raw": T,
                      "printed": "~3e6 windows (:377)"}}
    # gates
    mu_1e3 = L_ENV * 1e3
    g1 = p3(mu_1e3)
    g2 = g1 * n_tot
    out["gates"] = {
        "G1_p3_mu1e-4": {"exact": g1, "leading": p3_lead(mu_1e3),
                         "printed": "~2e-13 (:399)",
                         "pass": 1.5e-13 < g1 < 2.5e-13},
        "G2_posttrials_1e3s_x_totalN": {"value": g2, "printed": "5e-7 (:401)",
                                        "pass": 4e-7 < g2 < 7e-7}}
    # false-alarm table
    table = []
    for rate_name, lam in (("envelope", L_ENV), ("realistic_A", L_A)):
        for dt in SIZES:
            mu = lam * dt
            P = p3(mu)
            nk = n_per[f"{int(dt)}s"]
            post = P * n_tot
            table.append({"rate": rate_name, "dt_s": dt, "mu": mu,
                          "p_ge3_exact": P, "p_ge3_leading": p3_lead(mu),
                          "N_size": nk,
                          "raw_false_per_decade": P * nk,
                          "post_trials_p_per_triplet": post,
                          "sigma_equiv": sigma_eq(post),
                          "promotable_vs_p5": post < P5})
    out["false_alarm_table"] = table
    # promotability floor: max mu such that P3*N_tot < P5
    lo, hi = 1e-12, 1.0
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if p3(mid) * n_tot < P5: lo = mid
        else: hi = mid
    out["promotability"] = {"max_mu_promotable": lo,
                            "max_dt_at_envelope_s": lo / L_ENV,
                            "max_dt_at_realistic_s": lo / L_A}
    # exposure -> rate map (C-n14)
    out["exposure_to_rate"] = {
        "formula": "R_excl(95%) = -ln(0.05)/(T*p_det)",
        "R_excl_per_s_pd1": 3.0 / T,
        "R_excl_per_yr_pd1": 3.0 / 10.0,
        "note": "p_det=1 for bursts lasting >= 100 s; fluence-limited case "
                "scales as 1/p_det(fluence) with p_det set by the ARCA "
                "effective-area integral (not in repo; flagged UNVERIFIABLE)."}
    with open("paper/figs/fC_calc7_neutrino.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"gates": out["gates"],
                      "n_total": n_tot,
                      "promotability": out["promotability"],
                      "R_excl_yr": out["exposure_to_rate"]["R_excl_per_yr_pd1"]},
                     indent=1))

if __name__ == "__main__":
    main()
