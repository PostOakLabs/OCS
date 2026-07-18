# OCS — Stranded-Page Audit & Orphan Gate

**Date:** 2026-07-18 · **Branch:** `main` · **Status:** fixes applied, gates green, **not yet committed**

Audit of committed pages in `repo/` versus what the hub pages actually link to, plus the fixes and the new CI gate that stops the drift recurring.

---

## 1. Scope & method

Enumerated every tracked `.html` (`git ls-files "*.html"` → 196 files), extracted internal `href`/`src` targets from the hub pages, and computed reachability.

**Correction to the brief:** `about.html` and `tools.html` do not exist in this repo. The real hub set is `index.html`, `sitemap.html`, `paper.html`, `tools/index.html`.

Result: 196 tracked, 182 reachable, **14 stranded, 0 broken hub links**.

---

## 2. Findings

### 2a. The "6th paper"

`papers/mth-2026.pdf` — 448 KB, dated Jun 10, **zero references anywhere in the repo**. Superseded by `papers/macro-transcension-hypothesis.pdf` (478 KB, Jul 18), which is the one wired into `paper.html`. Left behind by the earlier filename rename.

`papers/source/` confirms five papers and only five: `campaign-paper.tex`, `economics-paper.tex`, `engineered-imbh-paper.tex`, `inward-review.tex`, `mth-paper.tex`. The published count of 5 was correct; only the PDF mirror carried the orphan.

### 2b. Stranded pages

| File | Status | Notes |
|---|---|---|
| `tools/gwtc-remnant-classifier.html` | fully orphaned | zero inbound links repo-wide |
| `tools/jwst-accretion-ledger.html` | fully orphaned | zero inbound; near-name collision with the wired `tools/jwst-accretion.html` |
| `tools/rubin-alert-throughput.html` | fully orphaned | zero inbound |
| `tools/bayes-factor-router.html` | depth-2 only | linked from an orphaned page and one scenario; absent from `tools/index.html` |
| `tools/flyby-survival.html` | depth-2 only | Paper-E cluster; reachable from `engineered-imbh-systems.html` |
| `tools/flyby-survival-simulator.html` | depth-2 only | same |
| `tools/imbh-fuel-budget.html` | depth-2 only | same |
| `psets.html` | island hub | no inbound link from outside its own cluster |
| `pset-1-kinematics.html` … `pset-4-emri.html` | island members | linked only from `psets.html`, itself unreachable |
| `papers/figs/index.html`, `papers/source/index.html` | benign | reached via directory hrefs `/papers/figs/`, `/papers/source/` |

All 19 `workflow-*` and 30 `scenario-*` pages were already wired. Root cause on the seven tools: registry drift in `tools/index.html` from the Paper-E session.

---

## 3. Fixes applied

**Duplicate PDF** — `git rm papers/mth-2026.pdf` (staged).

**Seven tools wired into `tools/index.html`:**

| Tool | Section | Tool # |
|---|---|---|
| `jwst-accretion-ledger` | ⚖ IMBH evidence | 91 |
| `gwtc-remnant-classifier` | ⚖ IMBH evidence | 92 |
| `bayes-factor-router` | ⚖ IMBH evidence | 93 |
| `rubin-alert-throughput` | ⚖ IMBH evidence | 94 |
| `imbh-fuel-budget` | ✦ Speculative compute | 95 |
| `flyby-survival` | ✦ Speculative compute | 96 |
| `flyby-survival-simulator` | ✦ Speculative compute | 97 |

Card descriptions were written from each tool's own `<meta name="description">`, not invented. `python scripts/verify-counts.py --fix` then rebased the section sentinels: evidence 36 → 40, speculative compute 15 → 18.

**psets cluster** — added a `/psets.html` entry to the "Main pages" list in `sitemap.html`, with a description covering all four sets. The four pset pages hang off it, so the whole island is now reachable.

---

## 4. Prevention — `scripts/check-orphans.py`

New strict-zero gate, the mirror of `check-links.py`. That script catches links pointing at files that do not exist; this one catches files that exist but nothing links to. The failure mode it closes is silent: the site builds, deploys, and looks fine.

**Check 1 — reachability.** Breadth-first walk from `index.html` and `sitemap.html` following internal `href`/`src`. Strips `<script>`/`<style>`/comments so runtime-built and commented-out hrefs do not count (mirrors `check-links.py`). Resolves root-relative `/foo.html` and directory links `dir/` → `dir/index.html`. Any tracked `.html` not reached fails.

**Check 2 — tool registry.** Every `tools/*.html` non-hub must be linked *directly* from `tools/index.html`.

Check 2 is the load-bearing one. Transitive reachability alone would **not** have caught the four Paper-E tools: they were reachable at depth 2 from `engineered-imbh-systems.html`, yet missing from the registry that readers and `tools-manifest.json` both treat as canonical. Reachability catches stranded clusters; the registry check catches registry drift. Neither subsumes the other.

Deliberate exceptions live in an `ALLOW` dict, each with a stated reason — currently the two `papers/*/index.html` directory listings and `404.html`.

**Wired into:**
- `.github/workflows/deploy.yml` — "Stranded-page gate", immediately after the broken-link gate in Job 1
- `.git/hooks/pre-push` — now step `[3/6]`, renumbered from `[N/5]`

**Current output:**

```
Scanned 196 HTML files; 196 reachable from index.html, sitemap.html.
[OK] No stranded pages; every tool is in the registry.
```

Full pre-push suite (6 gates) passes.

---

## 5. Open items

- ✅ **R1 — landed.** Branch `fix/stranded-pages-orphan-gate`, single PR carrying the PDF removal, `tools/index.html`, `sitemap.html`, `deploy.yml`, `scripts/check-orphans.py`, and this doc.
- ✅ **R2 — pre-push hook tracked.** Committed as `scripts/pre-push` with an install note in the new "Local validation hook" section of `CONTRIBUTING.md`. `.git/hooks/pre-push` is now an install target, not the master copy.
- ⏸ **R3 — deferred to the next manifest rev.** §6.4 found six of the seven tools already MCP-exposed while index-invisible; the `rubin-alert-throughput` exposure decision rides with the next `tools-manifest.json` revision, not this PR.
- **Tool numbers 91–97 assigned sequentially** after the previous max of 90. The existing numbering already contains duplicates (two "Tool 31"), so it is not a reliable key.

---

## 6. Independent verification (2026-07-18, session 6c4301bd) — all four checks pass

1. **Seven cards:** every card points at an existing file; blurbs match each tool's own `<meta description>` (4–5 of 5 distinctive meta words present per card; misses are word-form drift, not invented content).
2. **`mth-2026.pdf` deletion:** zero references repo-wide (HTML/XML/JSON/MD/JS/YML). Safe.
3. **Counterfactual gate test:** ran `check-orphans.py` against a scratch rebuild of pre-fix HEAD. Check 1 flagged exactly the 8 unreachable pages (psets island of 5 + 3 fully-orphaned tools); Check 2 flagged all 7 unregistered tools including the 4 depth-2 Paper-E ones that reachability alone misses — the "neither check subsumes the other" claim is empirically confirmed. 12 of 14 caught; the 2 `papers/*/index.html` are deliberate ALLOW entries, correctly not flagged. Current tree: 196/196, green.
4. **Manifest cross-check:** v1.3.0 consistent (toolCount 34 = actual, verify-counts green); no manifest tool missing from the index (no reverse drift). Six of the seven were already MCP-exposed while index-invisible — the drift this audit fixed from the other side. Live MCP probe confirms `jwst-accretion-ledger` serves from the worker.

## 7. Recommendations (for the landing session)

- **R1 — Land it.** Branch + single PR with the staged `git rm`, `tools/index.html`, `sitemap.html`, `deploy.yml`, and `scripts/check-orphans.py`; self-merge on green and watch deploy per standing order 8. Include this audit doc in the commit for provenance, then archive it per the auto-archiving policy once ✅ (root stays active-docs-only).
- **R2 — Track the pre-push hook.** Commit the hook body as `scripts/pre-push` (tracked) with a one-line install note (`cp scripts/pre-push .git/hooks/pre-push`) in CONTRIBUTING.md or README; the local-only copy protects nobody else.
- **R3 — `rubin-alert-throughput` manifest decision.** Now the only tool of the seven that is index-visible but MCP-dark. Not drift (manifest is curated, 34 of 107), but make it a deliberate call at the next manifest rev: include (it is deterministic calculator math, fits the catalog pattern) or record the exclusion reason in the manifest `_meta` notes. Recommended: include at next rev, not this PR — keeps this PR mechanical.
- **R4 — Do not renumber tools.** The duplicate "Tool 31" shows ordinal labels are decorative; filename is the key. Leave numbering as-is rather than inviting churn; optionally note in `tools/index.html`'s header comment that numbers are display-only.
