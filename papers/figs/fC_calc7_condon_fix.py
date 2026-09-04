"""R7-CALC-FIN / S2 item 1: Condon primary-read addendum (closes the C-n3 STOP).

Resolves the confusion-anchor STOP of R7-CALC-C1.md section 3.3 by reading the
Condon criterion from readable primaries and recomputing the affected column.

Primary findings (sources verified this pass):
  1. The Condon confusion criterion is a SELF-CONSISTENT cutoff S_c = q sigma_c,
     with the operational form (Condon 2007, as quoted in Rahman 2016 eq. 3;
     framework: Condon 1974, ApJ 188, 279 — "Confusion and Flux-Density Error
     Distributions"):
         sigma_c = [ k Omega_e q^(3-gamma) / (3 - gamma) ]^(1/(gamma-1)),
     with dN/dS = k S^-gamma the differential count law and
     Omega_e = Omega_b/(gamma-1) for a Gaussian beam (Condon's effective solid
     angle). The criterion constant is q ~ 5 ("reliable detection", Condon 2007).
     It is NOT "23.6 beams per source": no such convention appears in the
     readable primary chain, and the C1 column built on it (cutoff at
     N Omega = 23.6 sources per beam) is a misattribution.
  2. The NVSS "0.45 mJy at 45 arcsec" quantity is the NVSS RMS NOISE
     (Condon et al. 1998), not its confusion limit; scaling it as theta^2
     (the C1 anchor column) anchored on the wrong quantity. The corrected
     45-arcsec confusion anchor under the same count law and criterion is
     ~0.19 mJy, and NVSS (rms 0.45 mJy) is therefore noise-limited, not
     confusion-limited — consistent with its design.
  3. Independent primary anchor: Vernstrom et al. 2014 (MNRAS 440, 2791)
     abstract quotes rms confusion ~1.2 uJy/beam at 3 GHz in an 8-arcsec beam.
     The corrected criterion reproduces the order of that number from the
     faint-count normalization (see json note), supporting the q ~ 5 reading.

Same count law as the shipped C1 script (N(>S) = 220 (S/mJy)^-1 deg^-2 at
1.4 GHz, differential gamma = 2, extended below 10 uJy per C1 addendum A1);
same bands; additive to the shipped record (nothing overwritten).
Output: fC_calc7_condon_fix.json (this directory).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SR_PER_DEG2 = 3282.80635
K_DEG = 0.22           # dN/dS = 220 (S/mJy)^-1 deg^-2  ->  0.22 S_Jy^-2 deg^-2 (Jy conversion x1e-3)
Q = 5.0                 # Condon (2007) reliable-detection criterion
GAMMA = 2.0             # differential slope of the flattened law


def omega_deg2(theta_as):
    theta_rad = theta_as / 3600.0 * math.pi / 180.0
    return 1.133 * theta_rad ** 2 * SR_PER_DEG2


def sigma_condon_uJy(theta_as, nu_ghz):
    """Corrected Condon criterion, flattened law (gamma=2):
    sigma_c = k Omega_e q^(3-gamma)/(3-gamma) with Omega_e = Omega_b/(gamma-1);
    for gamma = 2 this reduces to sigma_c = k Omega_b q. Count normalization
    carried at 1.4 GHz and scaled to the band as (nu/1.4)^-0.7 (alpha=-0.7,
    same convention as the shipped script)."""
    om_deg2 = omega_deg2(theta_as)
    k_nu = K_DEG * (nu_ghz / 1.4) ** -0.7
    sigma_jy = k_nu * om_deg2 * Q          # gamma=2: [k Om q / 1]^(1/1)
    return sigma_jy * 1e6


def classical_uJy(theta_as):
    om = omega_deg2(theta_as)
    s_cut_mjy = 220.0 * om                 # N(>S) Omega = 1
    return s_cut_mjy / 2.0 * 1e3


def thermal_ujy(sefd_dish_jy, n_ant, dnu_hz, t_hr):
    return sefd_dish_jy / math.sqrt(n_ant * (n_ant - 1.0) * dnu_hz * t_hr * 3600.0) * 1e6


bands = [("L", 1.4, 6.0), ("S", 3.0, 6.0), ("UHF", 0.8, 8.0), ("L uniform", 1.4, 4.0)]
rows = []
for band, nu, th in bands:
    rows.append(dict(band=band, nu_ghz=nu, theta_as=th,
                     classical_uJy=classical_uJy(th),
                     condon_q5_uJy=sigma_condon_uJy(th, nu),
                     thermal_uJy=thermal_ujy(430.0, 60, 856e6, 100.0) if nu == 1.4 and th == 6.0 else None))

# Vernstrom 2014 3 GHz / 8 arcsec cross-check with Condon-2007 faint counts
# (differential slope 1.9, dN/dS = 1000 S^-1.9 at 1.4 GHz, 1-100 uJy):
gamma_f, k_f = 1.9, 1000.0
om_b_8as = 1.133 * (8.0 / 3600.0 * math.pi / 180.0) ** 2
om_e = om_b_8as / (gamma_f - 1.0)
sigma_14ghz_8as_Jy = (k_f * om_e * Q ** (3.0 - gamma_f) / (3.0 - gamma_f)) ** (1.0 / (gamma_f - 1.0))
xcheck_uJy = sigma_14ghz_8as_Jy * 1e6

out = dict(
    meta=dict(wu="R7-CALC-FIN", part="S2 item 1 — Condon primary-read addendum",
              date="2026-08-24", additive_to="fC_calc7_confusion.py/.json (untouched)"),
    primary_read=dict(
        criterion="S_c = q sigma_c, self-consistent",
        operational_form="sigma_c = [k Omega_e q^(3-gamma)/(3-gamma)]^(1/(gamma-1))",
        q=Q, q_source="Condon 2007 (reliable detection), as quoted in Rahman 2016 eq. 3",
        framework="Condon 1974, ApJ 188, 279 (P(D) formalism; scan-only, framework "
                  "cross-verified via Bond et al. quoting Condon's effective-solid-angle "
                  "definition)",
        misattribution_found=("C1's 'q = 23.6 beams per source' column implemented "
                              "N Omega = 23.6 sources per beam as the cutoff depth — "
                              "not a Condon convention"),
        nvss_anchor=("0.45 mJy at 45 arcsec is the NVSS rms noise (Condon et al. 1998), "
                     "not its confusion limit; corrected 45-arcsec confusion under the "
                     "same law/criterion is ~0.19 mJy, so NVSS is noise-limited"),
        vernstrom_xcheck=dict(
            claimed_uJy=1.2, note="Vernstrom et al. 2014 abstract: rms confusion "
            "~1.2 uJy/beam at 3 GHz, 8 arcsec",
            this_law_uJy=round(xcheck_uJy, 2),
            note2="Condon-2007 faint counts (gamma=1.9, k=1000, 1.4 GHz, q=5) give "
                  "~2.8 uJy at 8 arcsec; the factor ~2 gap to the Vernstrom 3-GHz "
                  "value is the count-normalization uncertainty C1 already flagged")),
    bands=rows,
    verdict=dict(
        corrected_spread_L6_uJy=[round(classical_uJy(6.0), 2), round(sigma_condon_uJy(6.0, 1.4), 2)],
        printed_claim="~1-2 uJy beam^-1 at ~6 arcsec (:252)",
        printed_inside_corrected_spread=True,
        ordering_at_6arcsec="confusion-dominated under the corrected Condon reading "
                            "(3.5 vs thermal 0.41); classical still reads "
                            "thermal-dominated (0.35 vs 0.41) — ordering remains "
                            "formalism-dependent, spread narrows from 0.35-8 to 0.35-3.5"),
)

with open(os.path.join(HERE, "fC_calc7_condon_fix.json"), "w") as fh:
    json.dump(out, fh, indent=1)

for r in rows:
    th = f"{r['thermal_uJy']:.2f}" if r["thermal_uJy"] else "  — "
    print(f"{r['band']:11s} {r['nu_ghz']:.1f} GHz {r['theta_as']:.0f}\"  "
          f"classical {r['classical_uJy']:.2f}  Condon(q=5) {r['condon_q5_uJy']:.2f}  "
          f"thermal {th}")
print(f"\nVernstrom 3 GHz/8\" cross-check (faint law): {xcheck_uJy:.2f} uJy vs quoted ~1.2")
print(f"corrected L/6\" spread: {out['verdict']['corrected_spread_L6_uJy']}")
