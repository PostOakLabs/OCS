# CLAUDE.md — The Omega Centauri Society

**Site:** omegacentauri.me | **Owner:** Tim (tim@postoaklabs.com) | **Updated:** 2026-06-02

**Counts drift — do not trust any hardcoded number here.** Re-count before quoting: `cd tools && ls *.html | wc -l` (all pages), `ls workflow-*.html | wc -l`, `ls scenario-*.html | wc -l`, `ls ../proposal*.html | wc -l`. (As of 2026-06-25: ~98 calculators · 19 workflows · 30 scenarios · 12 proposals — already ahead of older figures.) The category lists below are illustrative groupings, not an exhaustive or current inventory.

Science portal about NGC 5139 (Omega Centauri): candidate IMBH, Fermi Paradox, Macro Transcension Hypothesis (MTH). No framework, no build pipeline, no npm — hand-written HTML/CSS/JS, all inline per file. Two content registers kept strictly separate: peer-reviewed science (DOI-sourced) and speculative engineering (MTH/computronium — always labeled).

---

## ⚠ Token landmines — do NOT read these whole

| File | Size | Use instead |
|---|---|---|
| `faq.html` | ~240 KB (237,357 B) | `Grep` |
| `references.html` | ~220 KB (219,056 B) | `Grep` |
| `hypothesis.html` | ~175 KB (173,043 B) | `Grep` |
| Tool files >40 KB | varies | `compute-in-space`, `constraint-stacker`, `orbital-dynamics`, `cmd-explorer`, `lisa-emri`, `bekenstein-landauer`, `radio-seti`, `bz-kardashev` — `Grep` for specific functions |

Never read: `og-image.png` (204 KB), `apple-touch-icon.png`, `favicon.ico`.

---

## Architecture rules (never violate)

1. **Browser-only** — no backend, no npm, no build step
2. **No PII / no tracking** — no form submission, no identity localStorage, no cookies, no analytics
3. **No runtime network calls** — no fetch/XHR; tools work from `file://` (Google Fonts excepted)
4. **Single HTML per tool** — all CSS/JS inline; only shared external file is `<script src="data/measurements.js">`
5. **URL hash state** — every tool serializes state to `#key=val&...` on interaction, restores on load
6. **Measurements in `measurements.js` only** — never hardcode IMBH/cluster values in tool files

---

## Critical gotchas

### Gate scripts print ASCII only
Non-ASCII characters (arrows, fancy dashes) in gate-script `print()` strings exit 1 via UnicodeEncodeError on Windows cp1252 consoles while CI (UTF-8) stays green — the failure is console-dependent and invisible in CI logs. Keep gate output ASCII (P0-RESIDUE-1, 2026-09-25).

### IMBH mass tension
Two irreconcilable bounds, both current and valid — **never collapse to one number**:
- Häberle et al. 2024 (*Nature*): **≥ 8,200 M☉** (lower limit, stellar kinematics)
- Bañares-Hernández et al. 2025 (*A&A* 693 A104): **≤ 6,000 M☉** (upper limit, pulsar timing)

### Hash units for demo deeplinks
When chaining tools via `tools/toolname.html#param=val`:
- **Most tools:** hash values are **linear** native units (e.g. `mass=8200` = 8,200 M☉)
- **`optical-seti.html`:** takes **linear** input, internally log10s it — pass linear values
- **`radio-seti.html`:** hash params **are** log10 (`logEirp`, `logDist`, etc.)
- **Rule:** always `Grep` each tool's `loadHash()` block; check `state.X = parseFloat(v)` (linear) vs `state.logX = parseFloat(v)` (log10) before wiring

### Scenario page pattern
`tools/scenario-*.html` files chain existing tools as deeplinks (no iframes). Structure: scenario selector → step cards with CTA hash links → synthesis box. Use `scenario-breaking-degeneracy.html` as template (6-step); `scenario-dwarf-inheritance.html` for 4-step. Scenarios must not use `measurements.js` unless they actually need cluster data.

### Adding a paper or proposal
Enforced by `scripts/check-index-order.py` (pre-push + CI). Papers and proposals are not ordered automatically; follow this list.

**New paper**
1. Take the next letter after the last `Paper X` card on `paper.html` (currently A–H). A methods note, erratum or other companion is not lettered; label it "… companion to Paper X".
2. Add its card to `paper.html` immediately after the previous lettered paper; a companion goes directly after its parent paper (after any existing companions of that parent).
3. Card markup: `<a class="paper-card" href="/<file>.html">` with the label line "Paper X · Short title" (or "… companion to Paper X"), title in `<h2>`, byline, abstract. Presenter mode picks the card up automatically.
4. Add the page to `sitemap.xml` and `sitemap.html`; give it the shared nav, `ocs-crumb` breadcrumb (`OCS / Papers / <short title>`) and the shared footer.
5. Update the paper count in the `paper.html` lede ("Nine companion preprints …") and anywhere `verify-counts.py` reports.

**New proposal**
1. Create `proposal_<slug>.html` from an existing proposal page.
2. Link it exactly once from `proposals.html`, inside the `<section>` for its channel (neutrino, gamma-ray, radio, infrared, multi-messenger/GW, time-domain, astrometry); add a new `<section><h2>…</h2>` only for a genuinely new channel (it becomes a presenter step automatically).
3. Add it to `sitemap.xml` and `sitemap.html`, and update the proposal count in the `proposals.html` lede and any count sentinels (`python3 scripts/verify-counts.py`).

---

## File map

```
repo/
├── index.html                     ← homepage (~90 KB, readable with offset/limit)
├── omega-centauri.html            ← NGC 5139 physical overview (~84 KB)
├── hypothesis.html                ← Macro Transcension Hypothesis (TOKEN LANDMINE, ~175 KB)
├── fermi.html                     ← Fermi Paradox context (~81 KB)
├── roadmap.html                   ← project roadmap and phases (~105 KB)
├── references.html                ← bibliography and citation notes (TOKEN LANDMINE, ~220 KB)
├── faq.html                       ← FAQ, 60 items (TOKEN LANDMINE, ~240 KB)
├── proposals.html                 ← hub for 13 observational proposals (order rules: "Adding a paper or proposal")
├── proposal_*.html                ← 13 proposals (14–25 KB each — readable whole)
└── tools/
    ├── index.html                 ← tools landing page
    ├── data/measurements.js       ← SINGLE SOURCE OF TRUTH for IMBH/cluster values
    ├── [82 tool *.html files]     ← see categories below (category list partially stale)
    ├── [15 workflow-*.html files] ← end-to-end staged narrative calculators
    └── [30 scenario-*.html files] ← chained-tool narrative demos (incl. scenario-bh-tap)
```

**Tool categories (52 total):**
- *IMBH evidence (13):* constraint-stacker, imbh-timeline, cluster-comparator, velocity-dispersion, pulsar-timing, orbital-dynamics, tidal-disruption, synthetic-observation, jwst-accretion, cw-sensitivity, oc-orbit-simulator, qpo-mass-spin, tde-rate
- *Computronium / MTH (14):* bz-kardashev, bekenstein-landauer, time-dilation, hawking-evaporation, kerr-geometry, compute-in-space, matrioshka-brain, reversible-computing, stem-compression, penrose-process, magnetic-reconnection, spin-up-timeline, kugelblitz-dvali, barrow-scale
- *Fermi / SETI (19):* drake-monte-carlo, great-filter, aestivation, superradiance, dyson-swarm, lisa-emri, cmd-explorer, radio-seti, optical-seti, neutrino-seti, interstellar-link, multi-messenger-alert, passive-seti, iso-encounter, gamma-ray-msp, jet-radio-detectability, galaxy-percolation, galactic-habitable-zone
- *Cluster physics (8):* mass-segregation, omegacat-populations, omega-dwarf-origin, dark-cluster, dark-matter-flux, tidal-capture, imbh-growth-history, seed-formation
- *Context (3):* cosmic-center, cosmological-natural-selection, astrometric-microlensing
- *Civilisational cosmology (14):* monkeygod-simulator, cns-fitness-landscape, gough-blowtorch, cns-three-stage, starivore-energy, ferd-complexity-ladder, transcension-crossover, stem-compression, barrow-scale, kugelblitz-dvali, spider-stellar-engine, life-viability-landscape, gough-spiral-galaxy, grabby-aliens
- *Hub pages (2):* tools/index.html, tools/falsification-hub.html

**Workflows (10):** workflow-mth-compute-budget, workflow-fermi-mth-crossover, workflow-bh-energy-budget, workflow-wait-or-act, workflow-constraint-window, workflow-survivability, workflow-spin-economics, workflow-evodevouniverse, workflow-tde-detection, workflow-grabby-fermi 