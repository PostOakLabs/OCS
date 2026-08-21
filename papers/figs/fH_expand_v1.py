"""Paper H v1.2 expansion figures (WU OCS-H-EXPAND-1, referee items H-1..H-6).

Nothing here changes any v1.1 number.  Every panel is a picture of a quantity that
already exists in a frozen result file: the four verdict cubes under the post-FLAGD
reconciled MSP kernel (paper/h/flagd/results/fit2_msp/), the sixteen-configuration
ln K record in the same directory's fit2_results.json, the frozen data extractions
(paper/h/data/), the G2 jerk validation (paper/h/jerk/), the FLAG D jerk floors
(paper/h/flagd/results/jerk_deltas.json) and the G3 buildability map (paper/h/g3/).

The script recomputes, rather than transcribes, the quantities it draws that also
appear in a published table, and asserts each against the record before any figure
is written:

  * the four HPD90 and profile-likelihood-90 regions, against FIT3_REPORT Sec. 3.1;
  * the sixteen fiducial-bracket ln K values, against fit2_results.json;
  * the per-pulsar model acceleration envelope, against the record cell's own
    ppc_accel_extrema block;
  * the closed-form xi against the stored quadrature value in g2_results.json;
  * the G3 verdict tally against g3_map.json.

EMBARGO (binding, OCS-H-EXPAND-1 brief).  Fiducial M/L bracket only; 90 per cent is
the only level computed anywhere; no pessimistic-bracket number is read, written or
plotted; no all-legs HPD region is drawn; no compact-versus-extended statement is
sourced to the profile leg.  The ln K ladder plots the profile-leg configurations as
what the paper already calls them, an error-model sensitivity ladder, and the verdict
rows are labelled as the verdict rows.

Outputs (all written next to this script):
  fH_posterior_plane.png / .json   H-1  2x2 posterior plane, HPD90 + PL90
  fH_lnk_ladder.png / .json        H-2  sixteen-configuration ln K ladder
  fH_fast_stars.png / .json        H-3  fast stars against escape-velocity curves
  fH_pulsar_bounds.png / .json     H-4  one-sided pulsar bounds and model envelopes
  fH_jerk_dist.png / .json         H-5  1-stable jerk density, both xi floors
  fH_g3_overlay.png / .json        H-6  G3 buildability map under the HPD90 regions

Run:  python fH_expand_v1.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors                             # noqa: E402
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.lines import Line2D                  # noqa: E402
from matplotlib.patches import Patch, Rectangle      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HDIR = os.path.abspath(os.path.join(HERE, "..", "h"))
for _p in ("mock", "fit", "fit2", "flagd", "jerk"):
    _q = os.path.join(HDIR, _p)
    if _q not in sys.path:
        sys.path.insert(0, _q)

import fit_joint as fj            # noqa: E402
import mock_cluster as mc         # noqa: E402
import load_data as L             # noqa: E402
import jerk_dist as jd            # noqa: E402

MSP = os.path.join(HDIR, "flagd", "results", "fit2_msp")
FIT2_RESULTS = os.path.join(MSP, "fit2_results.json")
G3_MAP = os.path.join(HDIR, "g3", "g3_map.json")
G2_RESULTS = os.path.join(HDIR, "jerk", "g2_results.json")
JERK_DELTAS = os.path.join(HDIR, "flagd", "results", "jerk_deltas.json")

LEVEL = 0.90                                  # the only level, per the embargo package
CHI2_2_90 = float(stats.chi2.ppf(0.90, 2))
FID = 1                                       # fiducial M/L bracket index
COMPACT_MAX = 0.01                            # pc, pre-registered
EXTENDED_MIN = 0.10

VERDICT = ["nolegprof_plummer_5200", "nolegprof_plummer_5494",
           "nolegprof_abg_5200", "nolegprof_abg_5494"]
VERDICT_TITLE = {"nolegprof_plummer_5200": "Plummer, 5.20 kpc",
                 "nolegprof_plummer_5494": "Plummer, 5.49 kpc",
                 "nolegprof_abg_5200": r"BH25 $\alpha\beta\gamma$, 5.20 kpc",
                 "nolegprof_abg_5494": r"BH25 $\alpha\beta\gamma$, 5.49 kpc"}
PRIMARY = "nolegprof_plummer_5494"            # the paper's single-configuration default

# FIT3_REPORT Sec. 3.1, fiducial bracket, full prior range.  Regions are recomputed
# from the cubes below and compared against these to four significant figures.
FIT3_TABLE = {
    "nolegprof_plummer_5200": dict(hpd=(1.778e4, 2.512e4, 0.01228),
                                   pl=(1.778e4, 2.818e4, 0.01732)),
    "nolegprof_plummer_5494": dict(hpd=(2.239e4, 2.818e4, 0.01732),
                                   pl=(1.995e4, 3.162e4, 0.01732)),
    "nolegprof_abg_5200": dict(hpd=(1.778e4, 2.239e4, 0.01228),
                               pl=(1.585e4, 2.512e4, 0.01732)),
    "nolegprof_abg_5494": dict(hpd=(1.995e4, 2.512e4, 0.008711),
                               pl=(1.995e4, 2.818e4, 0.01732)),
}

STYLE = {"font.size": 9.0, "font.family": "serif", "axes.grid": True,
         "grid.alpha": 0.22, "savefig.dpi": 300, "savefig.bbox": "tight",
         "axes.axisbelow": True}
plt.rcParams.update(STYLE)

C_HPD = "#1a4f8f"
C_PL = "#c25a00"
C_COMPACT = "#1a4f8f"
C_EXTENDED = "#8c1d40"
C_VIS = "#555555"


def _w(name, obj):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)


def _close(a, b, rtol=2e-3):
    return abs(float(a) - float(b)) <= rtol * abs(float(b))


def log_edges(x):
    """Cell edges of a log-spaced node array, for an exact pcolormesh."""
    lx = np.log(np.asarray(x, dtype=float))
    mid = 0.5 * (lx[1:] + lx[:-1])
    return np.exp(np.concatenate([[lx[0] - (mid[0] - lx[0])], mid,
                                  [lx[-1] + (lx[-1] - mid[-1])]]))


# ---------------------------------------------------------------------------
# the record, reproduced and asserted
# ---------------------------------------------------------------------------


def load_cube(label):
    d = np.load(os.path.join(MSP, "posterior_%s.npz" % label))
    lnL = d["lnL_total"]
    resid = float(np.abs(lnL - (d["lnL_fast"] + d["lnL_pulsars"])).max())
    if resid != 0.0:
        raise SystemExit("%s: stored total is not leg-dropped (resid %.3e)"
                         % (label, resid))
    grid = fj.PriorGrid(M_dark=d["M_dark"], a_dark=d["a_dark"],
                        ml_brackets=(("pessimistic", float(d["ml"][0])),
                                     ("fiducial", float(d["ml"][1])),
                                     ("optimistic", float(d["ml"][2]))),
                        r_a=tuple(float(x) for x in d["r_a"]))
    return d, lnL, grid


def regions(label):
    """HPD90 and profile-likelihood-90 masks at the fiducial bracket."""
    d, lnL, grid = load_cube(label)
    P = fj.posterior(lnL, grid, bracket=FID)
    hpd = fj.hpd_mask(P, LEVEL)
    prof = lnL[:, :, FID, :].max(axis=-1)
    pl = (2.0 * (prof.max() - prof)) <= CHI2_2_90
    iM, ia = np.unravel_index(int(np.argmax(P)), P.shape)
    return dict(M=grid.M_dark, a=grid.a_dark, P=P, hpd=hpd, pl=pl,
                map_M=float(grid.M_dark[iM]), map_a=float(grid.a_dark[ia]))


def check_regions(reg):
    """Assert every drawn region against FIT3_REPORT Sec. 3.1 before plotting."""
    out = {}
    for lab, r in reg.items():
        row = {}
        for key, mask in (("hpd", r["hpd"]), ("pl", r["pl"])):
            iM, ia = np.where(mask)
            got = (float(r["M"][iM.min()]), float(r["M"][iM.max()]),
                   float(r["a"][ia.max()]))
            want = FIT3_TABLE[lab][key]
            for g, wv in zip(got, want):
                if not _close(g, wv):
                    raise SystemExit("%s/%s: %.6g against recorded %.6g"
                                     % (lab, key, g, wv))
            row[key] = dict(M_lo=got[0], M_hi=got[1], a_hi=got[2],
                            n_cells=int(mask.sum()), n_grid=int(mask.size),
                            touches_a_lo=bool(ia.min() == 0),
                            extended_cells=int((mask
                                                & (r["a"] > EXTENDED_MIN)[None, :]).sum()))
        row["map_M_dark"] = r["map_M"]
        row["map_a_dark"] = r["map_a"]
        out[lab] = row
    return out


def lnk_ladder_rows():
    """The sixteen-configuration ln K record, fiducial bracket only."""
    res = json.load(open(FIT2_RESULTS, encoding="utf-8"))
    rows = []
    for lab, c in res["configs"].items():
        cells = [x for x in c["cells"] if x["bracket"] == "fiducial"
                 and x["lnK_compact_extended"] is not None]
        full = [x for x in cells if x["M_range"].startswith("full")
                and x["a_range"].startswith("full")]
        if len(full) != 1:
            raise SystemExit("%s: %d full-range fiducial cells" % (lab, len(full)))
        vals = [x["lnK_compact_extended"] for x in cells]
        cfg = c["config"]
        rows.append(dict(label=lab, visible=cfg["visible"], distance=cfg["distance"],
                         tau=cfg["tau"], use_profile=bool(cfg["use_profile"]),
                         note=cfg["note"], n_cells=len(vals),
                         lnK_full=float(full[0]["lnK_compact_extended"]),
                         lnK_min=float(min(vals)), lnK_max=float(max(vals)),
                         minority_sign=bool(min(vals) < 0.0)))
    if len(rows) != 16:
        raise SystemExit("expected 16 configurations, found %d" % len(rows))
    scheme_order = {"nolegprof": 0, "a2": 1, "tau2.0": 2, "tau0.5": 3}

    def key(r):
        s = ("nolegprof" if not r["use_profile"]
             else ("a2" if r["tau"] == 1.0 else "tau%.1f" % r["tau"]))
        return (scheme_order[s], r["visible"], r["distance"])
    rows.sort(key=key)
    return rows


def cluster_params(label, M_dark, a_dark):
    """ClusterParams for one recorded configuration at the fiducial bracket."""
    res = json.load(open(FIT2_RESULTS, encoding="utf-8"))
    c = res["configs"][label]
    kw = {}
    if c["config"]["visible"] == "abg":
        bp = L.bh25_profile_params()
        kw["vis_abg"] = (bp["alpha"], bp["beta"], bp["gamma"], bp["r_c_pc"])
    return mc.ClusterParams(M_vis=c["meta"]["M_vis"], b_vis=c["meta"]["b_vis_pc"],
                            nu_ML=1.0, M_dark=M_dark, a_dark=a_dark, **kw), c


def los_nodes():
    """The line-of-sight quadrature nodes fit_joint uses for the pulsar leg."""
    half = np.geomspace(1e-3, 40.0, 241 // 2)
    return np.concatenate([-half[::-1], [0.0], half])


def accel_envelope(p, R):
    """max |a_LOS| the model can reach at each projected radius, (km/s)^2/pc."""
    z = los_nodes()
    rr = np.sqrt(np.asarray(R, dtype=float)[:, None] ** 2 + z[None, :] ** 2)
    az = -mc.G_PC * mc.M_enc(rr, p) * z[None, :] / rr ** 3
    return np.abs(az).max(axis=1)


# ---------------------------------------------------------------------------
# H-1 / H-6 : the posterior plane, and the formation map under it
# ---------------------------------------------------------------------------


def panel_plane(ax, r, title, edge_label=True):
    Me, ae = log_edges(r["M"]), log_edges(r["a"])
    ax.pcolormesh(Me, ae, np.where(r["pl"].T, 1.0, np.nan),
                  cmap=matplotlib.colors.ListedColormap([C_PL]), alpha=0.55,
                  shading="flat")
    ax.pcolormesh(Me, ae, np.where(r["hpd"].T, 1.0, np.nan),
                  cmap=matplotlib.colors.ListedColormap([C_HPD]), alpha=0.95,
                  shading="flat")
    ax.axhline(COMPACT_MAX, color="black", lw=0.7, ls=":")
    ax.axhline(EXTENDED_MIN, color="black", lw=0.7, ls="--")
    ax.plot([r["map_M"]], [r["map_a"]], marker="x", ms=6, mew=1.4, color="black",
            zorder=6, clip_on=False)
    ax.axhspan(ae[0], r["a"][0], color="black", alpha=0.30, lw=0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(Me[0], Me[-1])
    ax.set_ylim(ae[0], ae[-1])
    ax.set_title(title, fontsize=9.0)
    if edge_label:
        ax.text(1.4e3, 1.8e-4, "grid edge: point-mass limit", fontsize=6.4,
                va="bottom", ha="left")
        ax.text(1.4e3, 0.011, "compact bound", fontsize=6.4, va="bottom", ha="left")
        ax.text(1.4e3, 0.11, "extended bound", fontsize=6.4, va="bottom", ha="left")


def fig_posterior_plane(reg):
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.6), sharex=True, sharey=True)
    for ax, lab in zip(axes.ravel(), VERDICT):
        panel_plane(ax, reg[lab], VERDICT_TITLE[lab], edge_label=(lab == VERDICT[0]))
    for ax in axes[1]:
        ax.set_xlabel(r"$M_{\mathrm{dark}}$  [$M_\odot$]")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$a$  [pc]")
    handles = [Patch(facecolor=C_HPD, alpha=0.9, label="90% HPD region (primary)"),
               Patch(facecolor=C_PL, alpha=0.55,
                     label="90% profile-L region (secondary)"),
               Line2D([], [], color="black", marker="x", ls="none", label="MAP"),
               Line2D([], [], color="black", ls=":", label=r"$a = 0.01$ pc"),
               Line2D([], [], color="black", ls="--", label=r"$a = 0.1$ pc")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               fontsize=7.6, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fH_posterior_plane.png"))
    plt.close(fig)


def fig_g3_overlay(reg, g3):
    order = ["BUILDABLE_PESSIMISTIC", "BUILDABLE_OPTIMISTIC", "NOT_BUILDABLE",
             "LITERATURE_SILENT"]
    shade = {"BUILDABLE_PESSIMISTIC": "#cfe3cf", "BUILDABLE_OPTIMISTIC": "#f2e2b6",
             "NOT_BUILDABLE": "#e6c7c7", "LITERATURE_SILENT": "#e9e9e9"}
    text = {"BUILDABLE_PESSIMISTIC": "buildable under pessimistic retention",
            "BUILDABLE_OPTIMISTIC": "buildable only at the optimistic edge",
            "NOT_BUILDABLE": "not buildable", "LITERATURE_SILENT": "literature silent"}
    gm = np.array(sorted({c["log10_M_dark"] for c in g3["cells"]}))
    ga = np.array(sorted({c["log10_a_pc"] for c in g3["cells"]}))
    idx = {v: i for i, v in enumerate(order)}
    Z = np.full((ga.size, gm.size), np.nan)
    for c in g3["cells"]:
        Z[int(np.argmin(abs(ga - c["log10_a_pc"]))),
          int(np.argmin(abs(gm - c["log10_M_dark"])))] = idx[c["verdict"]]

    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    ax.pcolormesh(log_edges(10.0 ** gm), log_edges(10.0 ** ga), Z,
                  cmap=matplotlib.colors.ListedColormap([shade[k] for k in order]),
                  vmin=-0.5, vmax=3.5, shading="flat")
    for lab, ls in zip(VERDICT, ["-", "-", "--", "--"]):
        r = reg[lab]
        ax.contour(r["M"], r["a"], r["hpd"].T.astype(float), levels=[0.5],
                   colors=[C_HPD], linewidths=1.4, linestyles=[ls])
    bh = g3["regions"]["BH25_favoured"]["definition"]
    ax.add_patch(Rectangle((bh["m_range"][0], bh["a_range"][0]),
                           bh["m_range"][1] - bh["m_range"][0],
                           bh["a_range"][1] - bh["a_range"][0],
                           fill=False, edgecolor=C_EXTENDED, lw=1.6))
    ax.annotate("BH25-favoured region", xy=(bh["m_range"][0], bh["a_range"][1]),
                xytext=(2.2e4, 2.6), fontsize=7.4, color=C_EXTENDED,
                arrowprops=dict(arrowstyle="->", color=C_EXTENDED, lw=1.0))
    ax.annotate("90% HPD regions,\nfit of record", xy=(2.3e4, 1.4e-3),
                xytext=(7.0e4, 5e-4), fontsize=7.4, color=C_HPD,
                arrowprops=dict(arrowstyle="->", color=C_HPD, lw=1.0))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$M_{\mathrm{dark}}$  [$M_\odot$]")
    ax.set_ylabel(r"$a$  [pc]")
    ax.legend(handles=[Patch(facecolor=shade[k], edgecolor="#999999", label=text[k])
                       for k in order],
              loc="upper left", fontsize=7.0, framealpha=0.92)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fH_g3_overlay.png"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# H-2 : the ln K ladder
# ---------------------------------------------------------------------------


def fig_lnk_ladder(rows):
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    y = np.arange(len(rows))[::-1]
    for yi, r in zip(y, rows):
        col = C_EXTENDED if r["minority_sign"] else C_COMPACT
        ax.plot([r["lnK_min"], r["lnK_max"]], [yi, yi], color=col, lw=1.5,
                solid_capstyle="butt", alpha=0.85)
        ax.plot([r["lnK_min"], r["lnK_max"]], [yi, yi], marker="|", ls="none",
                color=col, ms=7, mew=1.3)
        ax.plot([r["lnK_full"]], [yi], marker="o", ms=4.6, color=col,
                markeredgecolor="white", mew=0.6, zorder=5)
        if not r["use_profile"]:
            ax.axhspan(yi - 0.5, yi + 0.5, color=C_COMPACT, alpha=0.07, lw=0)
    ax.axvline(0.0, color="black", lw=0.9)
    labels = []
    for r in rows:
        scheme = ("profile leg dropped" if not r["use_profile"]
                  else "A2 discrepancy" if r["tau"] == 1.0
                  else "A2, knot prior %s" % ("doubled" if r["tau"] > 1.0 else "halved"))
        vis = "Plummer" if r["visible"] == "plummer" else r"BH25 $\alpha\beta\gamma$"
        labels.append("%s, %s, %.2f kpc" % (scheme, vis, r["distance"] / 1e3))
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.4)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel(r"$\ln K$ (compact : extended), fiducial M/L bracket")
    ax.set_xlim(-8.0, 14.0)
    handles = [Line2D([], [], color=C_COMPACT, marker="o", lw=1.5,
                      label="compact preferred in all eight prior cells"),
               Line2D([], [], color=C_EXTENDED, marker="o", lw=1.5,
                      label="sign flipped: extended preferred"),
               Patch(facecolor=C_COMPACT, alpha=0.07,
                     label="fit of record (verdict rows)")]
    ax.legend(handles=handles, loc="upper left", fontsize=7.2, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fH_lnk_ladder.png"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# H-3 : the fast-star leg
# ---------------------------------------------------------------------------


def fast_star_table(distance_pc):
    d = L.load_json("fast_stars.json")
    out = []
    for s in d["fast_stars"]:
        mu = s["pm_total_masyr"]["value"]
        mu_e = s["pm_total_masyr"]["uncertainty"]
        out.append(dict(id=s["id"], robust=bool(s["robust"]),
                        theta_arcsec=s["r_proj_arcsec"]["value"],
                        R_pc=s["r_proj_arcsec"]["value"] / L.ARCSEC_PER_RAD * distance_pc,
                        v_pm=L.KMS_PER_MASYR_KPC * mu * distance_pc / 1e3,
                        v_pm_err=L.KMS_PER_MASYR_KPC * mu_e * distance_pc / 1e3))
    return out


STAR_LABEL_OFFSET = {"A": (6, 3), "B": (-11, -4), "C": (5, 4), "D": (5, -10),
                     "E": (6, 2), "F": (-3, 8), "G": (6, -9)}


def fig_fast_stars(stars, curves, v_thresh, r_search_pc):
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    r = np.array(curves["R_pc"])
    ax.plot(r, curves["visible"], color=C_VIS, lw=1.3, ls=":",
            label="visible mass only")
    ax.plot(r, curves["extended"], color=C_EXTENDED, lw=1.5, ls="--",
            label=curves["extended_label"])
    ax.plot(r, curves["compact"], color=C_COMPACT, lw=1.7,
            label=curves["compact_label"])
    ax.axvline(r_search_pc, color="black", lw=0.8, ls="-.")
    ax.text(r_search_pc * 1.10, 112.0, r"$3''$ search radius", fontsize=7.0,
            rotation=90, ha="left", va="bottom")
    ax.axhline(v_thresh, color="black", lw=0.8, ls=(0, (4, 3)))
    ax.text(0.95, v_thresh * 0.97, "selection threshold, 2.41 mas/yr", fontsize=7.0,
            ha="right", va="top")
    for s in stars:
        ax.errorbar([s["R_pc"]], [s["v_pm"]], yerr=[s["v_pm_err"]],
                    marker="o" if s["robust"] else "s",
                    mfc="black" if s["robust"] else "white",
                    color="black", ms=5.2, ls="none", elinewidth=0.9, capsize=2,
                    zorder=6)
        ax.annotate(s["id"], (s["R_pc"], s["v_pm"]), textcoords="offset points",
                    xytext=STAR_LABEL_OFFSET.get(s["id"], (5, 4)), fontsize=7.4,
                    zorder=7)
    ax.set_xscale("log")
    ax.set_xlim(4.0e-3, 1.0)
    ax.set_ylim(50.0, 340.0)
    ax.set_xlabel(r"projected radius $R$  [pc]")
    ax.set_ylabel(r"speed and $v_{\mathrm{esc}}$  [km s$^{-1}$]")
    sec = ax.secondary_xaxis("top", functions=(
        lambda x: x / curves["distance_pc"] * L.ARCSEC_PER_RAD,
        lambda t: t / L.ARCSEC_PER_RAD * curves["distance_pc"]))
    sec.set_xlabel(r"projected radius  [arcsec]", fontsize=8.5)
    handles, _ = ax.get_legend_handles_labels()
    handles += [Line2D([], [], color="black", marker="o", ls="none",
                       label="robust (five, in the likelihood)"),
                Line2D([], [], color="black", marker="s", mfc="white", ls="none",
                       label="candidate (sensitivity row)")]
    ax.legend(handles=handles, loc="upper right", fontsize=7.2, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fH_fast_stars.png"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# H-4 : the pulsar leg
# ---------------------------------------------------------------------------


PSR_LABEL_OFFSET = {"A": (7, -2), "B": (7, 4), "D": (7, 4), "E": (-11, 3),
                    "G": (0, 9), "H": (6, 5), "K": (7, 3)}


def fig_pulsar_bounds(psr, env):
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    r = np.array(env["R_pc"])
    for key, col, ls, lab in (("compact", C_COMPACT, "-", env["compact_label"]),
                              ("extended", C_EXTENDED, "--", env["extended_label"])):
        e = np.array(env[key])
        ax.fill_between(r, -e, e, color=col, alpha=0.13, lw=0)
        ax.plot(r, e, color=col, lw=1.5, ls=ls, label=lab)
        ax.plot(r, -e, color=col, lw=1.5, ls=ls)
    ax.axhline(0.0, color="black", lw=0.7)
    for name, R, A, Ae in zip(psr["names"], psr["R_pc"], psr["A_bound"], psr["A_err"]):
        ax.errorbar([R], [A], yerr=[Ae], marker="_", ms=11, mew=1.6, color="black",
                    ls="none", elinewidth=0.9, capsize=2, zorder=6)
        ax.annotate("", xy=(R, A - 30.0), xytext=(R, A),
                    arrowprops=dict(arrowstyle="->", color="black", lw=0.9))
        ax.annotate(name, (R, A), textcoords="offset points",
                    xytext=PSR_LABEL_OFFSET.get(name, (6, 5)), fontsize=7.4)
    ax.set_xscale("log")
    ax.set_xlabel(r"projected radius $R$  [pc]")
    ax.set_ylim(-330.0, 330.0)
    ax.set_ylabel(r"$a_{\mathrm{LOS}}$  [(km s$^{-1}$)$^2$ pc$^{-1}$]")
    sec = ax.secondary_yaxis("right", functions=(lambda y: y * L.ACC_UNIT * 1e9,
                                                 lambda y: y / (L.ACC_UNIT * 1e9)))
    sec.set_ylabel(r"$10^{-9}$ m s$^{-2}$", fontsize=8.5)
    handles, _ = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], color="black", marker="_", ls="none",
                          label=r"TRAPUM one-sided bound, $a_{\mathrm{LOS}} \leq A$"))
    ax.legend(handles=handles, loc="lower right", fontsize=7.2, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fH_pulsar_bounds.png"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# H-5 : the jerk density and the two xi floors
# ---------------------------------------------------------------------------


def fig_jerk_dist(block, xi_exact, xi_pub):
    rows = block["rows"]
    a0 = float(np.median([r["a0_floor"] for r in rows]))
    a0_pub = a0 * xi_pub / xi_exact
    x = np.geomspace(1e-23, 1e-18, 900)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.8, 3.0),
                                 gridspec_kw=dict(width_ratios=[1.8, 1.0]))
    for axis in (ax, bx):
        axis.plot(x, 2.0 * jd.pdf_jerk_los(x, a0) * x * np.log(10.0),
                  color=C_COMPACT, lw=1.6, label=r"corrected $\xi = 3.4596$")
        axis.plot(x, 2.0 * jd.pdf_jerk_los(x, a0_pub) * x * np.log(10.0),
                  color=C_EXTENDED, lw=1.4, ls="--", label=r"published $\xi = 3.04$")
        axis.axvline(a0, color=C_COMPACT, lw=0.9, ls=":")
        axis.axvline(a0_pub, color=C_EXTENDED, lw=0.9, ls=":")
        axis.set_xscale("log")
        axis.set_xlabel(r"$|\dot{a}_{\mathrm{LOS}}|$  [m s$^{-3}$]")
    ax.annotate(r"floors $\dot{a}_{0}$", xy=(a0, 0.74), xytext=(4.0e-21, 0.90),
                fontsize=7.2, arrowprops=dict(arrowstyle="->", lw=0.8))
    for r in rows:
        ax.plot([abs(r["jerk"])], [0.02], marker="|", ms=10, mew=1.2, color="black",
                clip_on=False)
    ax.text(4.0e-20, 0.26, "measured $|\\ddot{\\nu}|$ jerks,\neight TRAPUM pulsars",
            fontsize=7.0, ha="center")
    ax.set_xlim(1e-23, 1e-18)
    ax.set_ylim(0.0, 1.02)
    ax.set_ylabel("probability per decade")
    ax.legend(loc="upper left", fontsize=7.2, framealpha=0.95)
    bx.set_xscale("linear")
    bx.set_xlim(3.0e-22, 7.0e-22)
    bx.set_xticks([3e-22, 4e-22, 5e-22, 6e-22, 7e-22])
    bx.set_xticklabels(["3", "4", "5", "6", "7"])
    bx.set_xlabel(r"$|\dot{a}_{\mathrm{LOS}}|$  [$10^{-22}$ m s$^{-3}$]")
    bx.set_ylim(0.60, 0.78)
    bx.set_title("the two floors, 13.8 per cent apart", fontsize=7.6)
    bx.text(a0_pub * 0.985, 0.615, "3.04", fontsize=7.0, color=C_EXTENDED,
            ha="right", va="bottom")
    bx.text(a0 * 1.015, 0.615, "3.4596", fontsize=7.0, color=C_COMPACT,
            ha="left", va="bottom")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fH_jerk_dist.png"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    checks = []

    # --- H-1 and H-6 -------------------------------------------------------
    reg = {lab: regions(lab) for lab in VERDICT}
    region_record = check_regions(reg)
    checks.append("four HPD90 and profile-L90 regions reproduce FIT3_REPORT Sec. 3.1")
    for lab, row in region_record.items():
        if row["hpd"]["extended_cells"] or row["pl"]["extended_cells"]:
            raise SystemExit("%s: a region reaches the extended zone" % lab)
        if not row["hpd"]["touches_a_lo"]:
            raise SystemExit("%s: HPD region does not abut the grid edge" % lab)
    checks.append("no region contains an extended cell; all abut the a grid edge")

    fig_posterior_plane(reg)
    _w("fH_posterior_plane.json",
       dict(item="H-1", level=LEVEL, bracket="fiducial",
            source=dict(cubes="paper/h/flagd/results/fit2_msp/",
                        table="paper/h/fit3/FIT3_REPORT.md Sec. 3.1"),
            estimators=dict(primary="90 per cent HPD, r_a marginalised",
                            secondary="90 per cent profile likelihood, r_a profiled, "
                                      "chi2_2(0.90) = %.6f" % CHI2_2_90),
            configurations=region_record))

    g3 = json.load(open(G3_MAP, encoding="utf-8"))
    tally = {}
    for c in g3["cells"]:
        tally[c["verdict"]] = tally.get(c["verdict"], 0) + 1
    if tally != g3["verdict_counts"]:
        raise SystemExit("G3 tally %s against recorded %s"
                         % (tally, g3["verdict_counts"]))
    checks.append("G3 verdict tally reproduces g3_map.json verdict_counts")
    fig_g3_overlay(reg, g3)
    _w("fH_g3_overlay.json",
       dict(item="H-6",
            overlay_rule="consistency overlay only; never enters any likelihood or prior",
            source="paper/h/g3/g3_map.json",
            verdict_counts=tally,
            bh25_favoured=g3["regions"]["BH25_favoured"]["definition"],
            hpd90_regions={k: v["hpd"] for k, v in region_record.items()}))

    # --- H-2 ---------------------------------------------------------------
    rows = lnk_ladder_rows()
    minority = [r["label"] for r in rows if r["minority_sign"]]
    verdict_rows = [r for r in rows if not r["use_profile"]]
    vmin = min(r["lnK_min"] for r in verdict_rows)
    vmax = max(r["lnK_max"] for r in verdict_rows)
    if any(r["minority_sign"] for r in verdict_rows):
        raise SystemExit("a verdict row carries the minority sign")
    checks.append("sixteen fiducial-bracket ln K rows read from the FLAG D record; "
                  "verdict rows span +%.3f to +%.3f, all one-signed" % (vmin, vmax))
    fig_lnk_ladder(rows)
    _w("fH_lnk_ladder.json",
       dict(item="H-2", bracket="fiducial", n_configurations=len(rows),
            cells_per_row=rows[0]["n_cells"],
            source="paper/h/flagd/results/fit2_msp/fit2_results.json",
            minority_sign_rows=minority,
            verdict_row_span=[vmin, vmax], rows=rows))

    # --- H-3 ---------------------------------------------------------------
    D = 5494.0
    stars = fast_star_table(D)
    sel = L.selection(distance_pc=D)
    rr = np.geomspace(2.0e-3, 3.0, 400)
    p_compact, rec = cluster_params(PRIMARY, reg[PRIMARY]["map_M"],
                                    reg[PRIMARY]["map_a"])
    bh = g3["regions"]["BH25_favoured"]["definition"]
    M_ext = float(np.mean(bh["m_range"]))
    a_ext = float(np.mean(bh["a_range"]))
    p_extended, _ = cluster_params(PRIMARY, M_ext, a_ext)
    p_vis, _ = cluster_params(PRIMARY, 0.0, 1e-4)
    curves = dict(R_pc=rr.tolist(), distance_pc=D,
                  visible=mc.v_esc(rr, p_vis).tolist(),
                  compact=mc.v_esc(rr, p_compact).tolist(),
                  extended=mc.v_esc(rr, p_extended).tolist(),
                  compact_label=(r"+ compact MAP, $2.5\times10^{4}\,M_\odot$ "
                                 r"at $a = 10^{-4}$ pc"),
                  extended_label=(r"+ BH25-favoured, $2.5\times10^{5}\,M_\odot$ "
                                  r"at $a = 1.85$ pc"))
    v_cent = float(mc.v_esc(np.array([1e-4]), p_vis)[0])
    cat = L.structural_parameters()["central_escape_velocity_km_s"]
    if abs(v_cent - cat) / cat > 0.05:
        raise SystemExit("visible-only central v_esc %.2f against catalogue %.2f"
                         % (v_cent, cat))
    checks.append("visible-only central escape velocity %.2f km/s reproduces the "
                  "Baumgardt-Hilker catalogue value %.1f km/s to %.1f per cent"
                  % (v_cent, cat, 100.0 * abs(v_cent - cat) / cat))
    r_search_pc = 3.0 / L.ARCSEC_PER_RAD * D
    fig_fast_stars(stars, curves, sel["v_min"], r_search_pc)
    _w("fH_fast_stars.json",
       dict(item="H-3", distance_pc=D, configuration=PRIMARY, bracket="fiducial",
            source="paper/h/data/fast_stars.json via fit/load_data.py",
            caveat="the curve is v_esc evaluated at r = R_proj, an upper bound on "
                   "v_esc at the star's unknown three-dimensional radius; the plotted "
                   "speeds are two-dimensional and bound the space velocity from below",
            selection_v_min_kms=float(sel["v_min"]),
            search_radius_pc=r_search_pc,
            visible_central_v_esc_kms=v_cent,
            catalogue_central_v_esc_kms=cat,
            extended_point=dict(M_dark=M_ext, a_pc=a_ext,
                                source="g3_map.json regions.BH25_favoured"),
            stars=stars, curves=curves))

    # --- H-4 ---------------------------------------------------------------
    psr = L.pulsars(distance_pc=D)
    cell = [x for x in rec["cells"] if x["bracket"] == "fiducial"
            and x["M_range"].startswith("full") and x["a_range"].startswith("full")][0]
    p_cell, _ = cluster_params(PRIMARY, cell["map_M_dark"], cell["map_a_dark"])
    mine = accel_envelope(p_cell, psr["R_pc"])
    want = np.array(cell["ppc_accel_extrema"]["model_max_abs"])
    if not np.allclose(mine, want, rtol=1e-9, atol=0.0):
        raise SystemExit("accel envelope does not reproduce the record: %s"
                         % (mine - want))
    checks.append("model acceleration envelope reproduces the record cell's "
                  "ppc_accel_extrema to 1e-9 relative at all seven pulsars")
    Rgrid = np.geomspace(0.45, 12.0, 300)
    env = dict(R_pc=Rgrid.tolist(),
               compact=accel_envelope(p_compact, Rgrid).tolist(),
               extended=accel_envelope(p_extended, Rgrid).tolist(),
               compact_label=curves["compact_label"].replace("+ ", ""),
               extended_label=curves["extended_label"].replace("+ ", ""))
    fig_pulsar_bounds(psr, env)
    n_neg = int((psr["A_bound"] < 0).sum())
    _w("fH_pulsar_bounds.json",
       dict(item="H-4", distance_pc=D, configuration=PRIMARY, bracket="fiducial",
            source="paper/h/data/pulsars.json via fit/load_data.py; envelope by the "
                   "same line-of-sight quadrature as fit/pulsar_leg.accel_extrema",
            unit="(km/s)^2/pc; 1 unit = %.6e m/s^2" % L.ACC_UNIT,
            n_bounds=len(psr["names"]), n_negative_signed=n_neg,
            names=psr["names"],
            A_bound=[float(x) for x in psr["A_bound"]],
            A_err=[float(x) for x in psr["A_err"]],
            R_pc=[float(x) for x in psr["R_pc"]],
            envelope=env,
            record_check=dict(cell_map_M_dark=cell["map_M_dark"],
                              cell_map_a_dark=cell["map_a_dark"],
                              model_max_abs=[float(x) for x in mine])))

    # --- H-5 ---------------------------------------------------------------
    g2 = json.load(open(G2_RESULTS, encoding="utf-8"))
    xi_cf = jd.xi_closed_form()
    xi_q = g2["xi_quadrature"]
    if abs(xi_cf - xi_q) > 1e-9:
        raise SystemExit("xi disagreement: %.12f vs %.12f" % (xi_cf, xi_q))
    checks.append("closed-form xi = %.6f agrees with the stored quadrature to %.1e"
                  % (xi_cf, abs(xi_cf - xi_q)))
    deltas = json.load(open(JERK_DELTAS, encoding="utf-8"))
    block = deltas["sigma_kms"]["paper-set 21 km/s"]["FLAG D fiducial"]
    fig_jerk_dist(block, xi_cf, jd.XI_PUBLISHED)
    a0 = float(np.median([r["a0_floor"] for r in block["rows"]]))
    _w("fH_jerk_dist.json",
       dict(item="H-5", xi_closed_form=xi_cf, xi_quadrature=xi_q,
            xi_published=jd.XI_PUBLISHED,
            xi_ratio=xi_cf / jd.XI_PUBLISHED,
            floor_understatement_per_cent=100.0 * (1.0 - jd.XI_PUBLISHED / xi_cf),
            source=dict(constant="paper/h/jerk/g2_results.json",
                        floors="paper/h/flagd/results/jerk_deltas.json, "
                               "paper-set 21 km/s / FLAG D fiducial"),
            a0_median_corrected=a0, a0_median_published=a0 * jd.XI_PUBLISHED / xi_cf,
            measured_jerks=[dict(name=r["name"], jerk=r["jerk"],
                                 jerk_err=r["jerk_err"], a0_floor=r["a0_floor"],
                                 jerk_over_floor=r["jerk_over_floor"])
                            for r in block["rows"]],
            note="the density is the 1-stable (Cauchy) line-of-sight nearest-neighbour "
                 "jerk law of Prager Eq B10; the two vertical lines are the same "
                 "physical floor evaluated at the two constants"))

    print("H-EXPAND-1 figures written. Checks:")
    for c in checks:
        print("  ok:", c)


if __name__ == "__main__":
    main()
