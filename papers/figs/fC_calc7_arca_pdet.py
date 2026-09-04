"""R7-CALC-FIN / S2 item 2: ARCA fluence-limited p_det (closes the C1 UNVERIFIABLE).

Calibration from the KM3NeT 2.0 LOI (Adrian-Martinez et al. 2016, J.Phys.G 43,
084001, arXiv:1601.07459 — full text fetched 2026-08-24):
  * Table 6, RX J1713 track analysis, ARCA 2 building blocks, 5 years:
    nu_mu signal after final cuts = 8.1 events (33.4 triggered, 23.5 preselected).
  * RX J1713: dec -39d46', max elevation ~14 deg — the same near-horizon
    visibility class as omega Cen (dec -47d30', culmination ~6 deg; LOI Fig. 37
    covers it under the 'tracks up to 6 deg above the horizon' selection).
  * LOI visibility statement: selecting tracks below or a few degrees above the
    horizon reduces visibility only for source declinations ABOVE -40 deg;
    omega Cen at -47.5 deg is in the fully visible band.

p_det model (stated): for a burst of fluence f_rel x an RX-J1713-equivalent
steady flux, lasting T, the expected track count in the window is
  mu(T, f_rel) = (8.1 / 5 yr) * T * f_rel,
and the detection probability for the >= 3-track criterion is
  p_det = 1 - exp(-mu) (1 + mu + mu^2/2)   [Poisson, P(>=3)].
Caveats stated in the report addendum: spectrum shape (RX J1713 cuts at tens of
TeV, comparable to the T6 band), 2-block configuration, analysis-level cuts.

Output: fC_calc7_arca_pdet.json (this directory).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RATE_5YR = 8.1                     # tracks / 5 yr, RX J1713-equivalent, final cuts
RATE_PER_S = RATE_5YR / (5.0 * 3.15576e7)


def mu_tracks(T_s, f_rel):
    return RATE_PER_S * T_s * f_rel


def p_det(T_s, f_rel):
    mu = mu_tracks(T_s, f_rel)
    if mu < 50.0:
        return 1.0 - math.exp(-mu) * (1.0 + mu + mu * mu / 2.0)
    return 1.0


rows = []
for T in (1e2, 1e3, 1e4):
    for f in (1.0, 1e2, 1e3, 1e4, 1e5, 1e6):
        mu = mu_tracks(T, f)
        rows.append(dict(T_s=T, f_rel=f, mu=mu, p_det=p_det(T, f)))

# fluence amplification needed for p_det ~ 0.9 and ~ 1.0 per 1e3-s window
f_needed = None
f = 1.0
while f < 1e9:
    if p_det(1e3, f) >= 0.9:
        f_needed = f
        break
    f *= 1.05
f_one = None
f = 1.0
while f < 1e9:
    if p_det(1e3, f) >= 1.0 - 1e-3:
        f_one = f
        break
    f *= 1.05

out = dict(
    meta=dict(wu="R7-CALC-FIN", part="S2 item 2 — ARCA fluence-limited p_det",
              date="2026-08-24",
              calibration="LOI Table 6: 8.1 nu_mu tracks / 5 yr after final cuts, "
                          "RX J1713 analysis, ARCA 2 blocks",
              visibility="omega Cen dec -47.5 deg fully visible per LOI Fig. 37 "
                         "(reduction only for dec above -40 deg)"),
    p_det_formula="p_det = 1 - exp(-mu)(1 + mu + mu^2/2), mu = (8.1/5yr) T f_rel",
    rows=rows,
    fluence_amplification_for_pdet90_1e3s=f_needed,
    fluence_amplification_for_pdet999_1e3s=f_one,
    verdict=("Per-window detection of a >=3-track multiplet requires a burst "
             "fluence ~1e5 times an RX-J1713-equivalent steady flux (p_det ~ 0.89 "
             "at 1e5 x, 1e3-s window); at astrophysically-scaled fluences "
             "p_det << 1 and the C1 excluded-rate map scales as 1/p_det with "
             "p_det(F) as given. Confirms C1's statement that the practical "
             "limit on T6 is exposure, not background."),
)

with open(os.path.join(HERE, "fC_calc7_arca_pdet.json"), "w") as fh:
    json.dump(out, fh, indent=1)

print("mu(1e3 s, f_rel=1) =", mu_tracks(1e3, 1.0))
for r in rows:
    if r["T_s"] == 1e3:
        print(f"  T=1e3 s  f_rel={r['f_rel']:>8.0e}  mu={r['mu']:.4g}  p_det={r['p_det']:.4g}")
print("fluence amplification for p_det>=0.9 (1e3 s):", f_needed)
print("fluence amplification for p_det>=0.999 (1e3 s):", f_one)
