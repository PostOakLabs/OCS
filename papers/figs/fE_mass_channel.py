"""E-R9-03 / E-R8-01: score the engineered-mass channel, or show that it cannot carry
the claim made for it.

Section 5 has called M ~ 1.1e5 Msun "a second, already-observable discriminant"
that "sits above the TRAPUM 2026 ceiling" while Appendix C simultaneously scored
the kinematic and timing channels at ln K = 0 each.  Both cannot stand.  This
script prices the channel so the paper can say which.

Construction (every stipulation named):

  Merger-history mass.  Both hypotheses inherit the same growth history, so the
  same prior has to describe it under each.  Section 5.3's own H_gas prior is
  log-uniform over [1e4, 5e4] Msun and that is the primary here.  The paper has
  elsewhere used the Gonzalez Prieto et al. (2025) endpoint ~5e4 Msun as a point
  value; that reading is carried as the stated alternative, since it is the one
  the "1.1e5" figure was computed from.

  Spin-up branch.  H_eng requires a completed spin-up episode (Sec. 5).  If it
  ran LAST, the observed mass carries the full 2.2024x growth factor.  If it ran
  EARLY, the merger growth that followed delivers the observed endpoint and the
  factor is absorbed, leaving H_eng's mass distribution equal to H_gas's.  The
  branch weight w = P(late | H_eng) has no warrant in either direction; w = 0.5
  is the fiducial and 0.1-0.9 the reported band, mirroring the dormancy prior's
  treatment in fig3_lnk.py.

  Likelihood.  The TRAPUM 2026 timing ceiling (Colom i Bernadich et al. 2026) is
  M < 1e5 Msun at 90 per cent.  Translating a quoted one-sided confidence level
  into a likelihood ratio requires an assumption; we take
  lambda_T = (1 - C)/C = 0.111 at C = 0.90, which reads the quoted confidence as
  posterior odds under an equal prior split across the boundary.  That is a
  STIPULATION, not a result, so ln K is reported over a C grid as well.
  Haberle et al. (2024)'s 8.2e3 Msun kinematic lower bound is inert here: every
  draw under both hypotheses already exceeds it.  It is applied anyway so the
  omission is not silent.

  Not scored.  The kinematic mass measurement itself is NOT used as a
  discriminant.  Series policy does not collapse the mass tension in either
  direction, and doing so here would decide H_gas vs H_sub as a side effect.
  Only the TRAPUM upper limit enters.
"""
import json
import numpy as np

SPINUP_FACTOR = 2.2024          # Sec. 5 footnote, own numerical integration
M_CEIL = 1.0e5                  # Msun, TRAPUM 2026 timing ceiling
M_FLOOR = 8.2e3                 # Msun, Haberle 2024 kinematic lower bound
M_GAS_LO, M_GAS_HI = 1.0e4, 5.0e4   # Sec. 5.3 H_gas mass prior
M_ENDPOINT = 5.0e4              # GP2025 merger-only endpoint, point reading

N = 2_000_000
rng = np.random.default_rng(20260903)


def lam_T(conf):
    """Likelihood ratio above vs below the ceiling, from a quoted confidence."""
    return (1.0 - conf) / conf


def like(M, lam):
    """TRAPUM upper limit plus the (inert) kinematic lower bound."""
    L = np.where(M > M_CEIL, lam, 1.0)
    return np.where(M < M_FLOOR, 0.0, L)


def lnK_mass(w, lam, prior="range"):
    """ln [ P(d | H_eng) / P(d | H_gas) ] for the mass channel."""
    if prior == "range":
        M_merger = 10 ** rng.uniform(np.log10(M_GAS_LO), np.log10(M_GAS_HI), N)
    elif prior == "point":
        M_merger = np.full(N, M_ENDPOINT)
    else:
        raise ValueError(prior)
    late = rng.random(N) < w
    M_eng = np.where(late, SPINUP_FACTOR * M_merger, M_merger)
    p_eng = float(np.mean(like(M_eng, lam)))
    p_gas = float(np.mean(like(M_merger, lam)))
    return float(np.log(p_eng / p_gas)), p_eng, p_gas


out = {"spinup_factor": SPINUP_FACTOR, "M_ceiling": M_CEIL, "M_floor": M_FLOOR,
       "M_gas_prior": [M_GAS_LO, M_GAS_HI], "M_endpoint_point": M_ENDPOINT,
       "N_draws": N, "conf_fiducial": 0.90, "lambda_T_fiducial": lam_T(0.90)}

# fraction of each branch that clears the ceiling, analytic cross-check
frac_above = np.log(M_GAS_HI / (M_CEIL / SPINUP_FACTOR)) / np.log(M_GAS_HI / M_GAS_LO)
out["late_branch_fraction_above_ceiling_analytic"] = float(max(0.0, frac_above))

for prior in ("range", "point"):
    block = {}
    lam = lam_T(0.90)
    for w in (0.1, 0.5, 0.9):
        k, pe, pg = lnK_mass(w, lam, prior)
        block["w=%.1f" % w] = {"lnK": k, "P_d_given_Heng": pe, "P_d_given_Hgas": pg}
    # sensitivity to the confidence-to-likelihood stipulation, at w = 0.5
    conf_curve = {}
    for conf in (0.68, 0.90, 0.95, 0.99):
        k, _, _ = lnK_mass(0.5, lam_T(conf), prior)
        conf_curve["C=%.2f" % conf] = {"lambda_T": lam_T(conf), "lnK": k}
    block["confidence_curve_w0.5"] = conf_curve
    out[prior] = block

LNK_MIR = -0.474        # fig3_lnk.py, unchanged by anything in this script
out["lnK_MIR_unchanged"] = LNK_MIR
out["total_range_w0.5"] = LNK_MIR + out["range"]["w=0.5"]["lnK"]
out["total_point_w0.5"] = LNK_MIR + out["point"]["w=0.5"]["lnK"]

with open("fE_mass_channel.json", "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps(out, indent=1))
