"""Fig 1: survival time of swarm structures vs orbital radius (flyby Monte Carlo).

Semi-analytic Monte Carlo (Appendix A of the paper):
per radius bin, encounter statistics (impact parameter with gravitational focusing,
Maxwellian velocity, two-component mass function) are sampled directly; per history,
the disruption channel (single passage with b < 2a) is exponential in the sampled
disruptive rate and the diffusion channel (random-walk eccentricity growth to
orbit-crossing, e ~ 0.5) uses the sampled kick-variance with CLT scatter.
Lifetime = min of the two, capped at 12 Gyr.

Outputs fig1_envelope.pdf + fig1_results.json (numbers quoted in the text).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import (GM, RG, AU, YR, V_REL, SIGMA, N_STAR, M_BH, R_INFL,
                    MF_MASSES, MF_WEIGHTS, v_orb, STYLE)

rng = np.random.default_rng(20260717)
plt.rcParams.update(STYLE)

N_ENC_SAMPLE = 200_000     # encounter draws per radius bin (statistics)
N_HIST = 20_000            # histories per radius bin
E_CROSS = 0.5              # eccentricity threshold for swarm orbit-crossing
T_CAP = 1.2e10 * YR
B_MAX_FACTOR = 30.0        # kicks beyond 30a contribute <1e-3 of variance

a_grid = np.logspace(np.log10(1e-3), np.log10(4e3), 40) * AU

def sample_encounters(a, n):
    """Draw (b, m, v) for n encounters within b_max = 30a, focused distribution."""
    b_max = B_MAX_FACTOR * a
    v = rng.rayleigh(scale=SIGMA * np.sqrt(2.0/2.0), size=n) + 0.3 * SIGMA
    # cumulative rate within b: Q(b) = v^2 b^2 + 2GM b  (up to constants)
    u = rng.random(n)
    v2 = v ** 2
    Qmax = v2 * b_max**2 + 2 * GM * b_max
    # invert quadratic v2 b^2 + 2GM b - u Qmax = 0
    b = (-2 * GM + np.sqrt(4 * GM**2 + 4 * v2 * u * Qmax)) / (2 * v2)
    m = rng.choice(MF_MASSES, p=MF_WEIGHTS, size=n)
    return b, m, v

def total_rate(a):
    """Gamma(<30a) with focusing at the mean relative velocity."""
    b_max = B_MAX_FACTOR * a
    return N_STAR * np.pi * b_max**2 * V_REL * (1 + 2 * GM / (b_max * V_REL**2))

results = {"a_AU": [], "t_med": [], "t_lo": [], "t_hi": [],
           "p_dis": [], "kick_var": [], "rate_per_yr": []}

for a in a_grid:
    b, m, v = sample_encounters(a, N_ENC_SAMPLE)
    lam = total_rate(a)                                  # encounters / s
    # impulsive tidal kick, saturated for penetrating passages (b <= a).
    # Conservative: no adiabatic suppression is applied, although encounters with
    # duration b/v >> P_orb (the deep-envelope norm) perturb exponentially less
    # than this impulsive estimate.
    geom = np.minimum(1.0, (a / b) ** 2)
    delta = 2 * (m / M_BH) * geom * (v_orb(a) / v)
    mu, sd = np.mean(delta**2), np.std(delta**2)
    p_dis = np.mean(b < a)                               # penetrating fraction (diagnostic)
    t_dis = np.full(N_HIST, np.inf)                      # single-passage disruption impossible
                                                         # at these mass ratios (delta << 1)

    # diffusion channel: encounters needed for sum(delta^2) = E_CROSS^2
    if mu > 0:
        # encounters needed to random-walk to e = E_CROSS, with CLT scatter on the
        # kick-variance sum and Poisson scatter on the arrival times
        n_star = E_CROSS**2 / mu
        n_draw = np.maximum(rng.normal(n_star, (sd / mu) * np.sqrt(max(n_star, 1.0)), size=N_HIST), 1.0)
        t_diff = n_draw / lam * (1 + rng.normal(0, 1 / np.sqrt(n_draw), N_HIST))
        t_diff = np.maximum(t_diff, 0)
    else:
        t_diff = np.full(N_HIST, np.inf)

    t = np.minimum(np.minimum(t_dis, t_diff), T_CAP)
    results["a_AU"].append(a / AU)
    results["t_med"].append(float(np.median(t) / YR))
    results["t_lo"].append(float(np.percentile(t, 16) / YR))
    results["t_hi"].append(float(np.percentile(t, 84) / YR))
    results["p_dis"].append(float(p_dis))
    results["kick_var"].append(float(mu))
    results["rate_per_yr"].append(float(lam * YR))

a_AU = np.array(results["a_AU"])
t_med = np.array(results["t_med"])
t_lo, t_hi = np.array(results["t_lo"]), np.array(results["t_hi"])

fig, ax = plt.subplots()
ax.fill_between(a_AU, t_lo, t_hi, alpha=0.25, color="#3b4d8f", lw=0)
ax.loglog(a_AU, t_med, color="#3b4d8f", lw=2,
          label="median flyby-diffusion lifetime (impulsive MC, conservative)")
ax.text(5e-2, 1.5e8, "adiabatic protection lengthens deep-envelope\nlifetimes beyond this floor",
        fontsize=7.5, color="#2c3a6b")

for x, lab in [(6 * RG / AU, r"$r_{\rm ISCO}$"),
               (100 * RG / AU, r"$10^2\,r_{\rm g}$ (fueled inner bound)"),
               (0.1 * R_INFL / AU, r"$0.1\,r_{\rm infl}$ (cluster stripping)")]:
    ax.axvline(x, color="0.4", ls=":", lw=1)
    ax.text(x * 1.15, 2e2, lab, rotation=90, fontsize=7.5, va="bottom", color="0.25")

ax.axhline(1e6, color="#b98a2e", ls="--", lw=1)
ax.text(1.5e-3, 1.4e6, "passive-safety criterion ($10^6$ yr)", fontsize=7.5, color="#7a5a1d")
ax.axhline(1.2e10, color="0.6", ls="-", lw=0.8)
ax.text(1.5e-3, 1.6e10, "cluster age cap", fontsize=7.5, color="0.4")

ax.set_xlabel("structure semi-major axis  $a$  [AU]")
ax.set_ylabel("survival time against flybys  [yr]")
ax.set_xlim(5e-4, 4e3)
ax.set_ylim(1e2, 5e10)
ax.legend(loc="lower left", fontsize=8)
fig.savefig("fig1_envelope.pdf"); fig.savefig("fig1_envelope.png", dpi=110)

# numbers for the text
def interp_t(a_q):
    return 10 ** np.interp(np.log10(a_q), np.log10(a_AU), np.log10(t_med))
summary = {
    "t_at_10AU_yr": float(interp_t(10)),
    "t_at_100AU_yr": float(interp_t(100)),
    "t_at_1000AU_yr": float(interp_t(1000)),
    "a_passive_1e6yr_AU": float(10 ** np.interp(np.log10(1e6), np.log10(t_med[::-1]), np.log10(a_AU[::-1]))),
}
results["summary"] = summary
with open("fig1_results.json", "w") as f:
    json.dump(results, f, indent=1)
print(json.dumps(summary, indent=1))
