"""R7-CALC-GAXIF / F-CALC-2: wind-floor giant recount + Appendix A exchange rate.
Pre-committed spec: section 0.5.  Output: paper/figs/fF_calc7_windfloor.json
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))

G_KMS = 4.302e-3          # (km/s)^2 pc / Msun
SIGMA = 21.0              # km/s, paper-set fiducial
M_CL = 4.0e6              # Msun (Harris/BaumgardtVasiliev, paper's own)
RC_ARCSEC = 142.2         # 2.37 arcmin in arcsec
DIST_KPC = 5.49           # the paper-set fiducial (was 5.43 through v2.5)
RC_PC = RC_ARCSEC / 60.0 * DIST_KPC * 1000.0 * (math.pi / 10800.0)  # 3.78 pc
MU_M_E = 1.17 * 1.673e-24 # g
V_OUT = 50.0 * 1e5        # cm/s
YEAR = 3.15576e7
MSUN_G = 1.989e33

# inputs (pre-committed)
MEAN_M_LUM = 0.6          # Msun, luminous Kroupa mean
F_TURNOFF = 0.035         # Kroupa weight of the 0.8-0.9 Msun window
T_MS = 1.3e10             # yr, turnoff-mass main-sequence life
T_UPRGB = 0.35e9          # yr, L > 1e3 Lsun (range 0.2-0.5)
T_AGB = 0.07e9            # yr (range 0.05-0.1)
MDOT_PER_GIANT = 1.0e-8   # Msun/yr, the paper's own per-star rate

def m_enc_plummer(r_pc, M, a_pc):
    return M * r_pc ** 3 / (a_pc * a_pc + r_pc * r_pc) ** 1.5

def n_e_steady(mdot_msun_yr, r_pc):
    mdot = mdot_msun_yr * MSUN_G / YEAR
    return mdot / (4.0 * math.pi * (r_pc * 3.0857e18) ** 2 * MU_M_E * V_OUT)

def main():
    r_infl = G_KMS * 4.0e4 / SIGMA ** 2   # the HOLE mass sets the influence radius
    m_in = m_enc_plummer(r_infl, M_CL, RC_PC)
    n_star = m_in / MEAN_M_LUM
    f_phase = (T_UPRGB + T_AGB) / T_MS
    n_giants = n_star * F_TURNOFF * f_phase
    mdot_agg = n_giants * MDOT_PER_GIANT
    n_e = n_e_steady(mdot_agg, r_infl)
    # sensitivity rows
    sens = []
    for tur, tag in ((0.2e9, "t_upRGB=0.2Gyr"), (0.5e9, "t_upRGB=0.5Gyr")):
        ng = n_star * F_TURNOFF * (tur + T_AGB) / T_MS
        sens.append({"tag": tag, "n_giants": ng,
                     "mdot_msun_yr": ng * MDOT_PER_GIANT,
                     "n_e": n_e_steady(ng * MDOT_PER_GIANT, r_infl)})
    for tag, mm in (("mean_m=0.55", 0.55), ("mean_m=0.7", 0.7)):
        ng = (m_in / mm) * F_TURNOFF * f_phase
        sens.append({"tag": tag, "n_giants": ng,
                     "mdot_msun_yr": ng * MDOT_PER_GIANT,
                     "n_e": n_e_steady(ng * MDOT_PER_GIANT, r_infl)})
    # printed chain reproduction (gate): the arithmetic is internally consistent
    printed_n_e = n_e_steady(1e3 * MDOT_PER_GIANT, r_infl)
    gate = {"printed_chain_n_e": printed_n_e,
            "printed": "~3 cm^-3 (:202)",
            "pass": 2.0 < printed_n_e < 4.5,
            "note": "the printed ARITHMETIC holds; the 1e3-giant INPUT is "
                    "what the recount tests"}
    # exchange rate (F-n11)
    M_BH, NE = 2.0e4, 0.23
    rho = NE * MU_M_E
    def mdot_b(cs_kms):
        cs = cs_kms * 1e5
        gm = G_KMS * 1e6 * M_BH   # (km/s)^2 pc -> (m^2/s^2): G in SI-ish
        # work in cgs: G = 6.674e-8, M = 2e4*1.989e33 g, r in cm
        G_cgs = 6.674e-8
        M_g = M_BH * 1.989e33
        return 4.0 * math.pi * 0.25 * (G_cgs * M_g) ** 2 * rho / cs ** 3  # g/s
    mb_median = mdot_b(14.15)
    mb_implied_cs = ((4.0 * math.pi * 0.25 * (6.674e-8 * M_BH * 1.989e33) ** 2
                      * rho / 5.3e18)) ** (1.0 / 3.0) / 1e5
    pct = (mb_implied_cs - 11.7) / (16.6 - 11.7) * 100.0
    conv_ratio = 0.25 * (SIGMA ** 2 + 14.15 ** 2) ** 1.5 / 14.15 ** 3
    exch = {"Mdot_B_at_median_cs_g_s": mb_median,
            "printed": "5.3e18 g/s (:527)",
            "implied_cs_kms": mb_implied_cs,
            "implied_percentile_of_prior": pct,
            "convention_ratio_at_median": conv_ratio,
            "printed_convention_ratio": 1.9,
            "absolute_ratio_to_paperE_3e18": mb_median / 3.0e18}
    out = {"_meta": {"script": "paper/figs/fF_calc7_windfloor.py"},
           "inputs": {"r_infl_pc": r_infl, "M_enc_r_infl": m_in,
                      "n_star_r_infl": n_star, "f_phase": f_phase},
           "gates": gate,
           "recount": {"n_giants_central": n_giants, "mdot_agg_msun_yr": mdot_agg,
                       "n_e_steady": n_e, "sensitivity": sens,
                       "printed": {"n_giants": 1e3, "mdot": 1e-5, "n_e": 3}},
           "exchange": exch}
    with open(os.path.join(HERE, "fF_calc7_windfloor.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"gates": gate, "recount": out["recount"],
                      "exchange": exch}, indent=1))

if __name__ == "__main__":
    main()

