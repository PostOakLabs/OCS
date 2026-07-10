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
//
// Remaining 23 of 31 manifest tools have round-trip coverage only — a
// follow-up WU per spec §6.
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
  const location = { hash: '' };
  const history = { replaceState(_s, _t, url) {
    const h = String(url || ''); const i = h.indexOf('#');
    location.hash = i >= 0 ? h.slice(i) : h;
  } };
  const document = {
    getElementById() { return makeFakeEl(); },
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
    performance: { now: () => 0 }, screen: { width: 1280, height: 800 },
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  return sandbox;
}

function loadTool(toolId) {
  const entry = manifest.tools[toolId];
  const abs = resolve(REPO, entry.path);
  const html = readFileSync(abs, 'utf8');
  const sandbox = makeSandbox();
  const usesMeasurements = /measurements\.js/.test(html);
  const code = (usesMeasurements ? MEASUREMENTS_SRC + '\n' : '') + inlineScripts(html).join('\n;\n');
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
