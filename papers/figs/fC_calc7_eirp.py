"""R7-CALC-C1 / C-CALC-2: commensal SETI duty cycle + EIRP ladder.
Gate G-3.  Output: paper/figs/fC_calc7_eirp.json
"""
import json, math

D_KPC = 5.49
D_CM = D_KPC * 3.085677581e21
SNR = 10.0
DNU_HZ = 1.0
SEFD_INC_JY = 55.0
SEFD_COH_JY = 7.0
JY = 1e-23  # W/m2/Hz -> use cgs below

def eirp_w(sefd_jy, t_hr):
    d_m = D_KPC * 3.085677581e19
    sefd = sefd_jy * 1e-26  # W/m2/Hz
    return 4.0 * math.pi * d_m ** 2 * SNR * sefd * math.sqrt(DNU_HZ / (t_hr * 3600.0))

def main():
    gate = eirp_w(SEFD_INC_JY, 70.0)
    coh = eirp_w(SEFD_COH_JY, 70.0)
    sessions_per_yr, hrs_lo, hrs_hi = 26.0, 3.0, 5.0
    avail = {"2yr_lo": sessions_per_yr * hrs_lo * 2,
             "2yr_hi": sessions_per_yr * hrs_hi * 2}
    rows = []
    for t in (70.0, avail["2yr_lo"], 200.0, avail["2yr_hi"]):
        rows.append({"t_hr": t,
                     "EIRP_incoh_W": eirp_w(SEFD_INC_JY, t),
                     "EIRP_coh_W": eirp_w(SEFD_COH_JY, t),
                     "gain_vs_printed": math.sqrt(70.0 / t)})
    duty = {"eta_vs_lo": 70.0 / avail["2yr_lo"],
            "eta_vs_hi": 70.0 / avail["2yr_hi"]}
    out = {"_meta": {"script": "paper/figs/fC_calc7_eirp.py"},
           "gates": {"G3_incoh_70h_W": gate,
                     "G3_printed": "~4e15 W (:241/:246)",
                     "G3_pass": 3.8e15 < gate < 4.2e15,
                     "G3_coh_70h_W": coh,
                     "G3_coh_printed": "~5e14 W",
                     "G3_coh_pass": 4.5e14 < coh < 5.5e14},
           "available_commensal_2yr_h": avail,
           "implied_duty_cycle": duty,
           "ladder": rows,
           "arecibo_ratio": gate / 2e13}
    with open("paper/figs/fC_calc7_eirp.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"gates": out["gates"], "avail": avail,
                      "duty": duty, "ladder": rows}, indent=1))

if __name__ == "__main__":
    main()
