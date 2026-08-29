#!/usr/bin/env node
// schema-validate.mjs — GATE (conformance-by-construction).
// Validates captured OCS artifact fixtures against $defs/artifact in
// openchain-graph-v0.4.schema.json. Zero-dependency: implements the
// draft-2020-12 SUBSET the schema uses (type, required, properties,
// additionalProperties, enum, const, pattern, items, minItems, minLength,
// minimum, oneOf, $ref to local $defs).
// Non-zero exit blocks CI. Makes "strict v0.4" mean "validates against the
// published schema."
//
// Usage:
//   node scripts/schema-validate.mjs
//   SCHEMA=… FIXTURES_DIR=… node scripts/schema-validate.mjs
//
// Scope note: OCS's tools/data/chaingraph.json is a dict-of-tools registry
// (different shape from AINumbers' nodes[]/chains[] catalog) and is out of
// scope for this schema in this slice — only the artifact ENVELOPE (the
// per-call execution_hash/policy_parameters/output_payload object returned
// by a tool) is validated here, via captured fixtures in scripts/fixtures/.
//
// Adapted from AINumbers repo/chaingraph/standard/schema-validate.mjs
// (Phase B slice S-B1, OCG 0.2→0.8 upgrade).

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const SCHEMA = process.env.SCHEMA || join(HERE, 'openchain-graph-v0.4.schema.json');
const FIXTURES_DIR = process.env.FIXTURES_DIR || join(HERE, 'fixtures');

// ---- artifact-qualified tool coverage (OCS-FIXWAVE.md FW-1) ----
// A manifest tool is "artifact-qualified" if its page defines a top-level
// buildArtifact() — i.e. it actually emits a ChainGraph envelope with an
// execution_hash. Detected from source rather than hand-listed so the count
// self-updates as tools gain/lose artifact support; no separate list to drift.
//
// ALLOWLIST holds artifact-qualified tools NOT YET covered by a hash-bound
// fixture. Shrinks as OCS-FIXWAVE.md's FW-2..FW-5 sessions land; must be
// EMPTY at end state (28/28 covered). A tool here is a known, tracked gap —
// removing it from the list with no fixture in place is what the FAIL below
// is for.
const ALLOWLIST = new Set([
  // FW-2
  'shadow-imaging', 'velocity-dispersion', 'astrometric-microlensing',
  'pulsar-accel-mapper', 'dark-cluster',
  // FW-3
  'adaf-sed-modeler', 'bz-kardashev', 'cosmology-calculator',
  'gw-horizon-plotter', 'qpo-mass-spin',
  // FW-4
  'detection-forecast', 'gaia-dr4-forecaster', 'ir-excess-checker',
  'observing-campaign-planner', 'radio-seti',
  // FW-5
  'anisotropy-degeneracy-explorer', 'drake-monte-carlo', 'evidence-ledger',
  'great-filter', 'infall-survival',
]);

function artifactQualifiedTools() {
  const manifest = JSON.parse(readFileSync(resolve(REPO, 'tools/data/tools-manifest.json'), 'utf8'));
  const out = [];
  for (const [toolId, entry] of Object.entries(manifest.tools)) {
    let html;
    try { html = readFileSync(resolve(REPO, entry.path), 'utf8'); } catch { continue; }
    if (/function\s+buildArtifact\s*\(/.test(html)) out.push(toolId);
  }
  return out.sort();
}

// A fixture file "covers" a tool if it contains a hash-bound artifact object
// (top-level execution_hash, or a doc.artifact with one) whose tool_id
// matches. Value-only {cases:[...]} fixtures (no execution_hash) don't count.
function fixtureCoversTool(doc, toolId) {
  const candidates = doc.artifact ? [doc.artifact] : Array.isArray(doc) ? doc : doc.execution_hash ? [doc] : [];
  return candidates.some((a) => a && typeof a.execution_hash === 'string' && a.tool_id === toolId);
}

// ---- minimal JSON Schema (draft 2020-12 subset) validator ----
function validate(schema, data, root, path, errs) {
  if (schema.$ref) {
    const def = resolveRef(schema.$ref, root);
    if (!def) { errs.push(`${path}: unresolved $ref ${schema.$ref}`); return; }
    return validate(def, data, root, path, errs);
  }
  if (schema.oneOf) {
    const branchErrs = schema.oneOf.map((s) => { const e = []; validate(s, data, root, path, e); return e; });
    const passing = branchErrs.filter((e) => e.length === 0).length;
    if (passing !== 1) {
      errs.push(`${path}: matched ${passing} of ${schema.oneOf.length} oneOf branches (need exactly 1)`);
      // surface the closest branch's errors to aid debugging
      const closest = branchErrs.reduce((a, b) => (b.length < a.length ? b : a));
      closest.slice(0, 4).forEach((e) => errs.push(`  ↳ ${e}`));
    }
    return;
  }
  if (schema.const !== undefined && JSON.stringify(data) !== JSON.stringify(schema.const))
    errs.push(`${path}: expected const ${JSON.stringify(schema.const)}`);
  if (schema.enum && !schema.enum.some((v) => JSON.stringify(v) === JSON.stringify(data)))
    errs.push(`${path}: ${JSON.stringify(data)} not in enum [${schema.enum.join(', ')}]`);
  if (schema.type && !typeOk(schema.type, data)) {
    errs.push(`${path}: expected type ${schema.type}, got ${jsType(data)}`);
    return; // further checks assume the type
  }
  if (typeof data === 'string') {
    if (schema.pattern && !new RegExp(schema.pattern).test(data))
      errs.push(`${path}: "${trunc(data)}" does not match /${schema.pattern}/`);
    if (schema.minLength != null && data.length < schema.minLength)
      errs.push(`${path}: shorter than minLength ${schema.minLength}`);
  }
  if (typeof data === 'number' && schema.minimum != null && data < schema.minimum)
    errs.push(`${path}: ${data} < minimum ${schema.minimum}`);
  if (Array.isArray(data)) {
    if (schema.minItems != null && data.length < schema.minItems)
      errs.push(`${path}: fewer than minItems ${schema.minItems}`);
    if (schema.items) data.forEach((d, i) => validate(schema.items, d, root, `${path}[${i}]`, errs));
  }
  if (isObj(data)) {
    (schema.required || []).forEach((k) => { if (!(k in data)) errs.push(`${path}: missing required "${k}"`); });
    if (schema.properties)
      for (const [k, s] of Object.entries(schema.properties))
        if (k in data) validate(s, data[k], root, `${path}.${k}`, errs);
    if (schema.additionalProperties === false && schema.properties) {
      const allowed = new Set(Object.keys(schema.properties));
      for (const k of Object.keys(data))
        if (!allowed.has(k)) errs.push(`${path}: additional property "${k}" not allowed (strict)`);
    }
  }
}
function resolveRef(ref, root) {
  if (!ref.startsWith('#/')) return null;
  return ref.slice(2).split('/').reduce((o, seg) => (o ? o[seg] : undefined), root);
}
function typeOk(t, d) {
  if (Array.isArray(t)) return t.some((x) => typeOk(x, d)); // union type, e.g. ["string","null"]
  return t === 'object' ? isObj(d)
    : t === 'null' ? d === null
    : t === 'array' ? Array.isArray(d)
    : t === 'string' ? typeof d === 'string'
    : t === 'number' ? typeof d === 'number'
    : t === 'integer' ? Number.isInteger(d)
    : t === 'boolean' ? typeof d === 'boolean'
    : true;
}
const isObj = (d) => d !== null && typeof d === 'object' && !Array.isArray(d);
const jsType = (d) => (Array.isArray(d) ? 'array' : d === null ? 'null' : typeof d);
const trunc = (s) => (s.length > 50 ? s.slice(0, 47) + '…' : s);

// ---- run ----
const schema = JSON.parse(readFileSync(SCHEMA, 'utf8'));
let failed = 0, checked = 0;
const allFixtureDocs = [];

function check(label, data) {
  checked++;
  const errs = [];
  const sub = data && data.execution_hash ? schema.$defs.artifact : schema;
  validate(sub, data, schema, label, errs);
  if (errs.length) { failed++; console.error(`✗ ${label}`); errs.slice(0, 40).forEach((e) => console.error(`    ${e}`)); if (errs.length > 40) console.error(`    … +${errs.length - 40} more`); }
  else console.log(`✓ ${label}`);
}

console.log(`schema-validate · schema=${rel(SCHEMA)}\n`);

if (FIXTURES_DIR && existsSync(FIXTURES_DIR) && statSync(FIXTURES_DIR).isDirectory()) {
  for (const f of readdirSync(FIXTURES_DIR).filter((n) => n.endsWith('.json'))) {
    let doc; try { doc = JSON.parse(readFileSync(join(FIXTURES_DIR, f), 'utf8')); } catch { continue; }
    allFixtureDocs.push(doc);
    // fixtures may hold {artifact} or an array of expected artifacts; validate any object with execution_hash
    const candidates = doc.artifact ? [doc.artifact] : Array.isArray(doc) ? doc : doc.execution_hash ? [doc] : [];
    if (candidates.length === 0) console.error(`! ${f}: no artifact-shaped object found (expected execution_hash field) — value-only fixture, OK if its tool is not artifact-qualified`);
    candidates.forEach((a, i) => check(`fixture ${f}#${i}`, a));
  }
} else {
  console.error(`! fixtures dir not found: ${FIXTURES_DIR}`);
}

// ---- coverage gate: every artifact-qualified manifest tool needs a
// hash-bound fixture, or must be named on the shrinking ALLOWLIST ----
const qualified = artifactQualifiedTools();
let uncovered = 0, allowlisted = 0, covered = 0;
console.log(`\nartifact-qualified coverage · ${qualified.length} tools`);
for (const toolId of qualified) {
  const isCovered = allFixtureDocs.some((doc) => fixtureCoversTool(doc, toolId));
  if (isCovered) { covered++; console.log(`  ✓ ${toolId}`); continue; }
  if (ALLOWLIST.has(toolId)) { allowlisted++; console.log(`  ⏸ ${toolId} (allowlisted, no fixture yet)`); continue; }
  uncovered++; failed++;
  console.error(`  ✗ ${toolId}: artifact-qualified (has buildArtifact()) but no hash-bound fixture and not on ALLOWLIST`);
}
const stale = [...ALLOWLIST].filter((id) => !qualified.includes(id) || allFixtureDocs.some((doc) => fixtureCoversTool(doc, id)));
if (stale.length) console.error(`! ALLOWLIST has ${stale.length} stale entr${stale.length === 1 ? 'y' : 'ies'} (already covered or no longer artifact-qualified) — shrink it: ${stale.join(', ')}`);
console.log(`\n${covered}/${qualified.length} covered, ${allowlisted} allowlisted, ${uncovered} gap(s) not allowlisted.`);

function rel(p) { return p ? p.replace(resolve(HERE, '..'), '.') : p; }
console.log(`\n${checked} checked, ${failed} failed.`);
process.exit(failed ? 1 : 0);
