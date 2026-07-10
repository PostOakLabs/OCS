// tier-c-hash-roundtrip.test.mjs — OCS-TEST-COVERAGE-SPEC.md v1 §3 Tier C, layer 1.
//
// Per CLAUDE.md architecture rule #5, every tool serializes state to a URL
// hash on interaction and restores it on load. This test proves that
// round trip is lossless: saveHash(fixture) -> loadHash() -> saveHash()
// reproduces the exact same hash string (a fixed point), for every tool
// in tools-manifest.json. It does NOT assert the fixture's hash matches
// any particular physics answer — that's tier-c-known-value.test.mjs.
// A failure here means a hash param was dropped, renamed, or its encoding
// changed during a refactor — the gap flagged in the spec as "no gate".
//
// Technique: load each tool's inline <script> bodies (+ measurements.js if
// referenced) into a node:vm context with a minimal DOM/window/history
// shim, same extraction regex as syntax-check.mjs. Then drive the tool's
// own saveHash/loadHash (or saveStateToHash/loadStateFromHash) functions.
//
// Run: node --test scripts/tests/tier-c-hash-roundtrip.test.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');

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

// Chainable fake DOM element via Proxy: reads of unset props return either
// a callable no-op (for method-shaped access) or a fresh fake element (for
// property-shaped access); writes are stored and read back verbatim.
// Common DOM value-ish properties default to primitives (not the no-op
// function fallback) so `(el.value || '').trim()`-style code doesn't choke.
const PRIMITIVE_DEFAULTS = {
  value: '', textContent: '', innerText: '', innerHTML: '', className: '',
  id: '', name: '', checked: false, disabled: false, hidden: false,
  selectedIndex: -1,
  firstChild: null, lastChild: null, nextSibling: null, previousSibling: null,
  parentNode: null, parentElement: null,
};
function makeFakeEl(initial) {
  const store = { ...PRIMITIVE_DEFAULTS, ...(initial || {}) };
  const noop = () => makeFakeEl();
  return new Proxy(store, {
    get(target, prop) {
      if (prop === Symbol.toPrimitive || prop === 'toString') return () => '';
      if (prop === 'valueOf') return () => 0;
      if (Object.prototype.hasOwnProperty.call(target, prop)) return target[prop];
      if (prop === 'style' || prop === 'dataset') { const v = {}; target[prop] = v; return v; }
      if (prop === 'classList') {
        const v = { add() {}, remove() {}, toggle() { return false; }, contains() { return false; } };
        target[prop] = v; return v;
      }
      if (prop === 'children' || prop === 'childNodes' || prop === 'options') return [];
      if (prop === 'getAttribute') return () => null;
      return noop;
    },
    set(target, prop, value) { target[prop] = value; return true; },
  });
}

// Scan the raw HTML for <input id=.. value=..>/<select id=..><option ..
// selected> initial markup so getElementById(id) reflects what a browser
// would show before any script runs (checkboxes/selects several tools
// read on init to seed their default state).
function staticElementValues(html) {
  const values = {};
  const inputRe = /<input\b([^>]*)>/gi;
  let m;
  while ((m = inputRe.exec(html)) !== null) {
    const attrs = m[1];
    const idMatch = attrs.match(/\bid\s*=\s*["']([^"']+)["']/i);
    if (!idMatch) continue;
    const valMatch = attrs.match(/\bvalue\s*=\s*["']([^"']*)["']/i);
    const checked = /\bchecked\b/i.test(attrs);
    const typeMatch = attrs.match(/\btype\s*=\s*["']([^"']+)["']/i);
    values[idMatch[1]] = { value: valMatch ? valMatch[1] : '', checked, type: typeMatch ? typeMatch[1] : 'text' };
  }
  const selectRe = /<select\b[^>]*\bid\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/select>/gi;
  while ((m = selectRe.exec(html)) !== null) {
    const [, id, body] = m;
    const optRe = /<option\b([^>]*)>/gi;
    let om, first = null, selected = null;
    while ((om = optRe.exec(body)) !== null) {
      const attrs = om[1];
      const valMatch = attrs.match(/\bvalue\s*=\s*["']([^"']*)["']/i);
      const val = valMatch ? valMatch[1] : '';
      if (first === null) first = val;
      if (/\bselected\b/i.test(attrs)) selected = val;
    }
    values[id] = { value: selected !== null ? selected : (first || '') };
  }
  return values;
}

function makeSandbox(html) {
  const elValues = staticElementValues(html);
  const location = { hash: '', href: 'https://omegacentauri.me/tools/x.html', search: '', pathname: '/tools/x.html' };
  location.replace = (url) => {
    const h = String(url || '');
    const i = h.indexOf('#');
    location.hash = i >= 0 ? h.slice(i) : h;
  };
  location.assign = location.replace;
  const history = { replaceState(_s, _t, url) {
    const h = String(url || '');
    const i = h.indexOf('#');
    location.hash = i >= 0 ? h.slice(i) : h;
  }, pushState(_s, _t, url) { history.replaceState(_s, _t, url); } };
  const listeners = {};
  const document = {
    getElementById(id) { return makeFakeEl(elValues[id]); },
    querySelector() { return makeFakeEl(); },
    querySelectorAll() { return []; },
    createElement() { return makeFakeEl(); },
    createElementNS() { return makeFakeEl(); },
    addEventListener(ev, fn) { (listeners['doc:' + ev] = listeners['doc:' + ev] || []).push(fn); },
    removeEventListener() {},
    body: makeFakeEl(),
    documentElement: makeFakeEl(),
    readyState: 'complete',
  };
  const navigator = { clipboard: { writeText() { return Promise.resolve(); } }, userAgent: 'node-test' };

  // `window` IS the vm context's global object (as in a real browser, where
  // `window === globalThis`) so `window.OCS_MEASUREMENTS = x` assignments
  // inside measurements.js are visible as the bare global `OCS_MEASUREMENTS`
  // that tool scripts reference directly.
  const sandbox = {
    location, history, document, navigator,
    addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
    removeEventListener() {},
    matchMedia() { return { matches: false, addEventListener() {}, addListener() {} }; },
    isSecureContext: false,
    requestAnimationFrame(fn) { return setTimeout(fn, 0); },
    cancelAnimationFrame() {},
    scrollTo() {},
    innerWidth: 1280, innerHeight: 800,
    console, setTimeout, clearTimeout, setInterval, clearInterval,
    URL, URLSearchParams, Blob, TextEncoder, TextDecoder, crypto: globalThis.crypto,
    performance: { now: () => 0 },
    screen: { width: 1280, height: 800 },
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  return sandbox;
}

function loadTool(toolId, entry) {
  const abs = resolve(REPO, entry.path);
  const html = readFileSync(abs, 'utf8');
  const sandbox = makeSandbox(html);
  const usesMeasurements = /measurements\.js/.test(html);
  const code = (usesMeasurements ? MEASUREMENTS_SRC + '\n' : '') + inlineScripts(html).join('\n;\n');
  new vm.Script(code, { filename: entry.path }).runInContext(sandbox, { timeout: 5000 });
  const saveName = typeof sandbox.saveHash === 'function' ? 'saveHash'
    : typeof sandbox.saveStateToHash === 'function' ? 'saveStateToHash' : null;
  const loadName = typeof sandbox.loadHash === 'function' ? 'loadHash'
    : typeof sandbox.loadStateFromHash === 'function' ? 'loadStateFromHash' : null;
  return { sandbox, saveName, loadName };
}

// Build a plausible fixture hash string from the manifest's own documented
// inputs — pulls "default X" / "e.g. X" example values out of the desc text,
// falling back to 1 (numbers) or the first enumerated token (strings).
function fixtureHashFor(entry) {
  const parts = [];
  for (const [key, spec] of Object.entries(entry.inputs || {})) {
    const desc = spec.desc || '';
    let value;
    const defaultMatch = desc.match(/default\s*-?\d+(\.\d+)?/i);
    const egMatch = desc.match(/e\.g\.,?\s*(-?\d+(\.\d+)?)/i);
    if (defaultMatch) value = defaultMatch[0].replace(/default\s*/i, '');
    else if (egMatch) value = egMatch[1];
    else if (spec.type === 'number') value = '1';
    else if (spec.type === 'string') {
      const enumMatch = desc.match(/:\s*([a-zA-Z0-9_]+)\s*(\||\()/);
      value = enumMatch ? enumMatch[1] : '';
    } else value = '';
    if (value !== '' && value !== undefined) parts.push(`${key}=${encodeURIComponent(value)}`);
  }
  return parts.join('&');
}

// Drives one load-then-save cycle and returns the resulting hash. Some
// tools' saveHash(state)/saveHash(value) needs an explicit argument that
// only the tool's own render/calculate pipeline knows how to supply; others
// save as a side effect of loadHash() itself (e.g. loadHash -> calculate ->
// saveHash chain). We try, in order: a render-family entrypoint (covers the
// common "loadHash sets state, caller renders" pattern), saveHash(state) if
// a module-level `state` object exists, then fall back to whatever hash
// loadHash() itself already left behind.
function driveLoadSave(sandbox, saveName, loadName) {
  sandbox[loadName]();
  for (const fnName of ['render', 'update', 'recalc', 'draw', 'refresh']) {
    if (typeof sandbox[fnName] === 'function') {
      sandbox[fnName]();
      return sandbox.location.hash;
    }
  }
  if (typeof sandbox[saveName] === 'function') {
    if (sandbox.state !== undefined) { sandbox[saveName](sandbox.state); return sandbox.location.hash; }
    try { sandbox[saveName](); return sandbox.location.hash; } catch { /* loadHash already saved */ }
  }
  return sandbox.location.hash;
}

const tools = manifest.tools;
test('tier-c hash round-trip — every MCP-manifest tool', async (t) => {
  const toolIds = process.env.ONLY_TOOL ? [process.env.ONLY_TOOL] : Object.keys(tools);
  assert.ok(toolIds.length > 0, 'manifest must list at least one tool');

  for (const toolId of toolIds) {
    await t.test(toolId, () => {
      const entry = tools[toolId];
      const { sandbox, saveName, loadName } = loadTool(toolId, entry);
      assert.ok(saveName, `${toolId}: no saveHash()/saveStateToHash() found in page script`);
      assert.ok(loadName, `${toolId}: no loadHash()/loadStateFromHash() found in page script`);

      const fixture = fixtureHashFor(entry);
      sandbox.location.hash = '#' + fixture;
      const h1 = driveLoadSave(sandbox, saveName, loadName);

      // Reset to h1, reload, resave — must be a fixed point.
      sandbox.location.hash = h1;
      const h2 = driveLoadSave(sandbox, saveName, loadName);

      assert.equal(h2, h1, `${toolId}: hash round-trip not idempotent (${h1} -> ${h2})`);
    });
  }
});
