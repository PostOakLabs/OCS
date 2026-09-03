# Contributing to the Omega Centauri Society tools

Thanks for considering a contribution. The OCS catalogue is a solo-maintained
science portal at omegacentauri.me, and most updates take one of a few well-defined
shapes. This guide walks each one.

Triple-licensing reminder before you start: **code is MIT, prose is CC BY 4.0,
curated data tables are CC0 1.0.** See the three `LICENSE-*.md` files in the
repository root. Submitting a contribution means you're releasing it under
whichever of those licenses fits the kind of change you're making.

---

## Adding a new IMBH mass measurement

When a new paper publishes an IMBH mass estimate or limit for Omega Centauri (or
any cluster represented in the comparator), the canonical place to add it is
`tools/data/measurements.js`. *Do not* hardcode the value into any individual
tool — they all read from this shared sibling file.

1. Open `tools/data/measurements.js`.
2. Find the `imbh:` array (for IMBH measurements) or `clusters:` /
   `pulsars:` for the others.
3. Append a new object following the existing schema. For IMBH measurements
   the schema is (match the fields already used by the other entries in the
   `imbh:` array):

```javascript
{
  id: "lastname2026",          // short stable identifier
  year: 2026,
  authors: "Lastname et al.",
  value: 12000,                 // central value or limit, M_sun. null for
                                // no-evidence or parameter-dependent
  uncertaintyLo: 2000,          // for symmetric error bars (lower extent), M_sun
  uncertaintyHi: 3000,          // upper extent, M_sun
  limitType: "detection",       // "detection" | "upper" | "lower" |
                                // "noEvidence" | "parameterDependent"
  sigma: null,                  // confidence in sigma if applicable
  confidenceLevel: null,        // optional, fractional (e.g. 0.90 for 90% CL)
  method: "kinematics",         // "kinematics" | "propermotion" | "timing" |
                                // "nbody" | "accretion"
  methodLabel: "Stellar kinematics (instrument)",  // human-readable
  journal: "Nature 642:123",
  doi: "10.1038/s41586-026-...",   // DOI string, no leading URL
  url: null,                    // optional fallback URL
  notes: "One- or two-sentence summary; appears in tool detail cards."
}
```

4. Update `meta.lastUpdated` to today's ISO date (`YYYY-MM-DD`).
5. Bump the `Version:` line in the file header of any tool whose displayed
   data has changed (typically constraint-stacker, imbh-timeline, and
   cluster-comparator).
6. Open a PR. Include the DOI in the description.

By contributing the row, you agree to release it under CC0 (the original
paper's authors retain their own copyright; the citation stays in the row).

## Correcting a hardcoded physical value

If you find a numerical constant in a tool file that needs correction (e.g., a
better measurement of a cluster's half-light radius, an updated coefficient on
the M-σ relation):

1. Edit the value in the relevant tool file.
2. Add a comment immediately above noting the source: `// from <citation>, year`.
3. Update the file's `Last updated:` line in its header comment block.
4. If the constant is shared across multiple tools (e.g., a calculation
   duplicated character-for-character across several tool files — `grep` the
   function or constant name across `tools/*.html` to find every consumer),
   update **all** consumer tools in the same PR.
5. Open the PR with a one-line explanation and the source citation.

## Adding a new language

Tools launch in English only. The path to add a second language is intentionally
made cheap:

1. Find the `const STRINGS = { ... }` object near the top of each tool file
   (the site-wide convention: every tool stores its user-facing string
   literals in a single JS object, so a translation only ever touches that
   object).
2. Add a new key for the language code (e.g., `STRINGS.zh = { ... }` for
   Chinese) with translated values matching the existing English keys.
3. Wire a language toggle (see how the main `index.html` handles the `lang-zh`
   body class for the existing English/Chinese site toggle — copy that pattern).
4. Test in Chrome and Firefox; verify text fits in the slider labels and badge
   pills.
5. Submit one PR per language, even if the translations were generated together —
   makes review tractable.

## Code style

- **Vanilla JavaScript only.** No npm, no build step, no transpilation, no
  TypeScript, no React. The whole site is statically served.
- **Inline everything.** Each tool is a single self-contained HTML file. The
  one exception is `tools/data/measurements.js`, the shared reference-data
  file (see "What goes in `tools/data/measurements.js`" below).
- **No network calls at runtime.** No `fetch`, no XHR, no dynamic import over
  the network. Google Fonts is the only exception (already used by the rest of
  the site). Tools must work when opened directly from disk on `file://`.
- **No PII.** Forms that submit data, identity localStorage, cookies, and
  analytics are not allowed. Non-identity localStorage (e.g., "About panel
  collapsed/expanded") is permitted.
- **CSS palette and typography:** copy the `:root` CSS-variable block verbatim
  from an existing tool (e.g. `tools/velocity-dispersion.html`) into every new
  tool. Do not invent new color values.
- **URL hash state:** every interactive tool must serialize its current state
  to the URL hash on every interaction and restore from the hash on page load.
  Copy the `loadHash()`/`saveHash()` pattern already implemented in an
  existing tool rather than writing a new one.

## Local validation hook

`scripts/pre-push` mirrors Job 1 (Validate) in `deploy.yml` — count drift, broken
links, stranded pages, JS syntax, hash lint, schema. Git cannot install hooks from
the repository itself, so run this once per clone:

```
cp scripts/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

Edit `scripts/pre-push` (the tracked copy), never `.git/hooks/pre-push`, then re-run
the command above. To bypass in an emergency: `git push --no-verify`.

## Pull-request checklist

Before opening a PR, confirm:

- [ ] Any physics is verified against a cited primary source.
- [ ] Epistemic tier badge(s) are present and correct (🔬 established physics /
      ⚠ observationally debated / ⚠ theoretical / ✦ engineering fiction — copy
      the badge markup from an existing tool).
- [ ] URL hash state is implemented (read on load, write on every interaction).
- [ ] File-header comment block at the top of the file is current (version
      bumped, "Last updated" matches the commit date, license trio declared,
      data sources listed — copy the block layout from an existing tool file).
- [ ] Tested in Chrome and Firefox at desktop width and at 720 px.
- [ ] A new tool page has a card in `tools/index.html`, and any new page is
      linked from a hub — `python3 scripts/check-orphans.py` passes.
- [ ] If a shared utility function was modified, all consumer tools updated
      in the same PR.
- [ ] If a hardcoded measurement was modified, the change has been migrated to
      `tools/data/measurements.js` instead, and consumer tools updated to read
      from there.

## What goes in `tools/data/measurements.js`

That file is the single source of truth for **curated reference tables only** —
IMBH measurements, cluster properties, OC pulsar inventory. It is loaded via a
single `<script src>` tag from tools that need it. Adding a new schema section
(e.g., a "compute substrate calibration" table) changes a contract that every
consumer tool relies on — open an issue proposing the new section's shape
before sending a direct PR.

## Reporting an error

Bug reports, factual corrections, and "this slider does the wrong thing" issues
are all welcome. Open an issue or email the OCS maintainer (contact details on
the main site). Include the URL with hash state (the tools serialise state into
the hash on every interaction precisely so a bug report can be reproduced).

## Style of correspondence

Brief, technical, falsifiable. The site's whole stance is epistemic honesty
about what is established physics vs. what is speculative engineering — please
keep correspondence in that voice. Tier-correct disagreement is welcome; ad
hominem and pseudo-scientific tone-policing are not.
