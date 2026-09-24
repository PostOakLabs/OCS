#!/usr/bin/env python3
"""
check-p0calc-parity.py — standalone parity gate for the two explorer pages'
embedded paper data (OCS-P0-CALC-1 / P0-08, P0-09).

Reads NO outer-repo file (paper/figs is not present in a fresh site
checkout). Instead it pins the values of record at WU time and fails when the
generated embeds drift from them:

  tools/data/fF_v4_embed.js   ANCHORS_M == [6000, 8200, 40000];
                              ANCHORS_EXCL at 8,200/40,000 M☉ ≈
                              85.0% / 99.3% (riaf), 78.5% / 98.5% (jet) —
                              the paper's 85/78/99 headline — with a ±0.5 pp
                              Monte Carlo tolerance; 41-point curves present
                              for all three channels; CROSSINGS finite.
  tools/data/fH_plane_embed.js each configuration's hpd/pl intervals and
                              shipped cell counts equal the values pinned
                              from paper/figs/fH_posterior_plane.json
                              (pinned from outer commit 5d4615c-era tree,
                              2026-09-24).

It also asserts both explorer pages actually reference their embed files, so
the page→embed chain cannot silently detach.

Usage (from repo root):  python3 scripts/check-p0calc-parity.py
Zero dependencies (stdlib only). Wired into deploy.yml Job 1 + scripts/pre-push.
"""
import json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# paper/figs/fF_v4_exclfrac.json p_excl_ppc at [6000, 8200, 40000], 2026-09-24.
FF_ANCHOR_PINS = {
    "riaf":        [0.777125, 0.8503, 0.992775],
    "jet":         [0.6969, 0.7846, 0.98525],
    "riaf_noradio": [0.20085, 0.2814, 0.762075],
}
MC_TOL = 0.005  # ±0.5 pp Monte Carlo tolerance around the pins

# paper/figs/fH_posterior_plane.json item H-1 (level 0.90, fiducial bracket),
# pinned 2026-09-24: M_lo, M_hi, a_hi, n_cells, n_grid per region.
FH_PINS = {
    "nolegprof_plummer_5200": {
        "hpd": [17782.794100389227, 25118.864315095823, 0.012283531735409992, 49, 1891],
        "pl":  [17782.794100389227, 28183.82931264455, 0.017320508075688777, 58, 1891],
    },
    "nolegprof_plummer_5494": {
        "hpd": [22387.21138568338, 28183.82931264455, 0.017320508075688777, 44, 1891],
        "pl":  [19952.62314968879, 31622.776601683792, 0.017320508075688777, 57, 1891],
    },
    "nolegprof_abg_5200": {
        "hpd": [17782.794100389227, 22387.21138568338, 0.012283531735409992, 42, 1891],
        "pl":  [15848.93192461114, 25118.864315095823, 0.017320508075688777, 55, 1891],
    },
    "nolegprof_abg_5494": {
        "hpd": [19952.62314968879, 25118.864315095823, 0.008711358306319453, 39, 1891],
        "pl":  [19952.62314968879, 28183.82931264455, 0.017320508075688777, 45, 1891],
    },
}


def load_embed(rel):
    """Parse 'const NAME = {...};' (generated) into a dict."""
    path = os.path.join(REPO, rel)
    text = open(path, encoding="utf-8").read()
    m = re.search(r"=\s*(\{.*\})\s*;\s*$", text, re.S)
    if not m:
        raise ValueError("%s: no 'const ... = {...};' payload found" % rel)
    return json.loads(m.group(1))


def main():
    bad = []

    # ---------- Paper F embed ----------
    try:
        ff = load_embed(os.path.join("tools", "data", "fF_v4_embed.js"))
    except Exception as e:
        print("[FAIL] %s" % e)
        return 1
    if [round(x) for x in ff.get("ANCHORS_M", [])] != [6000, 8200, 40000]:
        bad.append("fF_v4_embed: ANCHORS_M = %r != [6000, 8200, 40000]" % ff.get("ANCHORS_M"))
    for fam, pins in FF_ANCHOR_PINS.items():
        got = ff.get("ANCHORS_EXCL", {}).get(fam)
        if not got or len(got) != 3:
            bad.append("fF_v4_embed: ANCHORS_EXCL.%s missing" % fam)
            continue
        for mass, g, p in zip([6000, 8200, 40000], got, pins):
            if abs(g - p) > MC_TOL:
                bad.append("fF_v4_embed: %s @ %d = %.4f, pinned %.4f (> %.3f)"
                           % (fam, mass, g, p, MC_TOL))
    for fam, curve in (ff.get("EXCLFRAC") or {}).items():
        if len(curve) != 41:
            bad.append("fF_v4_embed: EXCLFRAC.%s has %d points, expected 41" % (fam, len(curve)))
    for fam, cr in (ff.get("CROSSINGS") or {}).items():
        if not cr.get("M50") or not cr.get("M90"):
            bad.append("fF_v4_embed: CROSSINGS.%s not finite: %r" % (fam, cr))

    # ---------- Paper H embed ----------
    try:
        fh = load_embed(os.path.join("tools", "data", "fH_plane_embed.js"))
    except Exception as e:
        print("[FAIL] %s" % e)
        return 1
    cfgs = fh.get("configurations", {})
    for cfg, pins in FH_PINS.items():
        for reg in ("hpd", "pl"):
            c = cfgs.get(cfg, {}).get(reg)
            if not c:
                bad.append("fH_plane_embed: %s.%s missing" % (cfg, reg))
                continue
            got = [c.get("M_lo"), c.get("M_hi"), c.get("a_hi"), c.get("n_cells"), c.get("n_grid")]
            for name, g, p in zip(["M_lo", "M_hi", "a_hi", "n_cells", "n_grid"], got, pins[reg]):
                if isinstance(p, int):
                    ok = g == p
                else:
                    ok = g is not None and abs(g - p) <= 1e-9 * max(1.0, abs(p))
                if not ok:
                    bad.append("fH_plane_embed: %s.%s.%s = %r, pinned %r" % (cfg, reg, name, g, p))

    # ---------- page -> embed chain ----------
    for page, needle in (
        ("tools/joint-accretion-bound-explorer.html", 'src="data/fF_v4_embed.js"'),
        ("tools/mass-tension-explorer.html", 'src="data/fH_plane_embed.js"'),
    ):
        text = open(os.path.join(REPO, page), encoding="utf-8").read()
        if needle not in text:
            bad.append("%s no longer references %s" % (page, needle))

    if bad:
        print("[FAIL] embedded-data parity — %d drift(s):" % len(bad))
        for b in bad:
            print("  " + b)
        print("\nRegenerate with scripts/gen-p0calc-embeds.py (workspace step; "
              "needs ../paper/figs) ONLY when the paper's own outputs moved — "
              "then update the pins here in the same commit.")
        return 1
    print("[OK] embedded-data parity: fF_v4 anchors (85.0/78.5/99.3 ±0.5 pp), "
          "41-pt curves, finite crossings, fH intervals + cell counts, and both "
          "page→embed references all match the pins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
