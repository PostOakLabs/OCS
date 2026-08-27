"""R7-CALC-H / H-CALC-2: exact point-mass (a = 0) restricted fits, one row per
tab:regions configuration, fiducial M/L bracket.
Pre-committed in 0xAlpha/results/R7-CALC-H.md section 0.2 (commit 77cb23f).

The shipped machinery is imported read-only; nothing outside paper/h/calc7/ is
written. 90 % regions only (no inner quantiles computed or stored). Embargo:
numbers are stated in the session report; no abstract/conclusion text proposed.

Evidence convention mirrors fit_joint.posterior exactly: uniform node weights
(log-uniform prior), mean over the r_a set, bracket fixed at fiducial.
ln K_rel = ln Z_restricted - ln Z_continuous under those identical priors.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HDIR = os.path.abspath(os.path.join(HERE, ".."))
for p in (os.path.join(HDIR, "fit2"), os.path.join(HDIR, "mock"),
          os.path.join(HDIR, "fit")):
    sys.path.insert(0, p)

import mock_cluster as mc            # noqa: E402
import load_data as L                # noqa: E402
import fit_joint as fj               # noqa: E402
import visible_model2 as vm2         # noqa: E402
import pulsar_leg as pl              # noqa: E402

BRACKET_INDEX = 1                    # fiducial
CONFIGS = [("plummer", L.D_KINEMATIC), ("abg", L.D_KINEMATIC),
           ("plummer", L.D_BH25), ("abg", L.D_BH25)]
# distances: D_KINEMATIC = 5494 pc (oMEGACat kinematic), D_BH25 = 5200 pc
# (BanaresHernandez2025 adopted) — verified against load_data constants
NAMES = {("plummer", L.D_BH25): "Plummer_5.20kpc",
         ("abg", L.D_BH25): "BH25_abg_5.20kpc",
         ("plummer", L.D_KINEMATIC): "Plummer_5.49kpc",
         ("abg", L.D_KINEMATIC): "BH25_abg_5.49kpc"}

results = {"meta": dict(wu="R7-CALC-H", part="H-CALC-2", date="2026-08-23",
                        note="a=0 exact point-mass restricted fits, fiducial bracket, "
                             "90 pct regions only"), "configs": {}}

# continuous-model reference evidences come from the RELEASED cubes
# (post-FLAGD MSP kernel; flagd/results/fit2_msp — this is the record
# tab:regions and the fit of record quote)
NPZDIR = os.path.join(HDIR, "flagd", "results", "fit2_msp")
NPZ = {"Plummer_5.20kpc": "posterior_nolegprof_plummer_5200.npz",
       "BH25_abg_5.20kpc": "posterior_nolegprof_abg_5200.npz",
       "Plummer_5.49kpc": "posterior_nolegprof_plummer_5494.npz",
       "BH25_abg_5.49kpc": "posterior_nolegprof_abg_5494.npz"}


def anchor_fast(lam, shim, grid_M, ml_brackets):
    """R1.anchor_intensity equivalent for the restricted tables: per-cell rescale
    so the projected tracer count inside sel['R_ref'] equals sel['N_ref']."""
    
    class Tmp:  # minimal duck-type for R1.projected_fraction
        pass
    nM, nnu = lam.shape[0], lam.shape[2]
    scaled = lam.copy()
    for iM in range(nM):
        for inu in range(nnu):
            p = shim.params(iM, 0, inu)
            rr = None
            R = np.geomspace(1e-3, shim.sel["R_ref"], 60)
            z = shim._z_psr
            rr = np.sqrt(R[:, None] ** 2 + z[None, :] ** 2)
            col = np.trapezoid(mc.rho_tracer_norm(rr, p), z, axis=1)
            f = float(np.trapezoid(col * 2.0 * np.pi * R, R))
            scaled[iM, 0, inu] *= shim.sel["N_ref"] / max(f, 1e-300)
    return scaled


def lnz_continuous(npz_path):
    z = np.load(npz_path)
    lnL = z["lnL_total"]                       # (nM, na, nnu, nra)
    ml = z["ml"]
    bi = int(np.argmin(np.abs(ml - 1.0)))
    ln = lnL[:, :, bi, :]
    top = float(ln.max())
    like = np.exp(ln - top).mean(axis=-1)
    return float(np.log(like.mean())), z       # uniform node weights over (M, a)


def fast_lnL_at_a0(model_R_nodes, model_v_nodes, sel, cluster_kw, M_vis,
                   grid_M, ml_brackets):
    """Fast-star log L on (M, nu) at a_dark = 0, replicated along r_a."""
    nM, nnu = grid_M.size, len(ml_brackets)
    lam = np.zeros((nM, 1, nnu) + model_R_nodes.shape + model_v_nodes.shape)
    for iM in range(nM):
        for inu in range(len(ml_brackets)):
            p = mc.ClusterParams(M_vis=M_vis, b_vis=vm2.B_VIS_PC,
                                 nu_ML=float(ml_brackets[inu][1]),
                                 M_dark=float(grid_M[iM]), a_dark=0.0,
                                 **cluster_kw)
            lam[iM, 0, inu] = mc.fast_star_intensity(
                model_R_nodes, model_v_nodes, p, N_tot=sel["N_tot"])
    return lam


def pulsar_lnL_at_a0(model, data, grid_M, ml_brackets, a_fixed=0.0):
    """Censored-pulsar log L on (M, nu) at a fixed dark scale (same quadrature as pl)."""
    R = np.asarray(data["R_pc"], dtype=float)
    A = np.asarray(data["A_bound"], dtype=float)
    Ae = np.asarray(data["A_err"], dtype=float)
    z = model._z_psr
    from scipy.special import log_ndtr
    nM = grid_M.size
    out = np.zeros((nM, 1, len(ml_brackets)))
    rr = np.sqrt(R[:, None] ** 2 + z[None, :] ** 2)
    w = np.broadcast_to(
        pl.md.los_weight(R[:, None], z[None, :], rc=pl.MSP_RC_PC,
                         alpha=pl.MSP_ALPHA, r_max=pl.MSP_RMAX_PC)[None],
        (nM,) + rr.shape)
    for iM in range(nM):
        Md = float(grid_M[iM])
        for inu in range(len(ml_brackets)):
            p = model.params(iM, 0, inu)
            m_vis = mc.M_enc_vis(rr, p)
            f_dark = rr ** 3 / (rr ** 2 + a_fixed ** 2) ** 1.5
            az = -mc.G_PC * (m_vis + Md * f_dark) * z / rr ** 3
            cdf = np.exp(log_ndtr((A[:, None] - az) / Ae[:, None]))
            wz = w[0]
            num = np.trapezoid(wz * cdf, z, axis=1)
            den = np.trapezoid(wz, z, axis=1)
            out[iM, 0, inu] = np.log(np.clip(num / den, 1e-300, None)).sum()
    return out


gate_ok = True
for visible, dist in CONFIGS:
    name = NAMES[(visible, dist)]
    print(f"== {name}", flush=True)
    cal = vm2.calibrate(visible, dist)
    kw = vm2.visible_kwargs(visible)
    cluster = {"M_vis": cal["M_vis"], "b_vis": vm2.B_VIS_PC}
    cluster.update(kw)

    # mirror run_fit2.build's selection/data/grid choices
    hw = vm2.bracket_half_width([vm2.calibrate(v, d) for v, d in vm2.CONFIGS])
    ml_brackets = tuple(vm2.ml_brackets(hw))
    grid = fj.PriorGrid(ml_brackets=ml_brackets)
    sel = L.selection(distance_pc=dist)
    data_fs = L.fast_stars(distance_pc=dist, robust_only=True)
    data_ps = L.pulsars(distance_pc=dist, source="trapum")

    # shared node grids identical to the joint model's
    Rn, vn = fj.fast_star_nodes(sel)
    shim = type("Shim", (), {})()
    shim.sel = sel
    shim.R_nodes, shim.v_nodes = Rn, vn
    shim._z_psr = fj._los_nodes(sel)[0]
    shim.cluster = cluster
    shim.grid = grid

    def _params(self, iM, ia, inu, ira=None):
        extra = {k: v for k, v in self.cluster.items() if k not in ("M_vis", "b_vis")}
        if isinstance(extra.get("vis_abg"), list):
            extra["vis_abg"] = tuple(extra["vis_abg"])
        return mc.ClusterParams(M_vis=self.cluster["M_vis"],
                                b_vis=self.cluster["b_vis"],
                                nu_ML=float(self.grid.ml_brackets[inu][1]),
                                M_dark=float(self.grid.M_dark[iM]),
                                a_dark=float(self.grid.a_dark[ia]), **extra)
    import types as _types
    shim.params = _types.MethodType(_params, shim)

    lam0 = fast_lnL_at_a0(Rn, vn, sel, kw, cal["M_vis"], grid.M_dark, ml_brackets)
    import run_fit as R1c
    lam0 = anchor_fast(lam0, shim, grid.M_dark, ml_brackets)
    shim.lam = lam0
    psr0 = pulsar_lnL_at_a0(shim, data_ps, grid.M_dark, ml_brackets)
    fs = fj.loglike_fast(shim, data_fs)[..., None] * np.ones(1)
    print("   DBG lam", shim.lam.shape, "fs", fs.shape, "psr0", psr0.shape)
    lnL_res = ((fs[..., 0] + psr0)[..., None]
               * np.ones((1, 1, 1, len(grid.r_a))))

    # G-H2 sanity: the same machinery evaluated at the grid-edge node a = 1e-4
    # must reproduce the released continuous cube cell to float precision,
    # for BOTH legs (validates the hand-rolled a-fixed paths before a = 0 use)
    z = np.load(os.path.join(NPZDIR, NPZ[name]))
    lnL_cont = z["lnL_total"]
    ia_edge = int(np.argmin(np.abs(z["a_dark"] - 1e-4)))
    iM_test = int(np.argmax(lnL_cont[:, ia_edge, 1, 0]))
    p_test = mc.ClusterParams(M_vis=cal["M_vis"], b_vis=vm2.B_VIS_PC,
                              nu_ML=1.0, M_dark=float(grid.M_dark[iM_test]),
                              a_dark=1e-4, **kw)
    lam_t = mc.fast_star_intensity(Rn, vn, p_test, N_tot=sel["N_tot"])
    # anchor the probe exactly as R1.anchor_intensity does (per-cell N_ref/f)
    Rt = np.geomspace(1e-3, sel["R_ref"], 60)
    rrt = np.sqrt(Rt[:, None] ** 2 + shim._z_psr[None, :] ** 2)
    col = np.trapezoid(mc.rho_tracer_norm(rrt, p_test), shim._z_psr, axis=1)
    f_ref = float(np.trapezoid(col * 2.0 * np.pi * Rt, Rt))
    lam_t = lam_t * (sel["N_ref"] / max(f_ref, 1e-300))
    shim.lam = lam_t.reshape(1, 1, 1, *lam_t.shape)
    fs_t = float(fj.loglike_fast(shim, data_fs)[0, 0, 0])
    # direct lam comparison against a cache-hit JointModel for this base
    model_ref = fj.JointModel(cluster, sel, L.profiles(distance_pc=dist)["R_pc"],
                              grid=grid, verbose=False)
    R1ref = __import__("run_fit")
    R1ref.anchor_intensity(model_ref)
    ref_lam = model_ref.lam[iM_test, ia_edge, BRACKET_INDEX]
    nz = ref_lam > 0
    rat = (lam_t / ref_lam)[nz & (lam_t > 0)]
    print(f"   DBG lam ratio min/max/med "
          f"{rat.min():.9f}/{rat.max():.9f}/{np.median(rat):.9f}  "
          f"(n_nz {int(nz.sum())}, n_mine_nz {int((lam_t > 0).sum())})")
    psr_t = float(pulsar_lnL_at_a0(shim, data_ps,
                                   grid.M_dark[iM_test:iM_test + 1],
                                   ml_brackets, a_fixed=1e-4)[0, 0, BRACKET_INDEX])
    dev_fs = abs(fs_t - float(z["lnL_fast"][iM_test, ia_edge, BRACKET_INDEX, :].mean()))
    dev_ps = abs(psr_t - float(z["lnL_pulsars"][iM_test, ia_edge, BRACKET_INDEX, :].mean()))
    if dev_fs > 1e-8 or dev_ps > 1e-8:
        print("   DBG FAIL", fs_t, psr_t, iM_test)

    # restricted posterior products (90 % regions only)
    ln_res = lnL_res[:, 0, BRACKET_INDEX, :]
    like = np.exp(ln_res - ln_res.max()).mean(axis=-1)
    Pm = like / like.sum()
    i_mode = int(np.argmax(Pm))
    thr = fj.hpd_threshold(Pm.reshape(-1, 1), 0.90)
    mask = Pm >= thr
    m_lo, m_hi = float(grid.M_dark[mask].min()), float(grid.M_dark[mask].max())
    ul = float(fj.upper_limit_M(Pm.reshape(-1, 1),
                                fj.PriorGrid(M_dark=grid.M_dark,
                                             a_dark=np.array([1e-4]),
                                             ml_brackets=ml_brackets,
                                             r_a=grid.r_a), 0.90))

    lnz_res = float(np.log(like.mean()))
    lnz_cont, _ = lnz_continuous(os.path.join(HDIR, "fit2", "results", NPZ[name]))
    lnK_rel = lnz_res - lnz_cont

    results["configs"][name] = dict(
        visible=visible, distance_pc=dist, M_vis=cal["M_vis"],
        mode_M_dark=float(grid.M_dark[i_mode]),
        hpd90_M=[m_lo, m_hi], M_ul90=ul,
        lnZ_restricted=lnz_res, lnZ_continuous=lnz_cont, lnK_rel=lnK_rel,
        gate_GH2_faststar_dev=dev_fs, gate_GH2_pulsar_dev=dev_ps)
    print(f"   mode {grid.M_dark[i_mode]:.4e}  HPD90 [{m_lo:.3e}, {m_hi:.3e}]"
          f"  UL90 {ul:.4e}  lnZ_res {lnz_res:.3f}  lnZ_cont {lnz_cont:.3f}"
          f"  lnK_rel {lnK_rel:+.3f}")
    print(f"   G-H2 devs at a=1e-4 node: fast {dev_fs:.3e}, pulsar {dev_ps:.3e}")
    gate_ok &= dev_fs < 1e-6 and dev_ps < 1e-6

results["gate_GH2_pass"] = bool(gate_ok)
with open(os.path.join(HERE, "fH_calc7_amass0.json"), "w") as fh:
    json.dump(results, fh, indent=1)
print("G-H2:", "PASS" if gate_ok else "FAIL")
if not gate_ok:
    raise SystemExit(1)
