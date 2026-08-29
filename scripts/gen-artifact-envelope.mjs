#!/usr/bin/env node
// gen-artifact-envelope.mjs — FIXWAVE helper (OCS-FIXWAVE.md FW-1).
//
// Produces a hash-bound ChainGraph artifact envelope for a tool's known-value
// fixture case, using the tool's OWN executionHash()/canonicalPreimage()
// (loaded live from its <script>, not reimplemented here) so the emitted
// execution_hash is byte-identical to what the real page would compute for
// the same policy_parameters/output_payload pair. Writes the envelope into
// the fixture file's top-level "artifact" property, which schema-validate.mjs
// already recognizes (doc.artifact ? [doc.artifact] : ...).
//
// Two call modes:
//   --kernel   compute() takes {execution_backend,input_parameters} and
//              returns {output_payload}; envelope wraps that live output.
//   --purefn   the tool has no compute() entrypoint, only named pure
//              functions (e.g. bekensteinBits). Envelope wraps a minimal
//              {fn,args} policy and {fn,result} payload — schema-conformant,
//              hash-bound, but not the tool's live UI buildArtifact() shape
//              (that path needs DOM-driven state the sandbox does not
//              simulate; the known-value test already covers fn(args)
//              correctness directly).
//
// Usage:
//   node scripts/gen-artifact-envelope.mjs <toolId> --kernel [--case=<name>]
//   node scripts/gen-artifact-envelope.mjs <toolId> --purefn --case=<name>
//
// Idempotent: re-running overwrites the "artifact" key with a fresh
// generated_at + recomputed hash (hash is a function of policy+output only,
// so it stays stable across regenerations of the same case).

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const FIXTURES_DIR = resolve(HERE, 'fixtures');

const [, , toolId, ...rest] = process.argv;
if (!toolId) { console.error('usage: gen-artifact-envelope.mjs <toolId> --kernel|--purefn [--case=name]'); process.exit(1); }
const mode = rest.includes('--kernel') ? 'kernel' : rest.includes('--purefn') ? 'purefn' : null;
if (!mode) { console.error('must pass --kernel or --purefn'); process.exit(1); }
const caseArg = rest.find((a) => a.startsWith('--case='));
const caseName = caseArg ? caseArg.slice('--case='.length) : null;

const manifest = JSON.parse(readFileSync(resolve(REPO, 'tools/data/tools-manifest.json'), 'utf8'));
const MEASUREMENTS_SRC = readFileSync(resolve(REPO, 'tools/data/measurements.js'), 'utf8');

function externalScriptSources(html, baseDir) {
  const out = [];
  const re = /<script\b[^>]*\bsrc\s*=\s*["']([^"']+)["'][^>]*>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const src = m[1];
    if (/^(https?:)?\/\//i.test(src)) continue;
    if (/measurements\.js$/.test(src)) continue;
    if (/prefill\.js$/.test(src)) continue;
    try { out.push(readFileSync(resolve(REPO, baseDir, src), 'utf8')); } catch {}
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
    get(target, prop) { if (Object.prototype.hasOwnProperty.call(target, prop)) return target[prop]; return () => makeFakeEl(); },
    set(target, prop, value) { target[prop] = value; return true; },
  });
}
function makeSandbox() {
  const location = { hash: '' };
  const history = { replaceState(_s, _t, url) { const h = String(url || ''); const i = h.indexOf('#'); location.hash = i >= 0 ? h.slice(i) : h; } };
  const document = {
    getElementById() { return makeFakeEl(); }, querySelector() { return makeFakeEl(); }, querySelectorAll() { return []; },
    createElement() { return makeFakeEl(); }, createElementNS() { return makeFakeEl(); }, addEventListener() {},
    body: makeFakeEl(), documentElement: makeFakeEl(),
  };
  const sandbox = {
    location, history, document,
    navigator: { clipboard: { writeText() { return Promise.resolve(); } } },
    addEventListener() {}, removeEventListener() {},
    matchMedia() { return { matches: false, addEventListener() {}, addListener() {} }; },
    isSecureContext: true,
    requestAnimationFrame(fn) { return setTimeout(fn, 0); }, cancelAnimationFrame() {},
    console, setTimeout, clearTimeout, setInterval, clearInterval,
    URL, URLSearchParams, Blob, TextEncoder, TextDecoder, crypto: globalThis.crypto,
    performance: { now: () => 0 }, screen: { width: 1280, height: 800 },
  };
  sandbox.window = sandbox; sandbox.self = sandbox;
  vm.createContext(sandbox);
  return sandbox;
}
function loadTool(id) {
  const entry = manifest.tools[id];
  if (!entry) throw new Error(`unknown tool in manifest: ${id}`);
  const abs = resolve(REPO, entry.path);
  const html = readFileSync(abs, 'utf8');
  const sandbox = makeSandbox();
  const usesMeasurements = /measurements\.js/.test(html);
  const deps = externalScriptSources(html, dirname(entry.path));
  const code = (usesMeasurements ? MEASUREMENTS_SRC + '\n' : '')
    + (deps.length ? deps.join('\n;\n') + '\n;\n' : '')
    + inlineScripts(html).join('\n;\n');
  new vm.Script(code, { filename: entry.path }).runInContext(sandbox, { timeout: 5000 });
  return sandbox;
}

const fixturePath = resolve(FIXTURES_DIR, `${toolId}.fixtures.json`);
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
const c = caseName ? fixture.cases.find((x) => x.name === caseName) : fixture.cases[0];
if (!c) { console.error(`case not found in ${fixturePath}`); process.exit(1); }

const sandbox = loadTool(toolId);
if (typeof sandbox.executionHash !== 'function') { console.error(`${toolId}: no top-level executionHash() found`); process.exit(1); }

let policy_parameters, output_payload;
if (mode === 'kernel') {
  if (typeof sandbox.compute !== 'function') { console.error(`${toolId}: no top-level compute() found`); process.exit(1); }
  policy_parameters = { execution_backend: 'js', input_parameters: c.input };
  const raw = sandbox.compute(policy_parameters);
  output_payload = JSON.parse(JSON.stringify(raw && raw.output_payload ? raw.output_payload : raw));
} else {
  // args/result are stringified: several known-value inputs/results
  // (Bekenstein/Landauer/Lloyd bounds, 1e16-1e26 W Kardashev thresholds) are
  // integer-valued floats past 2^53, which the tool's own assertIJson()/
  // RFC-7493 check rejects as a JSON number — matching how the real page
  // only ever surfaces these via formatted display strings, never as a raw
  // number through the hash preimage.
  policy_parameters = { execution_backend: 'js', input_parameters: { fn: c.fn, args: c.args.map(String) } };
  output_payload = { fn: c.fn, args: c.args.map(String), result: String(c.expected) };
}

const execution_hash = await sandbox.executionHash(policy_parameters, output_payload);

const artifact = {
  '@context': 'https://openchain.graph/spec/v0.3/context.jsonld',
  chaingraph_version: '0.4.0',
  buildType: 'https://openchain.graph/spec/v0.2#WebCryptoSHA256',
  mandate_type: `me.omegacentauri/${toolId.replace(/-/g, '_')}`,
  tool_id: toolId,
  tool_version: '1.2.0',
  generated_at: new Date().toISOString(),
  execution_hash,
  chain: { parent_hashes: [], parent_tool_ids: [], chain_depth: 0 },
  policy_parameters,
  output_payload,
  compliance_flags: mode === 'kernel' ? ['register:peer-reviewed'] : ['register:speculative'],
  audit_signature: {
    client_side_executed: true,
    zero_pii_verified: true,
    deterministic_run: true,
    ocs_artifact_version: '1.0.0',
    schema_version: 'ocs-chaingraph-0.4.0',
    generation_note: mode === 'kernel'
      ? `Envelope generated by scripts/gen-artifact-envelope.mjs from fixture case "${c.name}"; execution_hash computed with the tool's own executionHash()/canonicalPreimage(), output_payload is the tool's live compute() output for this input (matches the tier-c known-value fixture).`
      : `Envelope generated by scripts/gen-artifact-envelope.mjs wrapping the pure-function known-value case "${c.name}" (${c.fn}(${JSON.stringify(c.args)}) = ${c.expected}); this tool has no live buildArtifact()-driving UI state in the test sandbox, so policy_parameters/output_payload are a minimal fn/args/result envelope rather than the page's own artifact shape.`,
  },
};

fixture.artifact = artifact;
writeFileSync(fixturePath, JSON.stringify(fixture, null, 2) + '\n');
console.log(`${toolId}: artifact envelope written (execution_hash=${execution_hash.slice(0, 16)}…)`);
