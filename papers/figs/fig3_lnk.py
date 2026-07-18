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
  dormant fraction f_d: probability the installation is dormant (P_comp -> 0);
         prior 0.5 (varied 0.1--0.9 for the sensitivity band)

MIR likelihood: detection iff L_waste = leak * P_comp > L_lim (hard threshold;
a soft threshold changes ln K by < 0.1). Data = no detection.
  P(no det | H_eng) = f_d + (1 - f_d) * P(leak * P < L_lim)
  P(no det | H_q)   = 1
ln K_MIR = ln P(no det | H_eng)  (negative: H_eng pays for its detectable prior mass)

Outputs fig3_lnk.pdf + prints the numbers quoted in section 5.

Sensitivity: the transport floor (Appendix A.3) is an engineering estimate, so the
leak prior's lower bound is a parameter. Pass --leak-floor-dex (default -4, the
fiducial 1 - f_sink >= 1e-4); -6 is the pessimistic-for-the-bound alternative
quoted in section 5 and section 6.1. Figure output is written only for the default.
"""
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import LSUN, C, mdot_bondi, STYLE

ap = argparse.ArgumentParser()
ap.add_argument("--leak-floor-dex", type=float, default=-4.0)
args = ap.parse_args()
LEAK_FLOOR_DEX = args.leak_floor_dex

plt.rcParams.update(STYLE)
rng = np.random.default_rng(20260717)

P_FUEL = mdot_bondi() * C**2 / LSUN
L_LIM = 1.0
N = 2_000_000

def lnK_mir(f_dormant):
    logP = rng.uniform(np.log10(1.0), np.log10(P_FUEL), N)
    logleak = rng.uniform(LEAK_FLOOR_DEX, 0, N)
    p_quiet_active = np.mean(10 ** (logP + logleak) < L_LIM)
    return np.log(f_dormant + (1 - f_dormant) * p_quiet_active), p_quiet_active

lnK_c, p_qa = lnK_mir(0.5)
lo, _ = lnK_mir(0.1)     # least dormant -> most exposed -> most negative
hi, _ = lnK_mir(0.9)

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
if LEAK_FLOOR_DEX == -4.0:
    fig.savefig("fig3_lnk.pdf"); fig.savefig("fig3_lnk.png", dpi=110)
print(f"floor 1e{LEAK_FLOOR_DEX:.0f}  lnK_MIR central {lnK_c:+.3f}  band [{lo:+.3f}, {hi:+.3f}]  "
      f"P(quiet|active) {p_qa:.3f}  P_fuel {P_FUEL:.2e} Lsun")
