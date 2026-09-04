"""R7-CALC-C1 / C-CALC-3b: spectrometer data volume.
Gate G-5.  Output: paper/figs/fC_calc7_datavol.json
"""
import json

BW_HZ = 856e6          # MeerKAT L band 856-1712 MHz
CH_1HZ = BW_HZ * 1.0   # 1-Hz channels
HRS_YR = 130.0

def vol_tb_hr(bytes_per_sample, pols):
    return CH_1HZ * pols * bytes_per_sample * 3600.0 / 1e12

def main():
    formats = [("4-bit complex (2 nibbles/pol)", 0.5, 2),
               ("int8 complex", 1.0, 2),
               ("float16 complex", 2.0, 2),
               ("float32 complex (2 pol x 4 B)", 4.0, 2),
               ("float32 single-pol", 4.0, 1)]
    rows = []
    for name, b, p in formats:
        v = vol_tb_hr(b, p)
        rows.append({"format": name, "bytes_per_sample": b, "pols": p,
                     "TB_hr": v, "TB_yr_at_130h": v * HRS_YR,
                     "x_printed": v / 0.7})
    printed_yr = 0.7 * HRS_YR
    out = {"_meta": {"script": "paper/figs/fC_calc7_datavol.py",
                     "channels_1Hz": CH_1HZ, "hrs_yr": HRS_YR},
           "gates": {"G5_internal_consistency_TB_yr": printed_yr,
                     "G5_printed": "~90 TB/yr (:534)",
                     "G5_pass": 89.0 < printed_yr < 92.0,
                     "G5_verify2_float32_2pol_TB_hr": vol_tb_hr(4.0, 2),
                     "G5_verify2_claim": "~24.7 TB/hr (~35x)",
                     "G5_pass2": 24.0 < vol_tb_hr(4.0, 2) < 25.5},
           "ladder": rows,
           "implied_bytes_per_ch_pol_at_printed": 0.7e12 / (CH_1HZ * 2 * 3600.0)}
    with open("paper/figs/fC_calc7_datavol.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"gates": out["gates"],
                      "implied_B": out["implied_bytes_per_ch_pol_at_printed"],
                      "ladder": rows}, indent=1))

if __name__ == "__main__":
    main()
