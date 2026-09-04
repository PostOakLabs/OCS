"""R7-CALC-C1 / C-CALC-3a: confusion per band, three formalisms + radiometer gate.
Gate G-4 (radiometer) passes; the confusion ANCHOR gate fails under every
defensible formalism variant (see report section 3.3) - the absolute scale is
reported as a STOP per rule 5(b), with the per-band spread delivered instead.
Count law (pre-committed, extended below 10 uJy as addendum A1 in the report):
N(>S) = 220 (S/mJy)^-1.0 deg^-2 at 1.4 GHz down to 0; Euclidean above 1 mJy.
Formalisms:
  (i)   classical 1-source-per-beam cutoff, sigma ~ S_cut/2
  (ii)  Condon (1974) q=23.6 integral (Vernstrom+2014 eq. 1 form)
  (iii) NVSS-anchor scaling: 0.45 mJy at (45", 1.4 GHz) scaled as theta^2
Frequency scaling: S_1.4 = S_nu (nu/1.4)^0.7 (alpha = -0.7).
"""
import json, math

Q = 23.6
SR_PER_DEG2 = 3282.80635
N0 = 220.0  # deg^-2 at 1 mJy, 1.4 GHz

def omega_deg2(theta_as):
    theta_rad = theta_as / 3600.0 * math.pi / 180.0
    return 1.133 * theta_rad ** 2 * SR_PER_DEG2

def s_cut_one_per_beam_mjy(om):
    return N0 * om            # N(>S) Om = 1, flattened law

def s_cut_q_mjy(om):
    return N0 * om / Q        # N(>S) Om = q, flattened law

def sigma_classical_uJy(om):
    return s_cut_one_per_beam_mjy(om) / 2.0 * 1e3

def sigma_q_uJy(om, nu_ghz):
    # flattened law (beta=2): var = Om*0.22e3*S_c(Jy) + q*S_c(Jy)^2
    s_c_jy = s_cut_q_mjy(om) * 1e-3 * (nu_ghz / 1.4) ** -0.7
    var = om * 0.22e3 * s_c_jy + Q * s_c_jy ** 2
    return math.sqrt(max(var, 0.0)) * 1e6

def sigma_anchor_uJy(theta_as, nu_ghz):
    return 450.0 * (theta_as / 45.0) ** 2 * (nu_ghz / 1.4) ** -0.7

def thermal_ujy(sefd_dish_jy, n_ant, dnu_hz, t_hr):
    return sefd_dish_jy / math.sqrt(n_ant * (n_ant - 1.0) * dnu_hz * t_hr * 3600.0) * 1e6

def main():
    bands = [
        {"band": "L", "nu_ghz": 1.4, "theta_as": 6.0},
        {"band": "S", "nu_ghz": 3.0, "theta_as": 6.0},
        {"band": "UHF", "nu_ghz": 0.8, "theta_as": 8.0},
        {"band": "L uniform-weight", "nu_ghz": 1.4, "theta_as": 4.0},
    ]
    rows = []
    for b in bands:
        om = omega_deg2(b["theta_as"])
        rows.append({**b,
                     "sigma_classical_uJy": sigma_classical_uJy(om),
                     "sigma_condon_q_uJy": sigma_q_uJy(om, b["nu_ghz"]),
                     "sigma_nvss_anchor_uJy": sigma_anchor_uJy(b["theta_as"], b["nu_ghz"])})
    thermal = thermal_ujy(430.0, 60, 856e6, 100.0)
    out = {"_meta": {"script": "paper/figs/fC_calc7_confusion.py",
                     "count_law": "N(>S)=220 (S/mJy)^-1.0 deg^-2 at 1.4 GHz, extended below 10 uJy (addendum A1)",
                     "status": "anchor gate FAILED under all formalisms; absolute scale STOP per rule 5(b)"},
           "gates": {"G4_thermal_100h_uJy": thermal,
                     "G4_printed": "~0.5 uJy (:252)",
                     "G4_pass": 0.3 < thermal < 0.8,
                     "anchor_status": "FAILED - see report section 3.3; formalism spread spans 0.02-70 uJy at 6 arcsec"},
           "bands": rows,
           "printed_claim": "~1-2 uJy beam^-1 at ~6 arcsec, L band (:252)"}
    with open("paper/figs/fC_calc7_confusion.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"gates": out["gates"], "bands": rows}, indent=1))

if __name__ == "__main__":
    main()
