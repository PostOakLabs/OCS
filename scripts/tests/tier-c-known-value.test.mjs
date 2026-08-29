// tier-c-known-value.test.mjs — OCS-TEST-COVERAGE-SPEC.md v1 §3 Tier C, layer 2.
//
// Round-trip (tier-c-hash-roundtrip.test.mjs) proves hash serialization is
// lossless but says nothing about whether the number is *right*. This file
// asserts a fixed set of tools compute a documented correct answer for a
// known input. v1 scope (§6 non-goal: not all 31 manifest tools have a
// fixture yet — this is the gap, flagged not hidden):
//
//   - 5 tools whose page script is "vendored verbatim" from an already
//     §18-proven ocs-mcp-worker kernel (apophis-flyby-geometry,
//     roman-microlensing, gwtc-remnant-classifier, jwst-accretion-ledger,
//     bayes-factor-router): fixtures are copied from the worker's own
//     proven kernels/fixtures/*.fixtures.json, so this run is a drift
//     detector between the two copies, not a fresh physics claim.
//   - constraint-stacker: reuses the existing ChainGraph artifact fixture.
//   - bekenstein-landauer, kardashev-meter, energy-translator: fixtures
//     are independently hand-derived from the published closed-form
//     formula (Bekenstein 1973 / Landauer 1961 / Lloyd 2000 / Sagan 1973 /
//     SI unit definitions), not generated from the tool's own code.
//   - imbh-fuel-budget: pure calc() fn, fixture independently re-derives
//     the page's own stated Bondi accretion closed form.
//   - flyby-survival, flyby-survival-simulator: no buildArtifact(), and
//     their compute paths (simulate() / binResult()) run an internal Monte
//     Carlo. Both are fully deterministic at a fixed seed (20260717,
//     hardcoded for flyby-survival; passed explicitly for the simulator),
//     so their fixtures are SEED-FROZEN — they assert reproducibility of
//     the fixed-seed output, not independent correctness of the MC terms
//     (the closed-form terms in each output, e.g. lamYr/vorbKms/rinflAU,
//     are independently checkable and documented as such in the fixture).
//
// OCS-FIXWAVE.md FW-1 (2026-08) added the imbh-fuel-budget /
// flyby-survival / flyby-survival-simulator groups — previously flagged
// "harness-undriveable" only because none of the three emit a ChainGraph
// artifact (no buildArtifact()), which made them invisible to
// schema-validate.mjs's coverage gate. All three turned out to have a
// directly-callable compute entrypoint once inspected, so known-value
// coverage was still achievable; they remain outside schema-validate.mjs's
// scope (that gate only tracks artifact-QUALIFIED tools) and stay
// documented as value-only, non-hash-bound fixtures.
//
// Remaining 20 of 28 artifact-qualified manifest tools have round-trip
// coverage only — OCS-FIXWAVE.md FW-2..FW-5, tracked by schema-validate.mjs's
// ALLOWLIST (shrinks as each session lands).
//
// Run: node --test scripts/tests/tier-c-known-value.test.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');
const FIXTURES_DIR = resolve(HERE, '..', 'fixtures');

const manifest = JSON.parse(readFileSync(resolve(REPO, 'tools/data/tools-manifest.json'), 'utf8'));
const MEASUREMENTS_SRC = readFileSync(resolve(REPO, 'tools/data/measurements.js'), 'utf8');

// A page's own <script src="..."> tags are its declared dependencies (e.g.
// lib/imbh-constraints.core.js). The browser loads them before the inline
// code runs; the sandbox has no loader, so resolve and prepend them here in
// document order. Local, same-directory-relative paths only — nothing is
// fetched, matching the site's no-network rule. measurements.js is handled
// separately below because it predates this and some pages reference it in
// prose rather than a tag.
function externalScriptSources(html, baseDir) {
  const out = [];
  const re = /<script\b[^>]*\bsrc\s*=\s*["']([^"']+)["'][^>]*>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const src = m[1];
    if (/^(https?:)?\/\//i.test(src)) continue;      // no remote deps to load
    if (/measurements\.js$/.test(src)) continue;      // injected separately
    if (/prefill\.js$/.test(src)) continue;           // UI-only, no compute surface
    try {
      out.push(readFileSync(resolve(REPO, baseDir, src), 'utf8'));
    } catch {
      // A missing local dependency is the page's problem to surface at
      // runtime, not this harness's; the inline code will throw if it
      // actually needed it.
    }
  }
  return out;
}

function inlineScripts(html) {
  const scripts = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const attrs = m[1] || '';
    const body = m[2] || '';
    if (/\bsrc\s*=/i.test(attrs)) continue;
    const typeMatch = attrs.match(/\btype\s*=\s*["']?([^"'\s>]+)/i);
    const type = typeMatch ? typeMatch[1].toLowerCase() : '';
    if (type && !['text/javascript', 'application/javascript', 'module'].includes(type)) continue;
    if (type === 'module') continue;
    if (!body.trim()) continue;
    scripts.push(body);
  }
  return scripts;
}

function makeFakeEl() {
  const store = { value: '', textContent: '', innerHTML: '', firstChild: null, classList: { add(){}, remove(){}, toggle(){return false}, contains(){return false} }, style: {}, dataset: {} };
  return new Proxy(store, {
    get(target, prop) {
      if (Object.prototype.hasOwnProperty.call(target, prop)) return target[prop];
      return () => makeFakeEl();
    },
    set(target, prop, value) { target[prop] = value; return true; },
  });
}

function makeSandbox() {
  const location = { hash: '', href: 'https://omegacentauri.me/tools/probe.html' };
  const history = { replaceState(_s, _t, url) {
    const h = String(url || ''); const i = h.indexOf('#');
    location.hash = i >= 0 ? h.slice(i) : h;
  } };
  // id-cached elements: a real DOM returns the SAME node for repeated
  // getElementById(id) calls, so a value one function writes (e.g.
  // updateMetrics() setting #verdict-text.textContent) is visible to a
  // later read (e.g. render() collecting it into _toolArtifactData). The
  // groups above never touch the DOM, so a fresh-element-per-call stub was
  // fine for them; FW-3's buildArtifact()-driven tools need the cache.
  const elCache = new Map();
  const document = {
    getElementById(id) { if (!elCache.has(id)) elCache.set(id, makeFakeEl()); return elCache.get(id); },
    querySelector() { return makeFakeEl(); },
    querySelectorAll() { return []; },
    createElement() { return makeFakeEl(); },
    createElementNS() { return makeFakeEl(); },
    addEventListener() {},
    body: makeFakeEl(),
    documentElement: makeFakeEl(),
  };
  const sandbox = {
    location, history, document,
    navigator: { clipboard: { writeText() { return Promise.resolve(); } } },
    addEventListener() {}, removeEventListener() {},
    matchMedia() { return { matches: false, addEventListener() {}, addListener() {} }; },
    isSecureContext: false,
    requestAnimationFrame(fn) { return setTimeout(fn, 0); }, cancelAnimationFrame() {},
    console, setTimeout, clearTimeout, setInterval, clearInterval,
    URL, URLSearchParams, Blob, TextEncoder, TextDecoder, crypto: globalThis.crypto,
    performance: { now: () => 0 }, screen: { width: 1280, height: 800 }, devicePixelRatio: 1,
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  return sandbox;
}

function loadTool(toolId, extraCode = '') {
  const entry = manifest.tools[toolId];
  const abs = resolve(REPO, entry.path);
  const html = readFileSync(abs, 'utf8');
  const sandbox = makeSandbox();
  const usesMeasurements = /measurements\.js/.test(html);
  const deps = externalScriptSources(html, dirname(entry.path));
  const code = (usesMeasurements ? MEASUREMENTS_SRC + '\n' : '')
    + (deps.length ? deps.join('\n;\n') + '\n;\n' : '')
    + inlineScripts(html).join('\n;\n')
    // extraCode runs in the SAME vm.Script compilation as the page's inline
    // scripts, so it shares their top-level `let`/`const` lexical scope
    // (invisible from outside the script otherwise — a page's module-level
    // `state` never becomes a sandbox/global property, as noted above).
    + (extraCode ? '\n;\n' + extraCode : '');
  new vm.Script(code, { filename: entry.path }).runInContext(sandbox, { timeout: 5000 });
  return sandbox;
}

// ---- Group 1: tools whose compute() is vendored verbatim from a proven kernel ----
const KERNEL_VENDORED_TOOLS = [
  'apophis-flyby-geometry', 'roman-microlensing', 'gwtc-remnant-classifier',
  'jwst-accretion-ledger', 'bayes-factor-router',
];

test('tier-c known-value — kernel-vendored compute() matches proven fixtures', async (t) => {
  for (const toolId of KERNEL_VENDORED_TOOLS) {
    const fixturePath = resolve(FIXTURES_DIR, `${toolId}.fixtures.json`);
    const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
    const sandbox = loadTool(toolId);
    assert.equal(typeof sandbox.compute, 'function', `${toolId}: expected a top-level compute() function`);

    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, () => {
        const raw = sandbox.compute({ execution_backend: 'js', input_parameters: c.input });
        const rawPayload = raw && raw.output_payload ? raw.output_payload : raw;
        // Objects returned from inside the vm context belong to a different
        // realm (own Object.prototype) than the JSON.parse'd fixture, which
        // fails assert.deepEqual's prototype-identity check even when every
        // own property matches. Round-trip through JSON to normalize both
        // sides into plain main-realm objects before comparing.
        const actual = JSON.parse(JSON.stringify(rawPayload));
        for (const [key, expectedVal] of Object.entries(c.expected)) {
          const actualVal = actual[key];
          if (typeof expectedVal === 'number') {
            assert.ok(typeof actualVal === 'number' && Number.isFinite(actualVal),
              `${toolId}/${c.name}: field '${key}' expected number, got ${JSON.stringify(actualVal)}`);
            const tol = Math.max(1e-6, Math.abs(expectedVal) * 1e-3);
            assert.ok(Math.abs(actualVal - expectedVal) <= tol,
              `${toolId}/${c.name}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
          } else if (Array.isArray(expectedVal)) {
            assert.deepEqual(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' array mismatch`);
          } else if (typeof expectedVal === 'object' && expectedVal !== null) {
            assert.deepEqual(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' object mismatch`);
          } else {
            assert.equal(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' expected ${JSON.stringify(expectedVal)}, got ${JSON.stringify(actualVal)}`);
          }
        }
      });
    }
  }
});

// ---- Group 2: pure-formula fixtures (bekenstein-landauer, kardashev-meter, energy-translator) ----
const PURE_FN_TOOLS = ['bekenstein-landauer', 'kardashev-meter', 'energy-translator'];

// ---- Group 2b: FW-2 pure-formula fixtures, hand-derived from each page's own
// stated closed-form physics (Bardeen shadow radius, virial+Gultekin M-sigma,
// Einstein radius/Dominik-Sahu, 2/(3*sqrt(3)) LOS-max, Plummer profile) ----
const FW2_PURE_FN_TOOLS = [
  'velocity-dispersion', 'astrometric-microlensing', 'pulsar-accel-mapper', 'dark-cluster',
];

test('tier-c known-value — FW-2 independently-derived closed-form fixtures', async (t) => {
  for (const toolId of FW2_PURE_FN_TOOLS) {
    const fixturePath = resolve(FIXTURES_DIR, `${toolId}.fixtures.json`);
    const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
    const sandbox = loadTool(toolId);

    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, () => {
        assert.equal(typeof sandbox[c.fn], 'function', `${toolId}: expected top-level function '${c.fn}'`);
        const actual = sandbox[c.fn](...c.args);
        const tol = c.tolerance ?? 1e-9;
        assert.ok(Math.abs(actual - c.expected) <= tol * Math.max(1, Math.abs(c.expected)),
          `${toolId}/${c.name}: ${c.fn}(${c.args.map((a) => JSON.stringify(a)).join(',')}) expected ${c.expected}, got ${actual}`);
      });
    }
  }
});

// ---- Group 2c: shadow-imaging — no standalone pure fn (formula lives inside
// calculate()), so this drives the tool exactly like the real page: set the
// URL hash, call loadHash() (which triggers calculate() and populates
// window._toolArtifactData), and assert on that payload. ----
test('tier-c known-value — shadow-imaging hash-driven closed form', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'shadow-imaging.fixtures.json'), 'utf8'));
  for (const c of fixture.cases) {
    await t.test(`shadow-imaging / ${c.name}`, () => {
      const sandbox = loadTool('shadow-imaging');
      sandbox.location.hash = `#lm=${c.input.lm}&d=${c.input.d_kpc}`;
      sandbox.loadHash();
      const out = sandbox.window._toolArtifactData.output;
      for (const [key, expectedVal] of Object.entries(c.expected)) {
        if (typeof expectedVal === 'number') {
          const tol = Math.max(1e-6, Math.abs(expectedVal) * 1e-6);
          assert.ok(Math.abs(out[key] - expectedVal) <= tol,
            `shadow-imaging/${c.name}: field '${key}' expected ~${expectedVal}, got ${out[key]}`);
        } else {
          assert.equal(out[key], expectedVal, `shadow-imaging/${c.name}: field '${key}' expected ${expectedVal}, got ${out[key]}`);
        }
      }
    });
  }
});

test('tier-c known-value — independently-derived closed-form fixtures', async (t) => {
  for (const toolId of PURE_FN_TOOLS) {
    const fixturePath = resolve(FIXTURES_DIR, `${toolId}.fixtures.json`);
    const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
    const sandbox = loadTool(toolId);

    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, () => {
        assert.equal(typeof sandbox[c.fn], 'function', `${toolId}: expected top-level function '${c.fn}'`);
        const actual = sandbox[c.fn](...c.args);
        const tol = c.tolerance ?? 1e-9;
        assert.ok(Math.abs(actual - c.expected) <= tol * Math.max(1, Math.abs(c.expected)),
          `${toolId}/${c.name}: ${c.fn}(${c.args.join(',')}) expected ${c.expected}, got ${actual}`);
      });
    }
  }
});

// ---- Group 3b: harness-undriveable tools (no buildArtifact(), pure/seeded
// compute entrypoints) — OCS-FIXWAVE.md FW-1 ----
const PURE_FN_UNDRIVEABLE_TOOLS = ['imbh-fuel-budget'];

test('tier-c known-value — undriveable-but-pure-fn tools', async (t) => {
  for (const toolId of PURE_FN_UNDRIVEABLE_TOOLS) {
    const fixturePath = resolve(FIXTURES_DIR, `${toolId}.fixtures.json`);
    const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
    const sandbox = loadTool(toolId);
    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, () => {
        assert.equal(typeof sandbox[c.fn], 'function', `${toolId}: expected top-level function '${c.fn}'`);
        const actual = sandbox[c.fn](...c.args);
        for (const [key, expectedVal] of Object.entries(c.expected)) {
          const actualVal = actual[key];
          if (typeof expectedVal === 'number') {
            const tol = Math.max(1e-6, Math.abs(expectedVal) * (c.tolerance ?? 1e-9));
            assert.ok(Math.abs(actualVal - expectedVal) <= tol,
              `${toolId}/${c.name}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
          } else {
            assert.equal(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' expected ${JSON.stringify(expectedVal)}, got ${JSON.stringify(actualVal)}`);
          }
        }
      });
    }
  }
});

// ---- Group 3c: flyby-survival — seed-frozen internal Monte Carlo (fixed
// seed hardcoded in simulate(), reproducibility not independent correctness
// for tDiffYr/pen; the other fields are closed-form) ----
test('tier-c known-value — flyby-survival seed-frozen simulate()', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'flyby-survival.fixtures.json'), 'utf8'));
  const sandbox = loadTool('flyby-survival');
  assert.equal(typeof sandbox.simulate, 'function', 'flyby-survival: expected simulate()');
  for (const c of fixture.cases) {
    await t.test(`flyby-survival / ${c.name}`, () => {
      const actual = sandbox.simulate(...c.args);
      for (const [key, expectedVal] of Object.entries(c.expected)) {
        const tol = Math.max(1e-6, Math.abs(expectedVal) * (c.tolerance ?? 1e-9));
        assert.ok(Math.abs(actual[key] - expectedVal) <= tol,
          `flyby-survival/${c.name}: field '${key}' expected ~${expectedVal}, got ${actual[key]}`);
      }
    });
  }
});

// ---- Group 3d: flyby-survival-simulator — seed-frozen binResult() (rnd/mf
// are non-JSON args, reconstructed here exactly as the fixture records) ----
test('tier-c known-value — flyby-survival-simulator seed-frozen binResult()', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'flyby-survival-simulator.fixtures.json'), 'utf8'));
  const sandbox = loadTool('flyby-survival-simulator');
  assert.equal(typeof sandbox.binResult, 'function', 'flyby-survival-simulator: expected binResult()');
  assert.equal(typeof sandbox.makeRng, 'function', 'flyby-survival-simulator: expected makeRng()');
  assert.equal(typeof sandbox.remnantMF, 'function', 'flyby-survival-simulator: expected remnantMF()');
  for (const c of fixture.cases) {
    await t.test(`flyby-survival-simulator / ${c.name}`, () => {
      const rnd = sandbox.makeRng(c.seed);
      const mf = sandbox.remnantMF(c.mf_args.fbh, c.mf_args.mbhPertMsun);
      const a = c.binResult_args;
      const actual = sandbox.binResult(a.mbhMsun, a.sigmaKms, a.nstarPc3, a.eCross, a.aAU, a.nTrials, rnd, mf, a.adiab);
      for (const [key, expectedVal] of Object.entries(c.expected)) {
        const tol = Math.max(1e-6, Math.abs(expectedVal) * (c.tolerance ?? 1e-9));
        assert.ok(Math.abs(actual[key] - expectedVal) <= tol,
          `flyby-survival-simulator/${c.name}: field '${key}' expected ~${expectedVal}, got ${actual[key]}`);
      }
    });
  }
});

// ---- Group 4: FW-3 buildArtifact()-driven tools (OCS-FIXWAVE.md FW-3) ----
// Unlike constraint-stacker (module-level `const state` + a dedicated
// loadStateFromHash()), these five tools drive their module-level `let
// state` through the page's own hash-parsing entrypoint plus its normal
// render()/compute() cycle — the same path a browser takes on page load.
// Golden cases were hand-derived from each tool's own stated closed-form
// physics (Bardeen-Press-Teukolsky ISCO, Blandford-Znajek split-monopole
// power, flat/curved-w0 Friedmann-equation distances, chirp mass, ADAF SED
// vs ωCen observational limits) — see scripts/fixtures/<tool>.fixtures.json
// case comments in git history / OCS-FIXWAVE.md FW-3 board note for the
// derivation. Two tools needed harness accommodations, both noted inline
// at their call site below.
const STATEFUL_ARTIFACT_TOOLS = [
  { toolId: 'adaf-sed-modeler', extraSync: true },
  { toolId: 'bz-kardashev', extraSync: false },
  { toolId: 'gw-horizon-plotter', extraSync: true },
  { toolId: 'qpo-mass-spin', extraSync: false, computeFn: 'compute' },
];

test('tier-c known-value — FW-3 stateful buildArtifact() tools', async (t) => {
  for (const { toolId, extraSync, computeFn } of STATEFUL_ARTIFACT_TOOLS) {
    const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, `${toolId}.fixtures.json`), 'utf8'));
    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, async () => {
        const sandbox = loadTool(toolId);
        assert.equal(typeof sandbox.buildArtifact, 'function', `${toolId}: expected buildArtifact()`);
        assert.equal(typeof sandbox.loadHash, 'function', `${toolId}: expected loadHash()`);
        sandbox.location.hash = '#' + c.hash;
        sandbox.loadHash();
        if (extraSync && typeof sandbox.syncSliders === 'function') sandbox.syncSliders();
        if (computeFn) sandbox[computeFn]();
        else sandbox.render();
        const artifact = await sandbox.buildArtifact();
        const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
        for (const [key, expectedVal] of Object.entries(c.expected)) {
          const actualVal = actualPayload[key];
          if (typeof expectedVal === 'number') {
            assert.ok(typeof actualVal === 'number' && Number.isFinite(actualVal) === Number.isFinite(expectedVal),
              `${toolId}/${c.name}: field '${key}' expected number ~${expectedVal}, got ${JSON.stringify(actualVal)}`);
            const tol = Math.max(1e-6, Math.abs(expectedVal) * 1e-6);
            assert.ok(Math.abs(actualVal - expectedVal) <= tol || (actualVal === expectedVal),
              `${toolId}/${c.name}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
          } else {
            assert.equal(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' expected ${JSON.stringify(expectedVal)}, got ${JSON.stringify(actualVal)}`);
          }
        }
      });
    }
  }
});

// cosmology-calculator's loadHash() RETURNS a partial {z,H0,Om,OL,w} object
// instead of mutating `state` itself (the real Object.assign(state,
// fromHash) happens in the page's DOMContentLoaded handler, which never
// fires in this harness). Reaching that assign requires code sharing the
// same vm.Script lexical scope as the page's own top-level `let state` —
// loadTool()'s extraCode param exists for exactly this.
test('tier-c known-value — cosmology-calculator (buildArtifact via hash + explicit state assign)', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'cosmology-calculator.fixtures.json'), 'utf8'));
  const glue = `
    window.__cgDrive = function(hashStr) {
      location.hash = '#' + hashStr;
      const fromHash = loadHash();
      if (fromHash) Object.assign(state, fromHash);
      syncSliders();
      render();
    };
  `;
  for (const c of fixture.cases) {
    await t.test(`cosmology-calculator / ${c.name}`, async () => {
      const sandbox = loadTool('cosmology-calculator', glue);
      assert.equal(typeof sandbox.__cgDrive, 'function', 'cosmology-calculator: glue driver failed to install');
      sandbox.__cgDrive(c.hash);
      const artifact = await sandbox.buildArtifact();
      const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
      assert.deepEqual(actualPayload, c.expected,
        `cosmology-calculator/${c.name}: output_payload does not match hand-derived fixture`);
    });
  }
});

// ---- Group 5: FW-5 tools (OCS-FIXWAVE.md FW-5) ----
// great-filter, infall-survival: hand-derived closed-form (log-sum arithmetic /
// GR horizon formulas), independently reimplemented and cross-checked exactly
// against the page in the FW-5 board session. Both set window._toolArtifactData
// synchronously from render()/loadHash() and expose a sync buildArtifact() that
// reads it back (execution_hash filled separately by renderArtifact() in the
// live page) -- drive the same way here.
const FW5_SYNC_ARTIFACT_TOOLS = ['great-filter', 'infall-survival'];

test('tier-c known-value — FW-5 hand-derived closed-form (sync _toolArtifactData)', async (t) => {
  for (const toolId of FW5_SYNC_ARTIFACT_TOOLS) {
    const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, `${toolId}.fixtures.json`), 'utf8'));
    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, () => {
        const sandbox = loadTool(toolId);
        sandbox.location.hash = '#' + c.hash;
        sandbox.loadHash();
        if (typeof sandbox.render === 'function') sandbox.render();
        else if (typeof sandbox.calculate === 'function') sandbox.calculate();
        const actual = JSON.parse(JSON.stringify(sandbox.window._toolArtifactData.output));
        for (const [key, expectedVal] of Object.entries(c.expected)) {
          const actualVal = actual[key];
          if (typeof expectedVal === 'number') {
            const tol = Math.max(1e-6, Math.abs(expectedVal) * 1e-6);
            assert.ok(Math.abs(actualVal - expectedVal) <= tol,
              `${toolId}/${c.name}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
          } else {
            assert.equal(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' expected ${JSON.stringify(expectedVal)}, got ${JSON.stringify(actualVal)}`);
          }
        }
      });
    }
  }
});

// evidence-ledger, anisotropy-degeneracy-explorer: both expose an async
// buildArtifact() that recomputes entirely from `state` (no render() call
// needed) -- drive via loadHash() + buildArtifact() directly, same pattern as
// FW-3's cosmology-calculator/adaf-sed-modeler group above. evidence-ledger's
// cases are hand-derived Bayesian log-odds; anisotropy-degeneracy-explorer's
// are seed-independent but numerically-integrated (frozen, see fixture note).
const FW5_ASYNC_BUILDARTIFACT_TOOLS = ['evidence-ledger', 'anisotropy-degeneracy-explorer'];

test('tier-c known-value — FW-5 async buildArtifact() tools', async (t) => {
  for (const toolId of FW5_ASYNC_BUILDARTIFACT_TOOLS) {
    const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, `${toolId}.fixtures.json`), 'utf8'));
    for (const c of fixture.cases) {
      await t.test(`${toolId} / ${c.name}`, async () => {
        const sandbox = loadTool(toolId);
        sandbox.location.hash = '#' + c.hash;
        sandbox.loadHash();
        const artifact = await sandbox.buildArtifact();
        const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
        for (const [key, expectedVal] of Object.entries(c.expected)) {
          const actualVal = actualPayload[key];
          if (typeof expectedVal === 'number') {
            const tol = Math.max(1e-6, Math.abs(expectedVal) * 1e-6);
            assert.ok(Math.abs(actualVal - expectedVal) <= tol,
              `${toolId}/${c.name}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
          } else {
            assert.equal(actualVal, expectedVal, `${toolId}/${c.name}: field '${key}' expected ${JSON.stringify(expectedVal)}, got ${JSON.stringify(actualVal)}`);
          }
        }
      });
    }
  }
});

// drake-monte-carlo: SEED-FROZEN (see fixture note). schedule() wraps
// runMC()/render/_toolArtifactData assignment in a setTimeout debounce; drive
// the underlying calls directly and synchronously via glue sharing the page's
// lexical scope (same technique as cosmology-calculator's __cgDrive above).
test('tier-c known-value — drake-monte-carlo seed-frozen runMC()', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'drake-monte-carlo.fixtures.json'), 'utf8'));
  const glue = `
    window.__driveMC = function(hashStr) {
      location.hash = '#' + hashStr;
      loadHash();
      runMC();
      window._toolArtifactData = { policy: { nSamples: state.nSamples, preset: state.preset, priors: state.priors, seed: (state.seed || 1) }, output: { p_alone: state.meta?.pAlone || null, p_less1: state.meta?.pLess1 || null, median_log10N: state.meta?.median || null } };
    };
  `;
  for (const c of fixture.cases) {
    await t.test(`drake-monte-carlo / ${c.name}`, () => {
      const sandbox = loadTool('drake-monte-carlo', glue);
      assert.equal(typeof sandbox.__driveMC, 'function', 'drake-monte-carlo: glue driver failed to install');
      sandbox.__driveMC(c.hash);
      const actual = JSON.parse(JSON.stringify(sandbox.window._toolArtifactData.output));
      for (const [key, expectedVal] of Object.entries(c.expected)) {
        const actualVal = actual[key];
        const tol = Math.max(1e-9, Math.abs(expectedVal) * 1e-9);
        assert.ok(Math.abs(actualVal - expectedVal) <= tol,
          `drake-monte-carlo/${c.name}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
      }
    });
  }
});

// ---- Group 3: constraint-stacker (existing ChainGraph artifact fixture) ----
test('tier-c known-value — constraint-stacker matches existing artifact fixture', async () => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'constraint-stacker.artifact.json'), 'utf8'));
  const sandbox = loadTool('constraint-stacker');
  assert.equal(typeof sandbox.buildArtifact, 'function', 'constraint-stacker: expected buildArtifact()');
  assert.equal(typeof sandbox.loadStateFromHash, 'function', 'constraint-stacker: expected loadStateFromHash()');

  // `state` is a module-level `const`, invisible outside the vm-loaded
  // script (top-level const/let never become globalThis properties, in a
  // vm context exactly as in a browser). Drive it the same way the page
  // itself does — through the hash — rather than reaching in directly.
  const ip = fixture.policy_parameters.input_parameters;
  sandbox.location.hash = `#epsilon=${ip.epsilon}&rho=${ip.rho}&show=${encodeURIComponent(ip.show)}`;
  sandbox.loadStateFromHash();

  const artifact = await sandbox.buildArtifact();
  const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
  assert.deepEqual(actualPayload, fixture.output_payload,
    'constraint-stacker: output_payload does not match the proven fixture for the same inputs');
});
