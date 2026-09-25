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

function makeSandbox(presetIds) {
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
  // presetIds: {id: value} pairs seeded into the cache BEFORE the page's
  // own top-level script runs — needed by observing-campaign-planner (FW-4),
  // whose unconditional `loadHash(); calculate();` init call reads
  // document.getElementById('sel-instr').value directly (a real browser
  // initializes a <select> with no explicit "selected" option to its first
  // <option>) before this harness ever gets a chance to set the hash.
  if (presetIds) {
    for (const [id, value] of Object.entries(presetIds)) {
      const el = makeFakeEl();
      el.value = value;
      elCache.set(id, el);
    }
  }
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

function loadTool(toolId, extraCode = '', presetIds = null) {
  // P0-CALC-1: four site-only tools (not MCP-manifest tools) get known-value
  // coverage for their repaired physics; they are resolved by conventional
  // path when absent from the manifest.
  const entry = manifest.tools[toolId] ?? { path: `tools/${toolId}.html` };
  const abs = resolve(REPO, entry.path);
  const html = readFileSync(abs, 'utf8');
  const sandbox = makeSandbox(presetIds);
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

// ---- Group 5: FW-4 buildArtifact()-driven tools (OCS-FIXWAVE.md FW-4) ----
// Unlike FW-3's group, driving these five tools does NOT follow one uniform
// loadHash()->render()/compute()->buildArtifact() sequence — each tool's own
// buildArtifact() was inspected individually (per the FW-4 board note) and
// three different shapes turned up:
//   - detection-forecast, gaia-dr4-forecaster, ir-excess-checker: buildArtifact()
//     is fully self-contained (recomputes everything from module-level `state`
//     and calls the page's own executionHash() internally), so driving is just
//     loadHash() -> await buildArtifact() — no render()/compute() needed.
//   - radio-seti: buildArtifact() reads window._toolArtifactData, which is only
//     populated as a side effect of render() (which also calls compute()
//     internally) — driving is loadHash() -> render() -> await buildArtifact().
//   - observing-campaign-planner: buildArtifact() is SYNCHRONOUS and also reads
//     window._toolArtifactData (populated by calculate()), and execution_hash
//     is computed OUTSIDE buildArtifact() (mirroring the page's own
//     renderArtifact()) via a separate computeExecHash() call. calculate()
//     also reads instr_key from document.getElementById('sel-instr').value
//     directly (not from `state`) — a real browser initializes a <select> to
//     its first <option>, so the harness's id-cached fake DOM must be
//     pre-seeded with 'sel-instr'/'sel-goal' defaults before the page's own
//     top-level `loadHash(); calculate();` init call runs (it runs
//     unconditionally at script-load time, before this test ever touches the
//     sandbox), or that first calculate() throws on an undefined instrument.
// Golden cases were hand-derived from each tool's own stated closed-form
// physics/resource model (detection-forecast: mass-resolution timeline
// scaling; gaia-dr4-forecaster: Keplerian influence-radius kinematic S/N;
// ir-excess-checker: Planck-function IR-excess flux vs SPHEREx/WISE
// sensitivity; radio-seti: the radiometer equation; observing-campaign-planner:
// the virial-mass-estimator resource-budget model) and cross-checked against
// independently-written Node reimplementations, NOT by freezing the tool's
// own live output — see each fixture's "_derivation_note" and OCS-FIXWAVE.md
// FW-4 for the full derivations.
function deepFieldEqual(actualVal, expectedVal, toolId, caseName, key) {
  if (typeof expectedVal === 'number') {
    assert.ok(typeof actualVal === 'number' && Number.isFinite(actualVal) === Number.isFinite(expectedVal),
      `${toolId}/${caseName}: field '${key}' expected number ~${expectedVal}, got ${JSON.stringify(actualVal)}`);
    const tol = Math.max(1e-6, Math.abs(expectedVal) * 1e-6);
    assert.ok(Math.abs(actualVal - expectedVal) <= tol || actualVal === expectedVal,
      `${toolId}/${caseName}: field '${key}' expected ~${expectedVal}, got ${actualVal}`);
  } else if (Array.isArray(expectedVal) || (typeof expectedVal === 'object' && expectedVal !== null)) {
    assert.deepEqual(actualVal, expectedVal, `${toolId}/${caseName}: field '${key}' mismatch`);
  } else {
    assert.equal(actualVal, expectedVal, `${toolId}/${caseName}: field '${key}' expected ${JSON.stringify(expectedVal)}, got ${JSON.stringify(actualVal)}`);
  }
}

test('tier-c known-value — FW-4 detection-forecast (self-contained buildArtifact())', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'detection-forecast.fixtures.json'), 'utf8'));
  for (const c of fixture.cases) {
    await t.test(`detection-forecast / ${c.name}`, async () => {
      const sandbox = loadTool('detection-forecast');
      sandbox.location.hash = '#' + c.hash;
      sandbox.loadHash();
      const artifact = await sandbox.buildArtifact();
      const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
      for (const [key, expectedVal] of Object.entries(c.expected))
        deepFieldEqual(actualPayload[key], expectedVal, 'detection-forecast', c.name, key);
    });
  }
});

test('tier-c known-value — FW-4 gaia-dr4-forecaster (self-contained buildArtifact())', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'gaia-dr4-forecaster.fixtures.json'), 'utf8'));
  for (const c of fixture.cases) {
    await t.test(`gaia-dr4-forecaster / ${c.name}`, async () => {
      const sandbox = loadTool('gaia-dr4-forecaster');
      sandbox.location.hash = '#' + c.hash;
      sandbox.loadHash();
      const artifact = await sandbox.buildArtifact();
      const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
      for (const [key, expectedVal] of Object.entries(c.expected))
        deepFieldEqual(actualPayload[key], expectedVal, 'gaia-dr4-forecaster', c.name, key);
    });
  }
});

test('tier-c known-value — FW-4 ir-excess-checker (self-contained buildArtifact())', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'ir-excess-checker.fixtures.json'), 'utf8'));
  for (const c of fixture.cases) {
    await t.test(`ir-excess-checker / ${c.name}`, async () => {
      const sandbox = loadTool('ir-excess-checker');
      sandbox.location.hash = '#' + c.hash;
      sandbox.loadHash();
      const artifact = await sandbox.buildArtifact();
      const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
      for (const [key, expectedVal] of Object.entries(c.expected))
        deepFieldEqual(actualPayload[key], expectedVal, 'ir-excess-checker', c.name, key);
    });
  }
});

test('tier-c known-value — FW-4 radio-seti (render()-populated window._toolArtifactData)', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'radio-seti.fixtures.json'), 'utf8'));
  for (const c of fixture.cases) {
    await t.test(`radio-seti / ${c.name}`, async () => {
      const sandbox = loadTool('radio-seti');
      assert.equal(typeof sandbox.render, 'function', 'radio-seti: expected render()');
      sandbox.location.hash = '#' + c.hash;
      sandbox.loadHash();
      sandbox.render();
      const artifact = await sandbox.buildArtifact();
      const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
      for (const [key, expectedVal] of Object.entries(c.expected))
        deepFieldEqual(actualPayload[key], expectedVal, 'radio-seti', c.name, key);
    });
  }
});

// observing-campaign-planner's calculate() reads the "selected" instrument
// straight from document.getElementById('sel-instr').value rather than
// `state.instr` (loadHash() sets both, matching what a browser would do when
// the page's own onchange="calculate()" handler fires). Its own top-level
// `loadHash(); calculate();` init call runs unconditionally the instant the
// script is evaluated -- before this test ever gets a chance to set the
// hash -- so the fake DOM must already have a valid <select> default (a real
// browser initializes a <select> with no explicit "selected" option to its
// first <option>) or that first calculate() throws on an undefined
// instrument lookup. loadTool() takes an optional third `presetIds` param
// for exactly this.
function loadObservingCampaignPlanner() {
  const sandbox = loadTool('observing-campaign-planner', '', {
    'sel-instr': 'omegacat',
    'sel-goal': 'nominal_1',
  });
  return sandbox;
}

test('tier-c known-value — FW-4 observing-campaign-planner (sync buildArtifact() + external hash)', async (t) => {
  const fixture = JSON.parse(readFileSync(resolve(FIXTURES_DIR, 'observing-campaign-planner.fixtures.json'), 'utf8'));
  for (const c of fixture.cases) {
    await t.test(`observing-campaign-planner / ${c.name}`, async () => {
      const sandbox = loadObservingCampaignPlanner();
      assert.equal(typeof sandbox.calculate, 'function', 'observing-campaign-planner: expected calculate()');
      assert.equal(typeof sandbox.computeExecHash, 'function', 'observing-campaign-planner: expected computeExecHash()');
      sandbox.location.hash = '#' + c.hash;
      sandbox.loadHash();
      sandbox.calculate();
      const artifact = sandbox.buildArtifact();
      artifact.execution_hash = await sandbox.computeExecHash(artifact.policy_parameters, artifact.output_payload);
      const actualPayload = JSON.parse(JSON.stringify(artifact.output_payload));
      for (const [key, expectedVal] of Object.entries(c.expected))
        deepFieldEqual(actualPayload[key], expectedVal, 'observing-campaign-planner', c.name, key);
    });
  }
});

// ---- Group: P0-CALC-1 repaired site-only tools (2026-09-24) ----
// Four non-manifest tool pages whose physics this WU repaired. Fixtures are
// hand-derived from the documented conversion chains, not from the tools'
// own code:
//   - multi-messenger-alert: 10 TeV = 1e13 eV x 1.602e-12 erg/eV = 16.02 erg
//     (the old code divided by 1e6); LISA SNR refused outside the
//     Amaro-Seoane+2017 PSD fit's stated band (~1e-4..1e-1 Hz).
//   - accretion-state: Paper F limits 1.1 uJy @ 5.2 kpc -> L_nu = 4 pi d^2
//     S_nu = 3.56e9 W/Hz; 1.6e30 erg/s -> 1.6e23 W; Merloni+2003 plane
//     re-derived from their eq. 1 cgs form to the page's W / W-per-Hz units.
//   - joint-accretion-bound-explorer: v0.4 anchors (85.0% / 78.5% / 99.3%)
//     read from the generated data/fF_v4_embed.js; numeric pins live in
//     scripts/check-p0calc-parity.py (python, also CI-wired).
//   - mass-tension-explorer: region values + cell counts merge from
//     data/fH_plane_embed.js; assert the merge landed in the page's readout.

test('tier-c known-value — P0-CALC-1 multi-messenger-alert energy conversion + LISA band gate', async (t) => {
  const sandbox = loadTool('multi-messenger-alert');
  assert.equal(typeof sandbox.km3NetEvents, 'function', 'expected top-level km3NetEvents()');
  assert.equal(typeof sandbox.lisaSNR, 'function', 'expected top-level lisaSNR()');

  await t.test('10 TeV = 16.02 erg (event count at defaults, hand-derived)', () => {
    // logP=38 -> 1e45 erg/s; nu_frac 0.15; D = 1.694e22 cm;
    // flux = 1e45*0.15 / (4*pi*(1.694e22)^2 * 16.02) = 2.5966e-3 /cm2/s
    // events = flux * 2e8 cm^2 (Aeff) * 100 s (dt) = 5.1932e7
    const events = sandbox.km3NetEvents(38, 2);
    const expected = (1e45 * 0.15) / (4 * Math.PI * Math.pow(1.694e22, 2) * 16.02) * 2e8 * 100;
    assert.ok(Math.abs(events - expected) <= 1e-9 * expected,
      `km3NetEvents(38,2) expected ~${expected}, got ${events}`);
    assert.ok(Math.abs(events - 5.1932e7) / 5.1932e7 < 1e-3,
      `hand-derived 5.1932e7 events, got ${events}`);
  });

  await t.test('LISA out-of-band gate at 8,200 M_sun (f_peak ~ 0.54 Hz)', () => {
    const r = sandbox.lisaSNR(Math.log10(8200), 1.4, 5, 0.3);
    assert.equal(r.inBand, false, 'default mass must be flagged out-of-band');
    assert.equal(r.snr, null, 'no SNR may be quoted out of band');
    assert.ok(r.f_peak > 0.1, `f_peak ${r.f_peak} should exceed the 0.1 Hz ceiling`);
  });

  await t.test('LISA in-band at 50,000 M_sun (f_peak ~ 0.09 Hz) yields finite SNR', () => {
    const r = sandbox.lisaSNR(Math.log10(50000), 1.4, 5, 0.3);
    assert.equal(r.inBand, true, '50,000 M_sun should sit inside the band');
    assert.ok(Number.isFinite(r.snr) && r.snr > 0, `expected finite SNR, got ${r.snr}`);
  });
});

test('tier-c known-value — P0-CALC-1 accretion-state Paper F limits + Merloni plane', async (t) => {
  const sandbox = loadTool('accretion-state');
  assert.equal(typeof sandbox.radioLimitNu, 'function', 'expected radioLimitNu()');
  assert.equal(typeof sandbox.xrayLimitW, 'function', 'expected xrayLimitW()');
  assert.equal(typeof sandbox.merloniLogLnu, 'function', 'expected merloniLogLnu()');

  await t.test('1.1 uJy at 5.2 kpc -> 3.56e9 W/Hz', () => {
    const v = sandbox.radioLimitNu(1.1, 5.2);
    const expected = 4 * Math.PI * Math.pow(5.2 * 3.086e19, 2) * 1.1e-32;
    assert.ok(Math.abs(v - expected) <= 1e-9 * expected, `expected ~${expected}, got ${v}`);
    assert.ok(Math.abs(v - 3.559e9) / 3.559e9 < 1e-3, `hand-derived 3.559e9 W/Hz, got ${v}`);
  });

  await t.test('1.6e30 erg/s -> 1.6e23 W', () => {
    assert.ok(Math.abs(sandbox.xrayLimitW(1.6e30) - 1.6e23) <= 1e-12 * 1.6e23);
  });

  await t.test('Merloni plane round-trips to the cgs eq.-1 value', () => {
    // page convention: log10(L_nu/W Hz^-1) = 0.6 log10(L_X/W) + 0.78 log10(M)
    // - 5.17. Converting back (add log10(5e9 Hz), add 7 for erg/s) must
    // reproduce Merloni eq. 1: 0.6 log10(L_X/erg s^-1) + 0.78 log10(M) + 7.33.
    const logLxW = 23.2, mSun = 8200;
    const page = sandbox.merloniLogLnu(logLxW, Math.log10(mSun));
    const backToCgs = page + Math.log10(5e9) + 7;
    const merloni = 0.6 * (logLxW + 7) + 0.78 * Math.log10(mSun) + 7.33;
    assert.ok(Math.abs(backToCgs - merloni) <= 5e-3,
      `page plane + unit chain = ${backToCgs}, Merloni eq.1 = ${merloni}`);
  });

  await t.test('defaults carry the Paper F limits', () => {
    sandbox.compute(); // re-render at S defaults
    assert.match(sandbox.document.getElementById('lbl-lr').textContent, /3\.5[0-9]?×10⁹|3\.6×10⁹/);
    assert.match(sandbox.document.getElementById('lbl-lx').textContent, /1\.60×10²³/);
  });
});

test('tier-c known-value — P0-CALC-1 joint-accretion-bound-explorer v0.4 anchors', async (t) => {
  const sandbox = loadTool('joint-accretion-bound-explorer');
  // default state: 8,200 M_sun, RIAF family, radio leg on
  assert.equal(sandbox.document.getElementById('exclfrac-out').textContent, '85.0%',
    'default exclusion fraction must read the v0.4 85.0% anchor');
  sandbox.setFamily('jet');
  // The readout interpolates the shipped 41-point v0.4 curve; the exact MC
  // anchor at 8,200 is 78.46% (pinned in check-p0calc-parity.py), a rounding
  // hair off the curve interpolation the page quotes.
  assert.equal(sandbox.document.getElementById('exclfrac-out').textContent, '78.4%',
    'jet family at 8,200 M_sun must read the v0.4 curve interpolation');
});

test('tier-c known-value — P0-CALC-1 mass-tension-explorer shipped cell counts', async (t) => {
  const sandbox = loadTool('mass-tension-explorer');
  // default configuration nolegprof_plummer_5200: shipped HPD90 = 49 of 1,891
  assert.equal(sandbox.document.getElementById('hpd-cells-out').textContent,
    '49 of 1891 grid cells', 'HPD90 cell count must come from the shipped embed');
  assert.match(sandbox.document.getElementById('hpd-a-out').textContent, /pc/);
});

// ---- Group: P0-CALC-2 repaired site-only tools (2026-09-24) ----
//   - seed-formation: core-collapse law re-calibrated to the literature
//     standard t_cc = 0.15 t_rh (Spitzer 1987; Portegies Zwart et al. 2010
//     review; the previously coded 0.015 factor appears nowhere in the cited
//     PZ&M 2002). Regression: omega Cen preset relaxation time ~8.6 Gyr ->
//     t_core ~1.29 Gyr -> 'merger' channel; monotone in t_rh.
//   - tidal-capture: Hills masses hand-derived from r_T = R_star (M/M_star)^(1/3)
//     set equal to r_S = 2GM/c^2 -> M = (R_star c^2 / 2G)^(3/2) M_star^(-1/2):
//     solar-type ~1.14e8 M_sun, WD (0.6/0.01) ~1.48e5 M_sun.
test('tier-c known-value — P0-CALC-2 seed-formation collapse law + omega Cen regression', async (t) => {
  const sandbox = loadTool('seed-formation');
  assert.equal(typeof sandbox.calcRelaxationTime, 'function');
  assert.equal(typeof sandbox.calcCoreCollapse, 'function');
  assert.equal(typeof sandbox.determineChannel, 'function');

  await t.test('omega Cen preset: t_rh ~ 8.6 Gyr, t_core ~ 1.29 Gyr, merger channel', () => {
    const t_rh = sandbox.calcRelaxationTime(4e6, 7.0);
    assert.ok(Math.abs(t_rh - 8.586) / 8.586 < 0.01, `t_rh expected ~8.586 Gyr, got ${t_rh}`);
    const t_core = sandbox.calcCoreCollapse(t_rh);
    assert.ok(Math.abs(t_core - 0.15 * t_rh) < 1e-12, 'collapse law must be 0.15 x t_rh');
    assert.equal(sandbox.determineChannel(t_core, 0.50), 'merger',
      'present-day omega Cen structure must read the merger channel under the corrected law');
  });

  await t.test('core-collapse time monotone in t_rh', () => {
    let prev = -1;
    for (const t_rh of [0.01, 0.1, 1, 10, 100]) {
      const v = sandbox.calcCoreCollapse(t_rh);
      assert.ok(v > prev, `not monotone at t_rh=${t_rh}`);
      prev = v;
    }
  });

  await t.test('runaway channel still reachable for compact young low-Z cluster', () => {
    // M=1e7, r_h=0.05 pc -> t_rh ~ 7.7 Myr -> t_core = 1.16 Myr < 3 Myr, Z=0.05
    const t_rh = sandbox.calcRelaxationTime(1e7, 0.05);
    const t_core = sandbox.calcCoreCollapse(t_rh);
    assert.equal(sandbox.determineChannel(t_core, 0.05), 'runaway');
  });
});

test('tier-c known-value — P0-CALC-2 tidal-capture Hills masses + tidal-radius scaling', async (t) => {
  const sandbox = loadTool('tidal-capture');
  assert.equal(typeof sandbox.hillsMass_msun, 'function');
  assert.equal(typeof sandbox.encounterRate_perMyr, 'function',
    'encounter rate must be renamed away from TDE wording');

  await t.test('solar-type Hills mass ~1.14e8 M_sun', () => {
    const m = sandbox.hillsMass_msun(1.0, 1.0);
    assert.ok(Math.abs(m - 1.1429e8) / 1.1429e8 < 1e-3, `expected ~1.1429e8, got ${m}`);
  });

  await t.test('WD (0.6 M_sun, 0.01 R_sun) Hills mass ~1.48e5 M_sun', () => {
    const m = sandbox.hillsMass_msun(0.6, 0.01);
    assert.ok(Math.abs(m - 1.4758e5) / 1.4758e5 < 1e-3, `expected ~1.4758e5, got ${m}`);
  });

  await t.test('tidal radius scales as R_star (M/M_star)^(1/3)', () => {
    const r1 = sandbox.tidalRadius_cm(40000, 1.0, 1.0);
    const r2 = sandbox.tidalRadius_cm(40000, 1.0, 2.0);   // 2x star radius
    const r3 = sandbox.tidalRadius_cm(320000, 1.0, 1.0);  // 8x BH mass
    assert.ok(Math.abs(r2 / r1 - 2) < 1e-9, 'r_T must scale linearly in R_star');
    assert.ok(Math.abs(r3 / r1 - 2) < 1e-9, 'r_T must scale as M_BH^(1/3)');
  });

  await t.test('swallow case: at the Hills mass r_T == r_S; above it r_T < r_S', () => {
    const G = 6.674e-11, c = 2.998e8, MSUN = 1.989e30;
    const rS_cm = (m_kg) => 2 * G * m_kg / (c * c) * 100;
    const mH = sandbox.hillsMass_msun(1.0, 1.0);
    const rT_at = sandbox.tidalRadius_cm(mH, 1.0, 1.0);
    assert.ok(Math.abs(rT_at - rS_cm(mH * MSUN)) / rS_cm(mH * MSUN) < 1e-6,
      'r_T must equal r_S at the Hills mass');
    const rT_above = sandbox.tidalRadius_cm(mH * 4, 1.0, 1.0);
    assert.ok(rT_above < rS_cm(mH * 4 * MSUN), 'above the Hills mass the object is swallowed whole');
  });
});

// ---- Group: P0-PAGES-1 astrometric-microlensing physics (2026-09-25) ----
// Hand-derived from the page's own documented formulas (Dominik & Sahu 2000;
// Paczynski 1986): theta_E = sqrt(4GM(D_S-D_L)/(c^2 D_L D_S));
// delta_theta_max = theta_E/(2 sqrt 2) at u = sqrt 2.
//   theta_E(8200 M_sun, 5.49, 8.0 kpc) = 61.7801 mas
//   delta_max = 21842.57 uas ; A(u=1) = sqrt(5)/sqrt(9)... = 1.3416
test('tier-c known-value — P0-PAGES-1 astrometric-microlensing lensing geometry', async (t) => {
  const sandbox = loadTool('astrometric-microlensing');
  assert.equal(typeof sandbox.einsteinThetaRad, 'function');
  assert.equal(typeof sandbox.centroidShift, 'function');
  assert.equal(typeof sandbox.magnification, 'function');

  await t.test('Einstein radius at the omega Cen default geometry', () => {
    const th_mas = sandbox.einsteinThetaRad(8200, 5.49, 8.0) * 206264.806e3;
    const expected = Math.sqrt(4 * 6.674e-11 * 8200 * 1.989e30 * ((8.0 - 5.49) * 3.086e19) /
      (Math.pow(2.998e8, 2) * 5.49 * 3.086e19 * 8.0 * 3.086e19)) * 206264.806e3;
    assert.ok(Math.abs(th_mas - expected) <= 1e-9 * expected, `expected ~${expected} mas, got ${th_mas}`);
    assert.ok(Math.abs(th_mas - 61.7801) / 61.7801 < 1e-4, `hand-derived 61.7801 mas, got ${th_mas}`);
  });

  await t.test('centroid shift peaks at theta_E / (2 sqrt 2) for u = sqrt 2', () => {
    const th = 61.7801;
    const d = sandbox.centroidShift(Math.SQRT2, th) * 1000; // uas
    assert.ok(Math.abs(d - th * 1000 / (2 * Math.SQRT2)) < 1e-6);
    // far u: shift = u/(u^2+2) th = (th/u)/(1+2/u^2), slightly under th/u
    const far = sandbox.centroidShift(100, th);
    assert.ok(Math.abs(far - 100 / (100 * 100 + 2) * th) < 1e-9);
  });

  await t.test('magnification matches Paczynski 1986 at u = 1', () => {
    const A = sandbox.magnification(1.0);
    // A(1) = (1+2)/(1*sqrt(1+4)) = 3/sqrt(5)
    assert.ok(Math.abs(A - 3 / Math.sqrt(5)) < 1e-12, `A(1) expected 3/sqrt(5), got ${A}`);
  });
});
