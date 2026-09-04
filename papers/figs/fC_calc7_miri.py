"""R7-CALC-C1 / C-CALC-4: MIRI depth rescale + variability floor + gain factors.
Anchor of record: paper/figs/miri_sensitivity.json (JDox ETC 6.0, S/N=10,
10 ks, low background).  Gates G-6, G-7.  Output: fC_calc7_miri.json
NIRCam depths are quoted as printed only (panel P-1: not touched).
"""
import json, math

D_CM = 5.49 * 3.085677581e21
FOUR_PI_D2 = 4.0 * math.pi * D_CM ** 2
JY = 1e-23

ANCHOR = {"F770W": {"ujy": 0.25, "lambda_um": 7.7, "chen_nuLn_nu": 1.9e30},
          "F1000W": {"ujy": 0.47, "lambda_um": 10.0, "chen_nuLn_nu": 4.9e30},
          "F444W": {"ujy": None, "lambda_um": 4.44, "chen_nuLn_nu": 9.2e30}}

def rescale(ujy_10ks_10s):
    """to 15 ks, 3 sigma"""
    return ujy_10ks_10s * (3.0 / 10.0) * math.sqrt(10.0 / 15.0)

def nu_of(lambda_um):
    return 2.99792458e14 / lambda_um  # Hz

def nuLn_of_fnu_jy(fnu_jy, nu):
    return fnu_jy * JY * FOUR_PI_D2 * nu

def fnu_of_nuLn(nuln, nu):
    return nuln / (FOUR_PI_D2 * nu) / JY

def main():
    rows = []
    for f, a in ANCHOR.items():
        nu = nu_of(a["lambda_um"])
        row = {"filter": f, "nu_Hz": nu,
               "chen_nuLn_lim": a["chen_nuLn_nu"],
               "chen_fnu_uJy": fnu_of_nuLn(a["chen_nuLn_nu"], nu) * 1e6}
        if a["ujy"] is not None:
            s15 = rescale(a["ujy"])
            row.update({"jdox_10ks_10s_uJy": a["ujy"],
                        "rescaled_15ks_3sig_nJy": s15 * 1e3,
                        "printed_nJy": 70.0 if f == "F770W" else 170.0,
                        "printed_over_anchor": (70.0 if f == "F770W" else 170.0) / (s15 * 1e3),
                        "post_crowding_3x_nJy": s15 * 3e3,
                        "flux_gain_pre": a["chen_nuLn_nu"] and row["chen_fnu_uJy"] * 1e3 / (s15 * 1e3),
                        "flux_gain_post": row["chen_fnu_uJy"] * 1e3 / (s15 * 3e3)})
        rows.append(row)
    f1000 = next(r for r in rows if r["filter"] == "F1000W")
    per_epoch_sig = f1000["post_crowding_3x_nJy"] / 3.0
    sig_diff = math.sqrt(2.0) * per_epoch_sig
    floor_3s_20pct = 3.0 * sig_diff / 0.20
    # bolometric gain
    led_2e4 = 2.5e42
    bol_deliv_lo, bol_deliv_hi = 1e29 / led_2e4, 1e30 / led_2e4
    out = {"_meta": {"script": "paper/figs/fC_calc7_miri.py",
                     "anchor": "miri_sensitivity.json (JDox ETC 6.0, 10 sigma, 10 ks, low bkg)"},
           "gates": {"G6_anchor_values": {"F770W_uJy": 0.25, "F1000W_uJy": 0.47},
                     "G6_F770W_rescaled_nJy": rescale(0.25) * 1e3,
                     "G6_F770W_printed": 70.0,
                     "G6_pass": abs(rescale(0.25) * 1e3 - 70.0) / 70.0 < 0.15,
                     "G7_F444W_10nJy_nuLn": nuLn_of_fnu_jy(1e-8, nu_of(4.44)),
                     "G7_printed": "2.5e28 (:219)",
                     "G7_pass": 2.3e28 < nuLn_of_fnu_jy(1e-8, nu_of(4.44)) < 2.7e28},
           "filters": rows,
           "variability_floor_F1000W": {
               "per_epoch_sigma_nJy": per_epoch_sig,
               "two_epoch_sigma_diff_nJy": sig_diff,
               "printed_floor_uJy": 0.5,
               "floor_3sig_20pct_nJy": floor_3s_20pct,
               "printed_floor_x_low": floor_3s_20pct / 500.0},
           "bolometric": {
               "L_Edd_2e4": led_2e4,
               "deliv_ratio_range": [bol_deliv_lo, bol_deliv_hi],
               "printed_ratio_range": "1e-13 - 1e-12 (:215)",
               "archival_ratio": 1e-9,
               "bol_gain_vs_archival": [1e-9 / bol_deliv_hi, 1e-9 / bol_deliv_lo]}}
    with open("paper/figs/fC_calc7_miri.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"gates": out["gates"], "filters": rows,
                      "var": out["variability_floor_F1000W"],
                      "bol": out["bolometric"]}, indent=1))

if __name__ == "__main__":
    main()
