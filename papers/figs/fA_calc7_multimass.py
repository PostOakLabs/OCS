"""R7-CALC-AB addendum: multi-mass sensitivity row for the enclosed-mass profile.

Closes evaluation section 8.1 item S1-2 (the single-mass limitation disclosed
in R7-CALC-AB section 2.1).  Pre-committed here before the variants ran:

  Enhancement bracket: the central tracer density of the fuel-census profile
  is scaled by a mass-segregation enhancement factor of 2x (modest bracket;
  Paper E's bound-cusp model uses x10 for the remnant population, while the
  tracer here is the light-star mass that feeds the fuel census).  A single
  King model with all three anchors held (c, r_c, M_cl) cannot carry an
  independent central-density scaling -- rho_c is determined -- so the
  bracket is computed as two variants that each break one anchor, labelled:

    Variant E (density-scaled; the literal reading):
      rho_c -> 2 rho_c, dimensionless shape and r_c held.
      M(<r) doubles at every radius; M_total doubles to 8e6 Msun.
      Anchor broken: total cluster mass (paper prints 4e6).

    Variant M (mass-preserving companion):
      rho_c -> 2 rho_c with M_total held at 4e6 Msun and the same
      dimensionless shape (same W_0, same c), achieved by shrinking the
      structural radius r_c -> r_c / 2^(1/3).
      Anchor broken: r_c moves off the Harris 2.37' value.

  Depletion percentages recomputed at the corrected delivered mass
  Delta M = 2.4048e4 Msun (A-M3) in both variants and in the shipped
  single-mass baseline.

Gates (before any variant number is quoted):
  G-M1a  this script's King rebuild reproduces the shipped fA_calc7_profile.json
         enclosed masses M(<1/2/10 pc) to < 1e-10 relative.
  G-M1b  W_0 = 6.217 and model concentration = 1.31 (the shipped shot).

Deterministic; no randomness.  The King integrator is copied verbatim from
fA_calc7_v1.py (lines 104-185) so the two scripts share one numerical path.
Output: fA_calc7_multimass.json (this directory).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- constants (fA_calc7_v1.py)
M_CL = 4e6
RC_AMIN = 2.37
CONC = 1.31
D_KPC = 5.49
MEAN_STAR = 0.43
DELIVERED = 2.4048e4
ENH = 2.0
RADII = [1.0, 2.0, 10.0]

# ---------------------------------------------------------------- King integrator
# (copied verbatim from fA_calc7_v1.py lines 104-185; see docstring)


def rho_raw(W):
    if W <= 0:
        return 0.0
    return math.exp(W) * math.erf(math.sqrt(W)) - math.sqrt(4 * W / math.pi) * (1 + 2 * W / 3)


def king_curve(W0, ds=0.005):
    norm = rho_raw(W0)
    x0 = 1e-3
    W = W0 - 1.5 * x0 * x0
    y = -3 * x0

    def f(sv, state):
        xx = x0 * math.exp(sv)
        return [state[1], -state[1] - 9 * xx * xx * rho_raw(state[0]) / norm]

    xs, Ws = [x0], [W]
    s = 0.0
    while True:
        k1 = f(s, (W, y))
        k2 = f(s + ds / 2, (W + ds / 2 * k1[0], y + ds / 2 * k1[1]))
        k3 = f(s + ds / 2, (W + ds / 2 * k2[0], y + ds / 2 * k2[1]))
        k4 = f(s + ds, (W + ds * k3[0], y + ds * k3[1]))
        W_n = W + ds / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        y_n = y + ds / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        if W_n <= 0:
            fr = W / (W - W_n)
            s_t = s + ds * min(max(fr, 0.0), 1.0)
            xs.append(x0 * math.exp(s_t))
            Ws.append(0.0)
            break
        s += ds
        W, y = W_n, y_n
        xs.append(x0 * math.exp(s))
        Ws.append(W)
    return xs, Ws, xs[-1]


def shoot_concentration(target=CONC):
    lo, hi = 2.0, 12.0
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        _, _, xt = king_curve(mid, ds=0.01)
        cc = math.log10(xt)
        if cc < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def enclosed_mass_fraction(xs, Ws, norm):
    cum = [0.0]
    for i in range(1, len(xs)):
        hstep = xs[i] - xs[i - 1]
        g = xs[i] ** 2 * rho_raw(Ws[i]) / norm + xs[i - 1] ** 2 * rho_raw(Ws[i - 1]) / norm
        cum.append(cum[-1] + 0.5 * hstep * g)
    tot = cum[-1]

    def frac(xq):
        import bisect
        i = min(bisect.bisect_left(xs, xq) - 1, len(xs) - 2)
        i = max(i, 0)
        t = (xq - xs[i]) / (xs[i + 1] - xs[i])
        t = min(max(t, 0.0), 1.0)
        return (cum[i] + t * (cum[i + 1] - cum[i])) / tot

    return frac, tot


# ---------------------------------------------------------------- run
def main():
    shipped = json.load(open(os.path.join(HERE, "fA_calc7_profile.json")))
    shipped_enc = shipped["enclosed"]
    shipped_king = shipped["king"]

    # rebuild
    W0 = shoot_concentration()
    xs, Ws, x_t = king_curve(W0, ds=0.005)
    norm = rho_raw(W0)
    frac, _tot = enclosed_mass_fraction(xs, Ws, norm)
    rc_pc = RC_AMIN * D_KPC * 1000.0 * (math.pi / 10800.0)  # 3.785 pc (arcmin->pc, no /60)

    base = {}
    for r in RADII:
        base[str(r)] = M_CL * frac(r / rc_pc)

    # gates
    g1a_devs = [abs(base[str(r)] / shipped_enc[str(r)]["Msun"] - 1.0) for r in RADII]
    g1a = max(g1a_devs) < 1e-10
    g1b = (abs(W0 - shipped_king["W0"]) < 1e-10
           and abs(math.log10(x_t) - shipped_king["concentration"]) < 1e-10)
    gates = {"G_M1a_rebuild_matches_shipped": {"max_rel_dev": max(g1a_devs),
                                               "pass": g1a},
             "G_M1b_W0_conc_match_shipped": {"W0": W0,
                                             "W0_shipped": shipped_king["W0"],
                                             "conc": math.log10(x_t),
                                             "conc_shipped": shipped_king["concentration"],
                                             "pass": g1b}}
    status = "PASS" if (g1a and g1b) else "FAIL"
    print(f"[{status}] gates G-M1a/G-M1b: rebuild max rel dev {max(g1a_devs):.2e}, "
          f"W0={W0:.4f}, c={math.log10(x_t):.4f}")
    if not (g1a and g1b):
        print("STOP: gate failure (rule 5b)")
        return

    dep = lambda m: 100.0 * DELIVERED / m

    baseline = {"M_lt_r": {str(r): base[str(r)] for r in RADII},
                "depletion_pct": {str(r): dep(base[str(r)]) for r in RADII},
                "stars_lt_r_043": {str(r): base[str(r)] / MEAN_STAR for r in RADII}}

    # Variant E: density-scaled (literal reading).  Shape and r_c held;
    # rho_c x2 => M(<r) x2 at every radius; M_total doubles to 8e6 (flagged).
    var_e = {"M_lt_r": {str(r): 2.0 * base[str(r)] for r in RADII},
             "depletion_pct": {str(r): dep(2.0 * base[str(r)]) for r in RADII},
             "M_total_Msun": 2.0 * M_CL,
             "anchor_broken": "total cluster mass (8e6 vs paper's 4e6)"}

    # Variant M: mass-preserving.  Same shape, rho_c x2, r_c -> r_c/2^(1/3).
    f_shrink = ENH ** (-1.0 / 3.0)
    rc_m_pc = rc_pc * f_shrink
    rc_m_amin = rc_m_pc / (D_KPC * 1000.0 * (math.pi / 10800.0))
    var_m = {"M_lt_r": {str(r): M_CL * frac(r / rc_m_pc) for r in RADII},
             "r_c_eff_pc": rc_m_pc, "r_c_eff_amin": rc_m_amin,
             "M_total_Msun": M_CL,
             "anchor_broken": "r_c (1.88' vs Harris 2.37')"}
    var_m["depletion_pct"] = {str(r): dep(var_m["M_lt_r"][str(r)]) for r in RADII}
    var_m["stars_lt_r_043"] = {str(r): var_m["M_lt_r"][str(r)] / MEAN_STAR
                               for r in RADII}

    print("\n--- multi-mass sensitivity bracket (2x central tracer enhancement) ---")
    print(f"{'quantity':>22s} {'baseline':>12s} {'variant E':>12s} {'variant M':>12s}")
    for r in RADII:
        k = str(r)
        print(f"M(<{r} pc) Msun   {base[k]:12.4e} {var_e['M_lt_r'][k]:12.4e} {var_m['M_lt_r'][k]:12.4e}")
    for r in RADII:
        k = str(r)
        print(f"depletion {r} pc %   {dep(base[k]):12.2f} {var_e['depletion_pct'][k]:12.2f} {var_m['depletion_pct'][k]:12.2f}")
    print(f"variant E breaks the total-mass anchor (8e6 Msun); "
          f"variant M breaks the Harris r_c anchor (1.88' vs 2.37')")

    out = {"_meta": {"script": "paper/figs/fA_calc7_multimass.py",
                     "date": "2026-08-25",
                     "closes": "evaluation section 8.1 item S1-2 (single-mass limitation)",
                     "enhancement": ENH,
                     "delivered_Msun": DELIVERED,
                     "variants": {"E": "rho_c x2, shape+r_c held, M_total doubles (literal reading)",
                                  "M": "rho_c x2, M_total+shape held, r_c shrinks by 2^(-1/3)"}},
           "gates": gates,
           "baseline_single_mass": baseline,
           "variant_E_density_scaled": var_e,
           "variant_M_mass_preserving": var_m}
    with open(os.path.join(HERE, "fA_calc7_multimass.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("\nwritten fA_calc7_multimass.json")

if __name__ == "__main__":
    main()
