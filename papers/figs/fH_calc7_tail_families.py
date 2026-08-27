"""R7-CALC-H / H-CALC-1: fast-star speed-tail family sensitivity for the verdict
configuration (fit of record: profile leg dropped, fast-star + pulsar joint,
Plummer visible model at the kinematic distance, fiducial M/L bracket).
Pre-committed in 0xAlpha/results/R7-CALC-H.md section 0.1 (commit 77cb23f).

Families (pre-committed):
  T1  truncated polytrope (shipped; reproduction gate G-H1a)
  T2  lowered Maxwellian, King-form   p(v|r) propto v^2 [exp(-v^2/2w^2) - exp(-ve^2/2w^2)]
  T3  truncated isothermal            p(v|r) propto v^2 exp(-v^2/2w^2), hard cut

Matching rule (pre-committed): each family's w(r) solved so the truncated second
moment equals the Jeans second moment, <v^2> = 3 sigma_1d^2(r) -- the same
information the shipped polytrope index consumes. Same BW tracer cusp, same
escape-speed truncation, same selection/contamination/completeness. Differences
in ln K are pure high-velocity-tail shape.

The shipped machinery is imported read-only; alternative families are installed
by monkeypatching mock_cluster.pm_speed_pdf_at_r / .speed_pdf_local around each
build, and model tables are rebuilt with cache=False for T2/T3 (the persistent
cache holds T1-family tables keyed without the family). No RNG is drawn anywhere.

Embargo: 90 pct regions only; numbers reported, no abstract/conclusion text.
Output: fH_calc7_tail_families.json (this directory).
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.interpolate import CubicSpline

HERE = os.path.dirname(os.path.abspath(__file__))
HDIR = os.path.abspath(os.path.join(HERE, ".."))
for p in (os.path.join(HDIR, "fit2"), os.path.join(HDIR, "mock"),
          os.path.join(HDIR, "fit")):
    sys.path.insert(0, p)

import mock_cluster as mc        # noqa: E402
import load_data as L            # noqa: E402
import fit_joint as fj           # noqa: E402
import visible_model2 as vm2     # noqa: E402
import pulsar_leg as pl          # noqa: E402
import run_fit as R1             # noqa: E402

_ap = argparse.ArgumentParser()
_ap.add_argument("--visible", default="plummer")
_ap.add_argument("--dist", type=float, default=L.D_KINEMATIC)
_ap.add_argument("--tag", default="")
_args = _ap.parse_args()
VISIBLE, DIST = _args.visible, _args.dist
TAG = _args.tag
OUT_NAME = "fH_calc7_tail_families.json" if not TAG else f"fH_calc7_tail_families_{TAG}.json"
_GOLDEN_FILE = os.path.join(HDIR, "flagd", "results", "fit2_msp",
                            "fit2_results.json")
GOLDEN = json.load(open(_GOLDEN_FILE, encoding="utf-8")
                   )["configs"][f"nolegprof_{VISIBLE}_{DIST:.0f}"]["fiducial_bracket"]

# ---------------------------------------------------------------------------
# alternative local speed laws
# ---------------------------------------------------------------------------

_W_CACHE = {}


def _sigma1d_at(p, r):
    rg, s1d2 = mc.sigma1d_profile(p)
    lspl = CubicSpline(np.log(rg), np.log(s1d2))
    rr = np.clip(np.asarray(r, float), rg[0], rg[-1])
    return np.exp(lspl(np.log(rr)))


def _m2_family(vmax, w, family, gl_x, gl_w):
    """Truncated second moment <v^2> for the family, per radius (arrays)."""
    v = np.sqrt(np.outer(vmax ** 2, (gl_x + 1.0) / 2.0))         # (nr, ng)
    ww = np.broadcast_to(w[:, None], v.shape)                    # (nr, ng)
    if family == "T3":
        f = v ** 2 * np.exp(-v ** 2 / (2.0 * ww ** 2))
    else:
        lowering = np.exp(-v ** 2 / (2.0 * ww ** 2)) - \
            np.exp(-vmax ** 2 / (2.0 * w ** 2))[:, None]
        f = v ** 2 * lowering
    jacobian = v
    m2 = (f * jacobian ** 2 * gl_w[None, :]).sum(axis=1) / \
        (f * jacobian * gl_w[None, :]).sum(axis=1)
    return m2


def _w_of_r(p, family):
    key = (family, p.M_vis_eff, round(p.M_vis_eff, 12), id(None)) if False else \
        (family, p.M_vis, p.b_vis, p.nu_ML, p.M_dark, p.a_dark,
         tuple(p.vis_abg) if p.vis_abg else None)
    if key in _W_CACHE:
        return _W_CACHE[key]
    rg = np.geomspace(1e-3, 100.0, 240)
    ve = mc.v_esc(rg, p)
    s1d = _sigma1d_at(p, rg)
    target = 3.0 * s1d ** 2
    lo = np.full_like(rg, 0.02) * s1d
    hi = np.full_like(rg, 80.0) * s1d
    gl_x, gl_w = np.polynomial.legendre.leggauss(48)
    lo_m = _m2_family(ve, lo, family, gl_x, gl_w)
    hi_m = _m2_family(ve, hi, family, gl_x, gl_w)
    clipped = (lo_m > target) | (hi_m < target)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        m2 = _m2_family(ve, mid, family, gl_x, gl_w)
        too_low = m2 < target
        lo = np.where(too_low, mid, lo)
        hi = np.where(too_low, hi, mid)
    w = 0.5 * (lo + hi)
    spl = CubicSpline(np.log(rg), np.log(w))
    _W_CACHE[key] = (spl, float(clipped.mean()))
    return _W_CACHE[key]


def make_patched_pdf(family):
    orig = (mc.pm_speed_pdf_at_r, mc.speed_pdf_local)

    def pdf_local(r, v, p, _f=family):
        r = np.atleast_1d(np.asarray(r, float))
        v = np.atleast_1d(np.asarray(v, float))
        ve = mc.v_esc(r, p)[:, None]
        wspl, _cl = _w_of_r(p, _f)
        w = np.exp(wspl(np.log(np.clip(r, 1e-3, 100.0))))[:, None]
        x = np.clip(1.0 - (v[None, :] / ve) ** 2, 0.0, None)
        if _f == "T3":
            unnorm = v[None, :] ** 2 * np.exp(-v[None, :] ** 2 / (2.0 * w ** 2))
            unnorm = unnorm * (v[None, :] <= ve)
        else:
            lowering = np.exp(-v[None, :] ** 2 / (2.0 * w ** 2)) - \
                np.exp(-ve ** 2 / (2.0 * w ** 2))
            unnorm = v[None, :] ** 2 * np.clip(lowering, 0.0, None)
        from scipy.integrate import simpson
        norm = simpson(unnorm, x=v[None, :], even="first") if False else \
            np.trapezoid(unnorm, v[None, :], axis=1)
        return unnorm / norm[:, None]

    def pdf_pm(r, v_pm, p, n_w=40, _f=family):
        r = np.atleast_1d(np.asarray(r, float))
        v_pm = np.atleast_1d(np.asarray(v_pm, float))
        ve = mc.v_esc(r, p)
        wspl, _cl = _w_of_r(p, _f)
        w_scale = np.exp(wspl(np.log(np.clip(r, 1e-3, 100.0))))
        wmax = np.sqrt(np.clip(ve[:, None] ** 2 - v_pm[None, :] ** 2, 0.0, None))
        t = (np.arange(n_w) + 0.5) / n_w
        wq = wmax[:, :, None] * t[None, None, :]
        v = np.sqrt(v_pm[None, :, None] ** 2 + wq ** 2)
        ws = w_scale[:, None, None] * np.ones_like(v)
        if _f == "T3":
            f3d = v ** 2 * np.exp(-v ** 2 / (2.0 * ws ** 2))
            f3d = np.where(v <= ve[:, None, None], f3d, 0.0)
        else:
            lowering = np.exp(-v ** 2 / (2.0 * ws ** 2)) - \
                np.exp(-ve[:, None, None] ** 2 / (2.0 * ws ** 2))
            f3d = v ** 2 * np.clip(lowering, 0.0, None)
        norm = np.trapezoid(f3d * v_pm[None, :, None] / v ** 2, wq, axis=2)
        p3d_un = np.where(v <= ve[:, None, None], f3d, 0.0)
        proj = np.trapezoid(p3d_un * v_pm[None, :, None] / v ** 2, wq, axis=2)
        out = np.zeros_like(proj)
        good = norm > 0
        out[good] = proj[good] / norm[good]
        return out

    return orig, pdf_pm, pdf_local


# ---------------------------------------------------------------------------
# pipeline
# ---------------------------------------------------------------------------

hw = vm2.bracket_half_width([vm2.calibrate(v, d) for v, d in vm2.CONFIGS])
ML = tuple(vm2.ml_brackets(hw))
print("M/L brackets:", ML)

cal = vm2.calibrate(VISIBLE, DIST)
kw = vm2.visible_kwargs(VISIBLE)
cluster = {"M_vis": cal["M_vis"], "b_vis": vm2.B_VIS_PC, **kw}
grid = fj.PriorGrid(ml_brackets=ML)
sel = L.selection(distance_pc=DIST)
prof_R = L.profiles(distance_pc=DIST)["R_pc"]
data_fs = L.fast_stars(distance_pc=DIST, robust_only=True)
data_ps = L.pulsars(distance_pc=DIST, source="trapum")

results = {"meta": dict(wu="R7-CALC-H", part="H-CALC-1", date="2026-08-23",
                        config=f"nolegprof_{VISIBLE}_{DIST:.0f}, fiducial bracket",
                        matching="truncated <v^2> = 3 sigma_1d^2(r)",
                        golden=GOLDEN), "families": {}}

# Amendment H-CALC-1a (dated 2026-08-23, disclosed): the pre-committed
# moment-matching rule has NO solution for Maxwellian-type families inside the
# Bahcall-Wolf cusp -- their truncated second moments cap at ve^2/2, while cusp
# consistency requires sigma_1d^2 = Psi/(gamma+1), i.e. the target 3 sigma_1d^2
# exceeds ve^2/2 wherever Psi/sigma_1d^2 < 3, which holds throughout r_infl
# (gamma+1 = 2.75). The clamped T2/T3 runs below are retained as finding (A);
# the operative bracket is amendment (B): the polytrope exponent shifted by
# delta in {-0.25, +0.5}, heavier and lighter tails under the identical
# matching rule, always solvable.
PRIOR_CLAMPED_RUN = os.path.join(HERE, "fH_calc7_tail_families.json")
if os.path.exists(PRIOR_CLAMPED_RUN):
    _prev = json.load(open(PRIOR_CLAMPED_RUN, encoding="utf-8"))
    for k in ("T2", "T3"):
        if k in _prev.get("families", {}):
            results["families"][k + "_clamped_moment_rule"] = _prev["families"][k]
    results["amendment_1a"] = dict(
        rule="moment-match Maxwellian-type families inside the BW cusp",
        outcome="infeasible: target <v^2> = 3 sigma_1d^2 exceeds the family "
                "maximum ve^2/2 wherever Psi/sigma_1d^2 < 3 (holds throughout "
                "r_infl under the BW consistency sigma_1d^2 = Psi/(gamma+1), "
                "gamma+1 = 2.75)",
        corroboration="shipped polytrope index clips at N_INDEX_MIN = 0.25 "
                      "(mock_cluster.py) for the same reason",
        consequence="clamped runs reverse the verdict; see families T2_/T3_"
                    "_clamped_moment_rule")

orig_pi = mc.polytrope_index


def make_delta_patch(delta):
    def pi_patched(r, p):
        base = orig_pi(r, p)
        return np.clip(base + delta, mc.N_INDEX_MIN, mc.N_INDEX_MAX)
    return pi_patched

orig_refs = None
for family in ("T1", "Tm025", "Tp05"):
    print(f"== family {family}", flush=True)
    if family == "T1":
        use_cache = True
    else:
        delta = -0.25 if family == "Tm025" else 0.5
        mc.polytrope_index = make_delta_patch(delta)
        use_cache = False
    try:
        model = fj.JointModel(cluster, sel, prof_R, grid=grid,
                              cache=use_cache, verbose=False)
        R1.anchor_intensity(model)
        fs = fj.loglike_fast(model, data_fs)
        psr = pl.loglike_pulsars_censored(model, data_ps)
        total = (fs[..., None] + psr[..., None]) * np.ones(len(grid.r_a))

        lnK_full = float(fj.ln_bayes_compact_extended(
            total, grid, 1, compact_max=R1.COMPACT_MAX,
            extended_min=R1.EXTENDED_MIN))
        P = fj.posterior(total, grid, 1)
        comp_mass = float(P[:, grid.a_dark < R1.COMPACT_MAX].sum())
        ext_mass = float(P[:, grid.a_dark > R1.EXTENDED_MIN].sum())
        iM, ia = np.unravel_index(int(np.argmax(P)), P.shape)
        ul = float(fj.upper_limit_M(P, grid))
        # marginal-HPD90 interval in M_dark (90 pct regions only)
        pm = fj.marginal_M(P, grid)
        thr = fj.hpd_threshold(P, 0.90)
        colmask = (P >= thr).any(axis=1)
        m_lo, m_hi = float(grid.M_dark[colmask].min()), float(grid.M_dark[colmask].max())

        cell_lnks = []
        for bi in range(len(ML)):
            for mr_label, mr in R1.M_SWEEPS:
                for ar_label, ar in R1.A_SWEEPS:
                    cp = R1.cell_products(total, grid, bi, mr, ar)
                    lk = cp["lnK"]
                    cell_lnks.append(dict(bracket=ML[bi][0], M_range=mr_label,
                                          a_range=ar_label,
                                          lnK=(None if not np.isfinite(lk) else float(lk))))
        fin = [c["lnK"] for c in cell_lnks if c["lnK"] is not None]

        results["families"][family] = dict(
            delta=(-0.25 if family == "Tm025" else (0.5 if family == "Tp05" else 0.0)),
            lnK_fulldomain=lnK_full, compact_mass=comp_mass, extended_mass=ext_mass,
            map_M_dark=float(grid.M_dark[iM]), map_a_dark=float(grid.a_dark[ia]),
            M_ul90=ul, hpd90_M_marginal=[m_lo, m_hi],
            cells_defined=len(fin), cells_lnK_range=[min(fin), max(fin)],
            cells_all_positive=bool(all(c > 0 for c in fin)))
        print(f"   lnK(full domain)={lnK_full:+.4f}  compact mass={comp_mass:.4f}  "
              f"MAP M={grid.M_dark[iM]:.4e} @ a={grid.a_dark[ia]:.4g}  "
              f"UL90={ul:.4e}")
        print(f"   HPD90 M marginal [{m_lo:.4e}, {m_hi:.4e}]  "
              f"defined cells {len(fin)} range [{min(fin):+.3f}, {max(fin):+.3f}]"
              f"  all positive {all(c > 0 for c in fin)}")
    finally:
        if family != "T1":
            mc.polytrope_index = orig_pi

t1 = results["families"]["T1"]
g_ok = (abs(t1["lnK_fulldomain"] - GOLDEN["lnK"]) < 1e-9
        and abs(t1["compact_mass"] - GOLDEN["compact_mass"]) < 1e-9
        and abs(t1["map_M_dark"] - GOLDEN["map_M_dark"]) < 1e-6
        and abs(t1["M_ul90"] - GOLDEN["M_ul90"]) < 1e-6)
results["gate_GH1a_pass"] = bool(g_ok)
print("G-H1a (T1 reproduction of released fit-of-record):",
      "PASS" if g_ok else "FAIL")

with open(os.path.join(HERE, OUT_NAME), "w") as fh:
    json.dump(results, fh, indent=1)
if not g_ok:
    raise SystemExit(1)
print("tail-family sensitivity complete")
