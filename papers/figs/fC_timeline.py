"""Figure: campaign Gantt timeline 2026-2040 for Paper C
(campaign-paper.tex, Fig.~\ref{fig:gantt}, placed in Section sec:decision
before the decision tree).

Three layers on one time axis:

  (a) facility schedule (grey bars): Rubin/LSST (10-yr LSST from 2026 Jun 30),
      Gaia DR4 (marker, 2026 Dec 2), Roman (launch 2026 Aug 30, 5-yr mission),
      JWST (ongoing; the two P1 epochs marked), MeerKAT (P2 timing + SETI),
      SKA-Mid (science verification 2029), ELT/MICADO (first light 2029),
      KM3NeT/ARCA (build-out to the 230-DU completion), CTAO-South, LISA
      (2035 launch);
  (b) decision points D1-D4 as dashed vertical lines (D1 2027 DR4 frame
      re-derivation; D2 2030 timing profile + Roman wander; D3 2033 pre-LISA
      synthesis; D4 2035+ LISA), per Section sec:decision;
  (c) program phases P1-P3, P5-P8 as coloured bars (colours match the
      existing TikZ timeline, fig:timeline, in Section sec:cost).

A bottom strip counts simultaneously active facility + program tracks per
year: coverage peaks in 2029, when SKA-Mid and ELT/MICADO come online while
the MeerKAT, JWST, and KM3NeT programs are still running.

All years transcribed from campaign-paper.tex (Section 1.1 facility list,
Table 5 program timelines, Section sec:cost timeline, Section sec:decision
D1-D4 definitions).

Run:  python fC_timeline.py
Writes fC_timeline.pdf / .png / .json next to this script.
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.lines import Line2D      # noqa: E402
from matplotlib.patches import Patch     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

GREY_F = "#85929e"       # facility bars
EDGE = "#4d5656"
DEC = "#8b0000"          # decision lines
# Program colours (match the existing fig:timeline TikZ hues).
PROG = {
    "P1": "#2e86c1",
    "P2": "#5dade2",
    "P3": "#e74c3c",
    "P5": "#27ae60",
    "P6": "#f39c12",
    "P7": "#9b59b6",
    "P8": "#aab7b8",
}

plt.rcParams.update({
    "font.size": 9,
    "font.family": "serif",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# (label, start, end, in-bar note)
FACILITIES = [
    ("Rubin/LSST",   2026.0, 2036.0, "10-yr LSST"),
    ("Gaia DR4",     None, None, "DR4: 2026 Dec 2"),          # marker row
    ("Roman",        2026.66, 2031.7, "launch 2026 Aug 30; 5-yr mission"),
    ("JWST",         2026.0, 2035.0, "P1 epochs \u00d72 (~6 mo apart)"),
    ("MeerKAT",      2026.0, 2031.5, "P2 timing + SETI"),
    ("SKA-Mid",      2029.0, 2040.0, "science verification 2029"),
    ("ELT/MICADO",   2029.0, 2040.0, "first light 2029"),
    ("KM3NeT/ARCA",  2026.0, 2035.0, "build-out \u2192 230 DUs"),
    ("CTAO-South",   2028.0, 2040.0, ""),
    ("LISA",         2035.0, 2040.0, "launch ~2035"),
]

# (label, start, end, colour-key)
PROGRAMS = [
    ("P1  JWST imaging + waste heat", 2026.0, 2029.0, "P1"),
    ("P2  MeerKAT timing + SETI",     2026.0, 2031.5, "P2"),
    ("P3  astrometry (DR4/Roman/ELT)", 2026.0, 2033.0, "P3"),
    ("P5  KM3NeT/ARCA commensal",     2026.0, 2035.0, "P5"),
    ("P6  Fermi archival + CTAO",     2026.0, 2035.0, "P6"),
    ("P7  Rubin/LSST commensal",      2026.0, 2036.0, "P7"),
    ("P8  archival (X-ray/CW/UHECR)", 2026.0, 2029.0, "P8"),
]

DECISIONS = [
    (2027, "D1 (2027)\nDR4 frame\nre-derivation"),
    (2030, "D2 (2030)\ntiming profile +\nRoman wander"),
    (2033, "D3 (2033)\npre-LISA\nsynthesis"),
    (2035, "D4 (2035+)\nLISA"),
]

fig, (ax, axc) = plt.subplots(
    2, 1, figsize=(10.6, 7.4), sharex=True,
    gridspec_kw={"height_ratios": [5.6, 1.0], "hspace": 0.06})

# --- main Gantt -------------------------------------------------------------
n_fac = len(FACILITIES)
n_prog = len(PROGRAMS)
ys_fac = list(range(1, n_fac + 1))                       # 1..10
sep_y = n_fac + 0.8
ys_prog = [n_fac + 1.6 + i for i in range(n_prog)]       # 11.6..17.6
y_top = -1.9                                             # headroom for D labels
y_bot = n_fac + 1.6 + n_prog - 0.2

for (label, s, e, note), y in zip(FACILITIES, ys_fac):
    if s is None:                                        # Gaia DR4 marker
        ax.plot([2026.92], [y], marker="D", markersize=7, color=EDGE,
                zorder=4)
        ax.text(2027.25, y, "DR4: 2026 Dec 2", fontsize=7.4, va="center",
                color=EDGE)
        continue
    ax.barh(y, e - s, left=s, height=0.62, color=GREY_F, edgecolor=EDGE,
            linewidth=0.7, zorder=2)
    if note:
        ax.text((s + e) / 2, y, note, fontsize=7.0, ha="center", va="center",
                color="white", zorder=3)

for (label, s, e, key), y in zip(PROGRAMS, ys_prog):
    ax.barh(y, e - s, left=s, height=0.62, color=PROG[key], edgecolor=EDGE,
            linewidth=0.7, zorder=2)
    ax.text(s + 0.12, y, label, fontsize=7.2, ha="left", va="center",
            color="white", fontweight="bold", zorder=3)

# JWST P1 epoch ticks (two epochs, ~6 months apart, within the P1 window).
jwst_y = ys_fac[3]
for xep in (2027.0, 2027.5):
    ax.plot([xep, xep], [jwst_y - 0.31, jwst_y + 0.31], color="k", lw=1.6,
            zorder=4)

# block separator + block titles (right edge, clear of bars and D labels)
ax.axhline(sep_y, color="k", lw=0.7, alpha=0.5)
ax.text(2040.45, 0.45, "FACILITY SCHEDULE", fontsize=8, fontweight="bold",
        ha="right", va="center", color="#333333")
ax.text(2040.45, sep_y + 0.42, "CAMPAIGN PROGRAMS", fontsize=8,
        fontweight="bold", ha="right", va="center", color="#333333")

# decision lines + staggered labels
for i, (xd, lab) in enumerate(DECISIONS):
    ax.axvline(xd, color=DEC, ls="--", lw=1.5, ymin=0.0, ymax=0.96, zorder=5)
    ytxt = -0.35 if i % 2 == 0 else -1.25
    ax.text(xd, ytxt, lab, fontsize=7.3, ha="center", va="top", color=DEC,
            fontweight="bold", zorder=6,
            bbox=dict(facecolor="white", edgecolor=DEC, lw=0.7,
                      boxstyle="round,pad=0.25", alpha=0.95))

ax.set_ylim(y_bot, y_top)
ax.set_yticks(ys_fac + ys_prog)
ax.set_yticklabels([f[0] for f in FACILITIES] + [p[0] for p in PROGRAMS],
                   fontsize=8)
ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
for spine in ("top", "right", "bottom"):
    ax.spines[spine].set_visible(False)

# --- coverage strip ---------------------------------------------------------
years = list(range(2026, 2041))


counts = []
for y in years:
    c = 1 if y <= 2036 else 0                           # Rubin
    c += 1 if 2026.66 <= y <= 2031.7 else 0             # Roman
    c += 1 if y <= 2035 else 0                          # JWST
    c += 1 if y <= 2031.5 else 0                        # MeerKAT
    c += 1 if 2029 <= y else 0                          # SKA
    c += 1 if 2029 <= y else 0                          # ELT
    c += 1 if y <= 2035 else 0                          # KM3NeT
    c += 1 if 2028 <= y else 0                          # CTAO
    c += 1 if 2035 <= y else 0                          # LISA
    for (_, s, e, _) in PROGRAMS:
        c += 1 if s <= y <= e else 0
    counts.append(c)

axc.bar(years, counts, width=0.72, color="#34495e", alpha=0.85, zorder=2)
for y, c in zip(years, counts):
    axc.text(y, c + 0.25, str(c), fontsize=7, ha="center", va="bottom",
             color="#34495e")
peak = max(counts)
axc.text(2031.8, peak + 1.1,
         f"peak simultaneous coverage: {years[counts.index(peak)]} ({peak} tracks)",
         fontsize=7.6, color="#34495e", ha="left", va="center")
for xd, _ in DECISIONS:
    axc.axvline(xd, color=DEC, ls="--", lw=1.2, zorder=1)
axc.set_xlim(2025.4, 2040.6)
axc.set_ylim(0, peak + 2.2)
axc.set_ylabel("simultaneously\nactive tracks", fontsize=8)
axc.set_xticks(list(range(2026, 2041, 2)))
axc.set_xticklabels([str(y) for y in range(2026, 2041, 2)], fontsize=8.5)
axc.tick_params(axis="x", length=0)

# --- legend -----------------------------------------------------------------
handles = [Patch(facecolor=GREY_F, edgecolor=EDGE, label="facility schedule")]
prog_labels = {
    "P1": "JWST imaging", "P2": "MeerKAT timing+SETI", "P3": "astrometry",
    "P5": "KM3NeT commensal", "P6": "Fermi/CTAO", "P7": "LSST commensal",
    "P8": "archival",
}
for k in ["P1", "P2", "P3", "P5", "P6", "P7", "P8"]:
    handles.append(Patch(facecolor=PROG[k], edgecolor=EDGE,
                         label=f"{k} {prog_labels[k]}"))
handles.append(Line2D([0], [0], color=DEC, ls="--", lw=1.5,
                      label="decision point D1\u2013D4"))
fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
           fontsize=7.8, bbox_to_anchor=(0.5, -0.015), columnspacing=1.2,
           handlelength=1.3)

fig.subplots_adjust(left=0.155, right=0.985, top=0.985, bottom=0.115)
fig.savefig(os.path.join(HERE, "fC_timeline.pdf"))
fig.savefig(os.path.join(HERE, "fC_timeline.png"))

record = {
    "facilities": {f[0]: {"start": f[1], "end": f[2], "note": f[3]}
                   for f in FACILITIES},
    "programs": {p[0]: {"start": p[1], "end": p[2]} for p in PROGRAMS},
    "decisions": {lab.split(" ")[0]: year for year, lab in DECISIONS},
    "active_tracks_per_year": dict(zip(years, counts)),
    "sources": "campaign-paper.tex: Section 1.1 facility list, Table 5, "
               "Section sec:cost fig:timeline, Section sec:decision D1-D4",
}
with open(os.path.join(HERE, "fC_timeline.json"), "w", encoding="utf-8") as fh:
    json.dump(record, fh, indent=2)
print("wrote fC_timeline.pdf / .png / .json")
print("active tracks per year:",
      {y: c for y, c in zip(years, counts)})
