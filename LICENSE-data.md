# Creative Commons Zero v1.0 Universal — Curated Data Tables

**The Omega Centauri Society** — omegacentauri.me
Applies to: the curated measurement tables in `tools/data/measurements.js`.

The Omega Centauri Society has dedicated the contents of this data file to the
public domain by waiving all of its rights to the work worldwide under copyright
law, including all related and neighboring rights, to the extent allowed by law.

You can copy, modify, distribute, and use the data, even for commercial purposes,
all without asking permission.

Full license text: <https://creativecommons.org/publicdomain/zero/1.0/legalcode>
Human-readable summary: <https://creativecommons.org/publicdomain/zero/1.0/>

---

## What this covers

The CC0 dedication applies to the **curated tables** inside `tools/data/measurements.js`:

- The IMBH mass estimate table (`window.OCS_MEASUREMENTS.imbh`)
- The cluster properties table (`window.OCS_MEASUREMENTS.clusters`)
- The Omega Centauri pulsar table (`window.OCS_MEASUREMENTS.pulsars`)
- The metadata block (`window.OCS_MEASUREMENTS.meta`)

These tables are *selections* of measurements from the scientific literature — a
research librarian's job, not a creative one. We dedicate the selection to the
public domain so that academic researchers can reuse the curated tables without
attribution friction.

## What CC0 does NOT do

- It does not waive the rights of the **original paper authors** whose measurements
  populate the tables. Each row includes the original citation (authors, journal, DOI)
  exactly so that re-users can credit the underlying scientific source. The factual
  measurement values themselves are uncopyrightable in most jurisdictions.
- It does not apply to the **JavaScript code wrapper** around the tables (the
  `window.OCS_MEASUREMENTS = { ... }` boilerplate, comments, and helper structure) —
  that is licensed under MIT per [LICENSE-code.md](LICENSE-code.md).
- It does not apply to the **prose notes** in each row's `notes:` field — those are
  CC BY 4.0 per [LICENSE-content.md](LICENSE-content.md).

## Why CC0 specifically

Scientific measurement values are facts. Facts are uncopyrightable in most
jurisdictions. But the *curation and selection* of which measurements to include —
which papers to draw from, how to schema them, what to flag as a detection vs. an
upper limit — arguably is copyrightable. A CC0 dedication on the curated tables
removes any ambiguity for academic re-use while keeping the rest of the site
CC BY 4.0 and the executable code MIT.

## When you contribute a new measurement

Submitting a measurement to `tools/data/measurements.js` (e.g., a newly published
IMBH mass estimate) means you agree to release that addition under CC0. The
original-paper citation stays in the row — that is not yours or ours to license
away — but the curated row itself enters the public domain along with the rest.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the submission path.
