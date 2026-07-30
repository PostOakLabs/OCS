"""Fig 3: worked-example ln K per channel, H_eng vs H_q (best null), omega Cen today.

Appendix B model, v1.0 continuous MIRI likelihood (OCS-MIRI-1, R5 5.3):

Channels and data (2026):
  MIR  : continuous per-filter detection against the real MIRI point-source
         sensitivity curve (JDox Table 1, ETC 6.0; miri_sensitivity.json,
         OCS-MIRI-DATA), crowding-penalized for the omega Cen core
  radio: no detection to 1.1 uJy at 7.25 GHz (Mahida 2026) -- both hypotheses
         predict silence in dormancy; likelihood ratio ~ 1 by construction
  R    : accretion never detected; channel inactive (ln K = 0)
  spin : no measurement yet (ln K = 0)
  kin/MSP: identical point-mass predictions for H_eng and H_q (ln K = 0);
         they act only in the H_q vs H_sub contest (mass-window cross-check)

H_eng priors (pre-registered, log-flat):
  P_comp  : log-uniform over [1, P_fuel] Lsun  (fuel ceiling from fig2/common)
  leak = 1 - f_sink : log-uniform over [1e-4, 1]  (transport floor)
  r_swarm : log-uniform over the envelope [2e-2, 4e3] AU (referee M3)
  f_warm  : log-uniform mass-fraction split between the two blackbody
            components (referee R5 5.3); the one new free parameter this
            build introduces
  dormant fraction f_d: probability the installation is dormant (P_comp -> 0);
         prior 0.5 (varied 0.1--0.9 for the sensitivity band)

MIR likelihood, continuous (R5 5.3, replacing the piecewise hard threshold):
the swarm's waste luminosity L_waste = leak * P_comp splits into a warm
component f_warm * L_waste and a cool component (1 - f_warm) * L_waste, each
re-radiated as a blackbody from the same swarm radius r via the existing
common.t_eff(L, r) -- so the SED is fixed by (L_waste, r, f_warm) with f_warm
the only new free parameter. Each component's flux density at each MIRI
filter's pivot wavelength is F_nu = pi * B_nu(T) * (r/d)^2 at d = 5.43 kpc.
A configuration is detected iff the summed (warm + cool) flux exceeds the
crowding-penalized sensitivity in ANY filter (logical OR over filters, never
a sum of per-filter significances). Filter bandpass width is not folded in:
no published per-filter bandwidth is sourced in miri_sensitivity.json, so
each filter's response is treated as a delta function at its pivot
wavelength, a stated approximation, not a claimed measurement.

The far-infrared corner (swarm cold enough that its Wien tail is negligible
at all MIRI wavelengths, <=25.5 um / F2550W) is not clamped by an assumed
placeholder limit: it falls out of the physics as simply undetected by any
filter in the array, which is the honest state (no far-IR instrument is
operating; OCS-MIRI-DATA). This replaces both the piecewise T_eff step
function and the "Wien-peak band" / "cross-band leakage" language Appendix B
previously claimed and the script did not implement (R5-V7).

Report xi = 1 - P(quiet | active) as the data-only statistic, separately
from ln K.

Outputs fig3_lnk.pdf + prints the numbers quoted in section 5.

Prior-edge sensitivity (referee R5-V3, R5-V7): every prior boundary is a
command-line parameter, because ln K here is a prior-volume ratio and the
boundaries are the levers.

  --leak-floor-dex   lower bound of the 1 - f_sink prior (default -4, the
                     Appendix A.3 transport floor; -6 is the softer alternative)
  --pcomp-floor-dex  lower bound of the P_comp prior in log10 Lsun (default 0,
                     i.e. 1 Lsun, which coincides with the warm instrument limit)
  --pcomp-ceiling    upper bound of the P_comp prior in Lsun (default: the
                     engineered-unsuppressed Bondi ceiling; 1e3 is the
                     ADIOS-suppressed natural ceiling)
  --r-range          swarm-radius prior in AU, two values
  --split-floor-dex  lower bound of the f_warm (warm mass-fraction) prior in
                     log10 (default -3: warm component can be as small as
                     0.1 per cent of the waste luminosity)
  --split-ceiling    upper bound of the f_warm prior (default 0.999: warm
                     component can dominate but never fully exclude the cool
                     one, which would make the split parameter undefined)
  --soft-threshold   replace the hard per-filter detection threshold with a
                     logistic in log10(F_nu / sensitivity) of the given width
                     in dex (0 = hard); per-filter probabilities combine as
                     P(nondetect) = product over filters of (1 - p_det,i),
                     the probabilistic form of the same OR rule
  --crowding-factor  multiplicative crowding/confusion penalty on the MIRI
                     sensitivities (default 3.0, OCS-MIRI-DATA / Paper C)

Structural note (referee R5-V1): because P(no detection | H_q) = 1, this
channel is one-sided and its evidence is capped at ln K >= ln f_d for any
depth of photometry. The script prints the capacity and the spent fraction
alongside the value. The data-only statistic is xi = 1 - P(quiet | active),
the fraction of the *active* prior volume the limits exclude; it carries no
dormancy prior.

Outputs fig3_lnk.pdf + prints the numbers quoted in section 5. The figure is
written only when every prior boundary sits at its default.
"""
import argparse
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import LSUN, AU, C, PC, mdot_bondi, t_eff, STYLE

P_FUEL = mdot_bondi() * C**2 / LSUN
DIST_M = 5.43e3 * PC          # Paper C adopted distance, 5.43 kpc
H_PLANCK = 6.62607015e-34     # J s
K_BOLTZ = 1.380649e-23        # J K^-1

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "miri_sensitivity.json")) as _fh:
    _SENS = json.load(_fh)
FILTERS = _SENS["filters"]
LAM_M = np.array([f["pivot_wavelength_um"] for f in FILTERS]) * 1e-6
SENS_UJY = np.array([f["sensitivity_ujy"] for f in FILTERS])

ap = argparse.ArgumentParser()
ap.add_argument("--leak-floor-dex", type=float, default=-4.0)
ap.add_argument("--pcomp-floor-dex", type=float, default=0.0)
ap.add_argument("--pcomp-ceiling", type=float, default=P_FUEL)
ap.add_argument("--r-range", type=float, nargs=2, default=[2e-2, 4e3])
ap.add_argument("--split-floor-dex", type=float, default=-3.0)
ap.add_argument("--split-ceiling", type=float, default=0.999)
ap.add_argument("--soft-threshold", type=float, default=0.0)
ap.add_argument("--crowding-factor", type=float, default=3.0)
args = ap.parse_args()
LEAK_FLOOR_DEX = args.leak_floor_dex
IS_DEFAULT = (LEAK_FLOOR_DEX == -4.0 and args.pcomp_floor_dex == 0.0
              and args.pcomp_ceiling == P_FUEL and args.r_range == [2e-2, 4e3]
              and args.split_floor_dex == -3.0 and args.split_ceiling == 0.999
              and args.soft_threshold == 0.0 and args.crowding_factor == 3.0)

plt.rcParams.update(STYLE)
rng = np.random.default_rng(20260717)

N = 2_000_000
SENS_JY_EFF = SENS_UJY * 1e-6 * args.crowding_factor   # crowded effective limit, Jy

R_MIN_AU, R_MAX_AU = args.r_range   # fueled inner bound to cluster stripping radius

def planck_nu(nu, T):
    """Spectral radiance B_nu(T), W m^-2 Hz^-1 sr^-1. Cold limit -> 0, not NaN."""
    with np.errstate(over="ignore", divide="ignore"):
        x = H_PLANCK * nu / (K_BOLTZ * np.maximum(T, 1e-3))
        return (2.0 * H_PLANCK * nu**3 / C**2) / np.expm1(x)

def p_quiet_given_active():
    """Fraction of the active-installation prior volume that evades every filter.

    This is the data-only statistic: no dormancy prior enters. One set of
    draws serves every f_d, so the sensitivity band uses common random
    numbers. Per-filter flux is accumulated in a loop over the 9 filters to
    keep peak memory at O(N) rather than O(N x n_filters).
    """
    logP = rng.uniform(args.pcomp_floor_dex, np.log10(args.pcomp_ceiling), N)
    logleak = rng.uniform(LEAK_FLOOR_DEX, 0, N)
    logr = rng.uniform(np.log10(R_MIN_AU), np.log10(R_MAX_AU), N)
    logsplit = rng.uniform(args.split_floor_dex, np.log10(args.split_ceiling), N)

    L_waste = 10 ** (logP + logleak) * LSUN         # W
    f_warm = 10 ** logsplit
    r_m = 10 ** logr * AU
    T_warm = t_eff(f_warm * L_waste, r_m)
    T_cool = t_eff((1.0 - f_warm) * L_waste, r_m)
    area_term = (r_m / DIST_M) ** 2                  # (R_emit / d)^2, shared by both components

    if args.soft_threshold > 0:
        log_p_nondet_total = np.zeros(N)
    else:
        detected_any = np.zeros(N, dtype=bool)

    for lam, lim_jy in zip(LAM_M, SENS_JY_EFF):
        nu = C / lam
        F_nu = np.pi * area_term * (planck_nu(nu, T_warm) + planck_nu(nu, T_cool))  # W m^-2 Hz^-1
        F_jy = F_nu / 1e-26
        if args.soft_threshold > 0:
            z = np.log10(np.maximum(F_jy, 1e-300) / lim_jy) / args.soft_threshold
            p_det = 1.0 / (1.0 + np.exp(-z))
            log_p_nondet_total += np.log(np.maximum(1.0 - p_det, 1e-300))
        else:
            detected_any |= (F_jy > lim_jy)

    if args.soft_threshold > 0:
        return float(np.mean(np.exp(log_p_nondet_total)))
    return float(np.mean(~detected_any))

def lnK_mir(f_dormant, p_qa):
    return float(np.log(f_dormant + (1 - f_dormant) * p_qa))

p_qa = p_quiet_given_active()
lnK_c = lnK_mir(0.5, p_qa)
lo = lnK_mir(0.1, p_qa)   # least dormant -> most exposed -> most negative
hi = lnK_mir(0.9, p_qa)

channels = ["MIR waste heat", "radio continuum", "$R$ statistic", "spin", "kinematics", "MSP timing"]
vals     = [lnK_c, 0.0, 0.0, 0.0, 0.0, 0.0]
los      = [lo, 0, 0, 0, 0, 0]
his      = [hi, 0, 0, 0, 0, 0]

fig, ax = plt.subplots(figsize=(6.0, 3.4))
y = np.arange(len(channels))[::-1]
ax.barh(y, vals, color=["#3b4d8f"] + ["0.7"] * 5, height=0.55)
ax.errorbar([lnK_c], [y[0]], xerr=[[lnK_c - lo], [hi - lnK_c]],
            fmt="none", ecolor="0.2", capsize=3, lw=1)
for yi, v, ch in zip(y, vals, channels):
    note = "" if ch == "MIR waste heat" else "  (inactive / degenerate: 0)"
    ax.text(0.04, yi, ch + note, va="center", fontsize=8.5)
ax.axvline(0, color="0.2", lw=1)
ax.set_yticks([]); ax.set_ylim(-1.9, len(channels) - 0.4)
ax.set_xlabel(r"per-channel $\ln K$  ($H_{\rm eng}$ vs $H_{\rm q}$), 2026 data")
ax.set_xlim(min(lo * 1.3, -1.0), 0.6)
total = sum(vals)
ax.text(0.55, -0.7,
        f"total $\\ln K = {total:+.2f}$  (band {lo:+.2f} to {hi:+.2f})\n"
        f"null-favored; surviving $H_{{\\rm eng}}$ mass: dormant or "
        f"$P_{{\\rm comp}}(1-f_{{\\rm sink}}) < L_{{\\rm lim}}$",
        fontsize=8, va="top", ha="right",
        bbox=dict(fc="#eef0f6", ec="#3b4d8f", lw=0.6))
if IS_DEFAULT:
    fig.savefig("fig3_lnk.pdf"); fig.savefig("fig3_lnk.png", dpi=110)
cap = np.log(0.5)
print(f"leak floor 1e{LEAK_FLOOR_DEX:.0f}  P_comp [1e{args.pcomp_floor_dex:.0f}, "
      f"{args.pcomp_ceiling:.2e}] Lsun  r [{R_MIN_AU:g}, {R_MAX_AU:g}] AU  "
      f"split [1e{args.split_floor_dex:.0f}, {args.split_ceiling:g}]  "
      f"soft {args.soft_threshold:g} dex  crowding x{args.crowding_factor:g}")
print(f"  xi (excluded active-prior fraction) {1-p_qa:.3f}   P(quiet|active) {p_qa:.3f}")
print(f"  lnK_MIR central {lnK_c:+.3f}  band [{lo:+.3f}, {hi:+.3f}]")
print(f"  channel capacity ln f_d = {cap:+.3f} nats; spent {lnK_c/cap:.0%}, "
      f"headroom {cap-lnK_c:+.3f}")
print(f"  P_fuel {P_FUEL:.2e} Lsun")
