# imbh-constraints

Zero-dependency evidence-aggregation engine for the Omega Centauri intermediate-mass
black hole (IMBH) debate, generalized to any contested-compact-object-mass problem.

Published constraints on the mass of a candidate compact object are heterogeneous: some
are detections with error bars, some are one-sided limits at a stated significance, some
are null results that carry no number at all, and some are curves that only become a
number once you fix a nuisance parameter. This library gives those a single declarative
schema and computes the mass range they jointly allow, including the case where they
allow none.

- **Version** 1.0.0 · **Schema** 1.0 · **Licence** MIT (code), CC0 1.0 (data compilation)
- **Dataset** [`../data/measurements.js`](../data/measurements.js) — curated compilation,
  Noyola 2008 through TRAPUM 2026, every entry DOI-sourced
- **Archive** Zenodo [10.5281/zenodo.20689279](https://doi.org/10.5281/zenodo.20689279) ·
  ASCL [ascl.net/code/v/4787](https://ascl.net/code/v/4787)

## Install / load

No build step, no package manager, no network calls.

**Node 18+, Cloudflare Workers, any ES-module consumer**

```js
import { computeWindow, constraintsFromMeasurements } from './imbh-constraints.mjs';
```

**Browser** (works from `file://`, which is why the core is a classic script — see
[Layout](#layout))

```html
<script src="data/measurements.js"></script>
<script src="lib/imbh-constraints.core.js"></script>
<script>
  const lib = globalThis.IMBHConstraints;
</script>
```

## Quick start

```js
import { computeWindow, constraintsFromMeasurements } from './imbh-constraints.mjs';

const constraints = constraintsFromMeasurements(window); // or an injected scope in Node
const win = computeWindow(constraints, { show: 'propermotion,timing' });

win.lo       // 8200   — Häberle et al. 2024 lower bound
win.hi       // 6000   — Bañares-Hernández et al. 2025 upper limit
win.tension  // true   — lo > hi: these cannot both be right
win.lowSrc   // the full constraint object behind each bound
```

## The constraint schema

A constraint is one published statement about the mass. Required fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | stable identifier, unique within a set |
| `limitType` | enum | see below — the field the engine turns on |
| `method` | enum | `kinematics` · `propermotion` · `timing` · `accretion` · `nbody` |
| `value` | number \| null | M☉, positive; `null` for the types that carry no number |
| `year`, `authors` | | used to attribute bounds in output and verdict strings |

`limitType` encodes the epistemic kind of the statement, and each kind bounds the window
differently:

| `limitType` | Bounds | Why |
|---|---|---|
| `detection` | neither | A central value is consistent with its own error bars. Treating it as a bound would silently discard those errors. |
| `upper` | `hi` | M < value at the quoted significance. |
| `lower` | `lo` | M > value. |
| `noEvidence` | neither | Consistent with zero — distinct from a numerical upper limit, and carries no number to bound with. Baumgardt 2017 is the type case. |
| `parameterDependent` | `hi` | The limit is a curve. It is realized only when the caller supplies the parameters (Chen 2025 JWST: ADAF efficiency ε and ambient density ρ∞). |

Validate before trusting a set. Validation is pure and reports every problem at once
rather than throwing on the first:

```js
const { valid, errors } = validateConstraintSet(constraints);
```

## Tension records are never collapsed

The Häberle 2024 lower bound (≥8,200 M☉) and the Bañares 2025 upper limit (≤6,000 M☉)
are mutually incompatible. Both are current, both are valid, and at least one has
unaccounted systematics — or the central mass is not a point.

When the constraints are unsatisfiable, `computeWindow` returns `tension: true` and
**preserves both bounds and both sources**. It does not average them, take a midpoint,
drop the weaker one, or return an empty window. The incompatibility is the scientific
result, and callers are handed it intact. A caller that needs a single scalar must make
that choice itself and own it.

This is enforced, not merely documented:
[`scripts/tests/lib-imbh-constraints.test.mjs`](../../scripts/tests/lib-imbh-constraints.test.mjs)
asserts no reconciled midpoint is ever produced.

## API

| Export | Purpose |
|---|---|
| `computeWindow(constraints, opts)` | → `{lo, hi, tension, lowSrc, hiSrc}`. `opts`: `show`, `epsilon`, `rho`, `jwst`. Unbounded sides are `null`, never `±Infinity`. |
| `validateConstraint(c)` / `validateConstraintSet(cs)` | schema validation |
| `jwstUpperLimitMsun(eps, rho, opts?)` | the parameter-dependent curve; `null` when inputs define no limit |
| `mSigmaPrediction(sigma_kms?)` | Gültekin 2009 M–σ, context only — never enters the window |
| `computeStackerPayload(policy, constraints)` | the ChainGraph `output_payload` (hashed — byte-exact by contract) |
| `constraintsFromMeasurements(scope?)` | read the shipped compilation |
| `activeConstraints` / `activeLanes` / `normalizeShow` | lane helpers |
| `fmtEnUS` / `fmtMass` / `buildVerdictString` | deterministic formatting (no `Intl`) |
| `LIMIT_TYPES` / `METHODS` / `CONSTANTS` / `JWST_DEFAULTS` | vocabularies and constants |

## Layout

```
imbh-constraints.core.js   all logic; classic script, assigns globalThis.IMBHConstraints
imbh-constraints.mjs       named-export facade over the core — the importable surface
```

One authored copy of the math, two loading paths. The split is a loading constraint, not
a code fork: ES module scripts are fetched under CORS and a `file://` page has an opaque
origin, so `<script type="module">` cannot import anything there. Site architecture rule 3
requires tools to run from `file://`, so pages load the classic core and read the global —
the same pattern `data/measurements.js` already uses across the site. Node imports the
facade and gets real named bindings.

## Consumers

| Consumer | How |
|---|---|
| [`constraint-stacker.html`](../constraint-stacker.html) | full window over all five lanes, plus the hashed ChainGraph artifact |
| [`imbh-evidence-dashboard.html`](../imbh-evidence-dashboard.html) | the proper-motion vs timing conflict |
| `ocs-mcp-worker` `constraint_stacker` tool | via CI parity gate — see below |

The MCP worker's kernel is *guest-legal* (no imports, so it runs unchanged inside the zkVM
guest) and is groth16-proven, so it cannot import this library: editing it would invalidate
its compute proof. The two copies are instead held byte-identical by a CI gate
(`scripts/check-lib-parity.mjs` in the worker repo), which fails the build on any
divergence across the fixture corpus. That is a weaker guarantee than a shared import, and
it is stated plainly rather than papered over.

## Reproducibility

Output is deterministic across runtimes: no `Intl`/`toLocaleString`, no `Date`, no
floating-point-unstable helpers. Payloads are I-JSON clean, so they canonicalize under
RFC 8785 and hash reproducibly.

The published artifact [`../data/anchored-evidence.json`](../data/anchored-evidence.json)
(execution hash `533362…`, RFC3161 + OpenTimestamps anchored) is replayed as a test
fixture. If that test fails, the code and the timestamped public record disagree — that is
not a fixture to update.

## Tests

```
node --test scripts/tests/lib-imbh-constraints.test.mjs
```
