"""Fig 3: worked-example ln K per channel, H_eng vs H_q (best null), omega Cen today.

Appendix B model, deliberately minimal and fully stated:

Channels and data (2026):
  MIR  : point-source limit L_lim = 1 Lsun at kinematic centre (Chen 2025 JWST)
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
  dormant fraction f_d: probability the installation is dormant (P_comp -> 0);
         prior 0.5 (varied 0.1--0.9 for the sensitivity band)

MIR likelihood (radius-dependent, referee M3): the swarm re-radiates
L_waste = leak * P_comp at T_eff(r) = (L / 4 pi r^2 sigma_SB)^{1/4}; detection
iff L_waste > L_lim(T_eff), the piecewise instrument limit of common.L_lim_mir
(JWST/MIRI warm; WISE/MIPS cool, confusion-limited).  Data = no detection.
  P(no det | H_eng) = f_d + (1 - f_d) * P(L_waste < L_lim(T_eff))
  P(no det | H_q)   = 1
ln K_MIR = ln P(no det | H_eng)  (negative: H_eng pays for its detectable prior mass)

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
  --soft-threshold   replace the hard detection threshold with a logistic in
                     log10(L_waste / L_lim) of the given width in dex (0 = hard)
  --mips70-scale     multiply the T < 50 K (MIPS 70 um) limit by this factor
  --lmid-scale       multiply the 50-150 K (WISE/MIPS 24) limit by this factor

Structural note (referee R5-V1): because P(no detection | H_q) = 1, this channel
is one-sided and its evidence is capped at ln K >= ln f_d for any depth of
photometry.  The script prints the capacity and the spent fraction alongside the
value.  The data-only statistic is xi = 1 - P(quiet | active), the fraction of
the *active* prior volume the limits exclude; it carries no dormancy prior.

Outputs fig3_lnk.pdf + prints the numbers quoted in section 5.  The figure is
written only when every prior boundary sits at its default.
"""
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import LSUN, AU, C, mdot_bondi, t_eff, L_lim_mir, STYLE

P_FUEL = mdot_bondi() * C**2 / LSUN

ap = argparse.ArgumentParser()
ap.add_argument("--leak-floor-dex", type=float, default=-4.0)
ap.add_argument("--pcomp-floor-dex", type=float, default=0.0)
ap.add_argument("--pcomp-ceiling", type=float, default=P_FUEL)
ap.add_argument("--r-range", type=float, nargs=2, default=[2e-2, 4e3])
ap.add_argument("--soft-threshold", type=float, default=0.0)
ap.add_argument("--mips70-scale", type=float, default=1.0)
ap.add_argument("--lmid-scale", type=float, default=1.0)
args = ap.parse_args()
LEAK_FLOOR_DEX = args.leak_floor_dex
IS_DEFAULT = (LEAK_FLOOR_DEX == -4.0 and args.pcomp_floor_dex == 0.0
              and args.pcomp_ceiling == P_FUEL and args.r_range == [2e-2, 4e3]
              and args.soft_threshold == 0.0 and args.mips70_scale == 1.0
              and args.lmid_scale == 1.0)

plt.rcParams.update(STYLE)
rng = np.random.default_rng(20260717)

L_LIM = 1.0
N = 2_000_000

R_MIN_AU, R_MAX_AU = args.r_range   # fueled inner bound to cluster stripping radius

def p_quiet_given_active():
    """Fraction of the active-installation prior volume that evades the limits.

    This is the data-only statistic: no dormancy prior enters.  One set of draws
    serves every f_d, so the sensitivity band uses common random numbers.
    """
    logP = rng.uniform(args.pcomp_floor_dex, np.log10(args.pcomp_ceiling), N)
    logleak = rng.uniform(LEAK_FLOOR_DEX, 0, N)
    logr = rng.uniform(np.log10(R_MIN_AU), np.log10(R_MAX_AU), N)
    L_waste = 10 ** (logP + logleak) * LSUN            # W
    T = t_eff(L_waste, 10 ** logr * AU)
    lim = L_lim_mir(T)
    # rescale the two confusion-limited wedges if asked (T thresholds unchanged)
    lim = np.where(T < 50.0, lim * args.mips70_scale,
                   np.where(T < 150.0, lim * args.lmid_scale, lim))
    if args.soft_threshold > 0:
        # logistic detection probability in log10(L/L_lim); width in dex
        z = np.log10(L_waste / lim) / args.soft_threshold
        p_det = 1.0 / (1.0 + np.exp(-z))
        return float(np.mean(1.0 - p_det))
    return float(np.mean(L_waste < lim))

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
      f"soft {args.soft_threshold:g} dex  mips70x{args.mips70_scale:g} midx{args.lmid_scale:g}")
print(f"  xi (excluded active-prior fraction) {1-p_qa:.3f}   P(quiet|active) {p_qa:.3f}")
print(f"  lnK_MIR central {lnK_c:+.3f}  band [{lo:+.3f}, {hi:+.3f}]")
print(f"  channel capacity ln f_d = {cap:+.3f} nats; spent {lnK_c/cap:.0%}, "
      f"headroom {cap-lnK_c:+.3f}")
print(f"  P_fuel {P_FUEL:.2e} Lsun")
