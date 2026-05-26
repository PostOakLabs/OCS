# CLAUDE.md — The Omega Centauri Society

**Site:** omegacentauri.me  
**Owner:** Tim Swanson (tim@postoaklabs.com)  
**Last updated:** 2026-05-23

---

## What this project is

A solo-maintained, hand-written HTML/CSS/JS science portal about NGC 5139 (Omega Centauri) — its candidate intermediate-mass black hole (IMBH), Fermi Paradox implications, and the Macro Transcension Hypothesis (MTH). No framework, no build pipeline, no npm, no service worker, no manifest.json — by design. All CSS and JS is inline per file.

Two content registers, kept strictly separate:
- **Peer-reviewed science** — sourced to DOIs and arXiv
- **Speculative engineering** — the MTH, five-phase civilisation roadmap, computronium; always labeled as such

**One factual landmine:** IMBH mass is in unresolved tension. Häberle et al. 2024 gives ≥8,200 M☉ (lower limit, stellar kinematics); Bañares-Hernández et al. 2025 gives ≤6,000 M☉ (upper limit, pulsar timing + kinematics). Never collapse to a single number without flagging both.

---

## Tim's working style

- Ask clarifying questions **before** substantive work. Use `AskUserQuestion`, batch 3–4 at a time, mark one `(Recommended)`, explain trade-offs.
- Research with `WebSearch` before making architecture/standards decisions; cite sources.
- Use `TaskCreate` / `TaskUpdate` for non-trivial work.
- He prefers lean infrastructure — don't add files or dependencies unless he asks.
- He verifies claims independently and will push back on overstatements. Be precise.
- Accurate citation is required. This is an academic-adjacent site.

---

## Key files

| File | Purpose |
|---|---|
| `index.html` | Main site — 706 KB, 4,783 lines. Do not read whole (see below). |
| `faq.html` | FAQ — 166 KB. Do not read whole. |
| `membership.html` | Membership page |
| `advisors.html` | Advisors page |
| `proposals.html` | Hub listing all 11 observational proposals |
| `proposal_*.html` | 11 individual proposal pages (14–25 KB each) — readable whole |
| `tools/index.html` | Tools landing page |
| `tools/*.html` | 24 standalone interactive tools (13–63 KB each) |
| `tools/data/measurements.js` | **Single source of truth** for IMBH measurements, cluster properties, pulsar inventory — edit here, not in tool files |
| `ocs-tools-spec-v1.1.md` | **Canonical** tool build spec (59 KB). Has reading guide at top. |
| `HUB_AND_DEMOS_PLAN_2026-05-16.md` | Hub architecture + demo planning doc (38 KB). Has reading guide at top. |
| `HANDOVER_2026-05-12.md` | Session handover with full project history and open items (11 KB) — read this for context |
| `CONTRIBUTING.md` | How to add measurements, fix values, add languages, PR checklist |
| `llms.txt` | AI-agent index of the site (12 KB) — canonical summary for crawlers |
| `robots.txt` | Crawler allow/deny rules |
| `sitemap.xml` | 14 URLs, matches canonicals exactly |
| `LICENSE-code.md` | MIT (code / JS / HTML structure) |
| `LICENSE-content.md` | CC BY 4.0 (prose, captions, descriptions) |
| `LICENSE-data.md` | CC0 1.0 (curated measurement tables only) |

---

## Current build status (as of 2026-05-23)

All 23 numbered tools from the v1.1 spec + two hub pages are built. The `/tools/` directory contains:

**IMBH evidence tools:** constraint-stacker, imbh-timeline, cluster-comparator, velocity-dispersion, pulsar-timing, orbital-dynamics, tidal-disruption, synthetic-observation, jwst-accretion

**Computronium / MTH tools:** bz-kardashev, bekenstein-landauer, time-dilation, hawking-evaporation, kerr-geometry, compute-in-space

**Fermi / SETI tools:** drake-monte-carlo, great-filter, aestivation, superradiance, dyson-swarm, lisa-emri, cmd-explorer, radio-seti

**Hub pages:** `tools/index.html` (master landing), `tools/falsification-hub.html`

**Open items from HANDOVER_2026-05-12.md:**
1. Deploy to live host (local files are ahead of live site)
2. Submit sitemap in Google Search Console + Bing Webmaster Tools (post-deploy)
3. Verify with Google's Rich Results Test (post-deploy)
4. Full `FAQPage` JSON-LD on `faq.html` (currently `WebPage` only)
5. "twelve proposals" inconsistency in `index.html` body (only 11 exist; Tim may have a 12th in progress)
6. Visible "Last updated" lines on `faq.html` and `proposals.html` (polish)

---

## Architecture rules (do not violate)

1. **Browser-only** — no backend, no server calls, no npm, no build step
2. **No PII** — no submitting forms, no identity localStorage, no cookies, no analytics
3. **No network calls at runtime** — no fetch/XHR; tools work from `file://` (Google Fonts excepted)
4. **Self-contained per tool** — single HTML file; only exception is `<script src="data/measurements.js">` for tools that need the shared table
5. **URL hash state** — every interactive tool serializes state to URL hash on each interaction, restores on load
6. **Measurements go in `measurements.js`** — never hardcode IMBH/cluster values in tool files
7. **Shared JS utilities** (spec §11) — character-identical copies across all consumer tools; update all in the same PR

---

## Do NOT read these files whole

These are token landmines — use targeted `Read` with `offset`/`limit`, or `Grep` for specific content:

| File | Size | Why |
|---|---|---|
| `index.html` | 706 KB / 4,783 lines | Main site, inline CSS+content. Use `Grep` or read specific line ranges. |
| `faq.html` | 166 KB / ~4,400 lines | FAQ content, bilingual strings. Use `Grep`. |
| `ocs-tools-spec-v1.1.md` | 59 KB / 1,025 lines | Read the §-index at the top of the file to find what you need. |
| `HUB_AND_DEMOS_PLAN_2026-05-16.md` | 38 KB | Read the §-index at the top. |
| Tool HTML files >40 KB | varies | `compute-in-space`, `constraint-stacker`, `orbital-dynamics`, `cmd-explorer`, `lisa-emri`, `bekenstein-landauer`, `radio-seti`, `bz-kardashev` — grep for specific functions or sections. |

**Images / binaries** — never read: `og-image.png` (204 KB), `apple-touch-icon.png` (23 KB), `favicon.ico`.

---

## Deployment

Files are served as-is — flat URL structure (`/proposal_*.html`, `/tools/*.html`). Do not introduce subdirectories for proposals; it would break external citations. The canonical domain is `omegacentauri.me` (not `omegacentaurisociety.org`).
