# CLAUDE.md — The Omega Centauri Society

**Site:** omegacentauri.me | **Owner:** Tim (tim@postoaklabs.com) | **Updated:** 2026-06-02

**Current counts:** 59 tools · 7 workflows · 30 scenarios · 2 narrative/dashboard pages · 11 proposals · 1 pathways page

Science portal about NGC 5139 (Omega Centauri): candidate IMBH, Fermi Paradox, Macro Transcension Hypothesis (MTH). No framework, no build pipeline, no npm — hand-written HTML/CSS/JS, all inline per file. Two content registers kept strictly separate: peer-reviewed science (DOI-sourced) and speculative engineering (MTH/computronium — always labeled).

---

## ⚠ Token landmines — do NOT read these whole

| File | Size | Use instead |
|---|---|---|
| `index.html` | ~700 KB / ~4,800 lines | `Grep` or `Read` with `offset`/`limit` |
| `faq.html` | ~166 KB | `Grep` |
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

---

## File map

```
repo/
├── index.html                     ← main site (TOKEN LANDMINE)
├── faq.html                       ← FAQ (TOKEN LANDMINE)
├── proposals.html                 ← hub for 11 observational proposals
├── proposal_*.html                ← 11 proposals (14–25 KB each — readable whole)
└── tools/
    ├── index.html                 ← tools landing page
    ├── data/measurements.js       ← SINGLE SOURCE OF TRUTH for IMBH/cluster values
    ├── [59 tool *.html files]     ← see categories below
    ├── [7 workflow-*.html files]  ← end-to-end staged narrative calculators
    └── [30 scenario-*.html files]     ← chained-tool narrative demos
```

**Tool categories (52 total):**
- *IMBH evidence (11):* constraint-stacker, imbh-timeline, cluster-comparator, velocity-dispersion, pulsar-timing, orbital-dynamics, tidal-disruption, synthetic-observation, jwst-accretion, cw-sensitivity, oc-orbit-simulator
- *Computronium / MTH (14):* bz-kardashev, bekenstein-landauer, time-dilation, hawking-evaporation, kerr-geometry, compute-in-space, matrioshka-brain, reversible-computing, stem-compression, penrose-process, magnetic-reconnection, spin-up-timeline, kugelblitz-dvali, barrow-scale
- *Fermi / SETI (16):* drake-monte-carlo, great-filter, aestivation, superradiance, dyson-swarm, lisa-emri, cmd-explorer, radio-seti, optical-seti, neutrino-seti, interstellar-link, multi-messenger-alert, passive-seti, iso-encounter, gamma-ray-msp, jet-radio-detectability
- *Cluster physics (8):* mass-segregation, omegacat-populations, omega-dwarf-origin, dark-cluster, dark-matter-flux, tidal-capture, imbh-growth-history, seed-formation
- *Context (3):* cosmic-center, cosmological-natural-selection, astrometric-microlensing
- *Civilisational cosmology (10):* monkeygod-simulator, cns-fitness-landscape, gough-blowtorch, cns-three-stage, starivore-energy, ferd-complexity-ladder, transcension-crossover, stem-compression, barrow-scale, kugelblitz-dvali
- *Hub pages (2):* tools/index.html, tools/falsification-hub.html

**Workflows (7):** workflow-mth-compute-budget, workflow-fermi-mth-crossover, workflow-bh-energy-budget, workflow-wait-or-act, workflow-constraint-window, workflow-survivability, workflow-spin-economics — staged calculators with live stage-to-stage handoff and copy-to-clipboard export. Use an existing workflow as template for new ones.

---

## After every edit session

```powershell
cd "C:\dev\Claude\Projects\The Omega Centauri Society\repo"
if (Test-Path .git/index.lock) { Remove-Item .git/index.lock -Force }
git add <files>
git commit -m "<message>"
git push
```
