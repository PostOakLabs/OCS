// lint-forbidden-hash.mjs — CI/pre-deploy guard. Fails (exit 1) if any live
// OCS ChainGraph-qualified tool reintroduces a non-canonical hashing pattern.
// This is the regression gate: once a tool is on the single OCG canonical
// scheme, this keeps it there. Wired into deploy.yml Job 1 (validate).
//
// Usage: node scripts/lint-forbidden-hash.mjs
//
// Best-practice basis: a non-deterministic / mislabeled hash must never ship
// in a product whose value proposition is verifiable hashing. Cheapest
// possible guard = ban the byte-patterns that produce known-wrong schemes,
// plus a positive check that the canonical kernel functions are present.
//
// Registry note: OCS's tools/data/chaingraph.json is a DICT keyed by tool
// slug (not an array of nodes like AINumbers' chaingraph.json). Each entry's
// local HTML file is resolved as tools/<slug>.html (the OCS URL convention is
// https://omegacentauri.me/tools/<slug>.html — same slug, no per-entry `url`
// field in this registry, unlike AINumbers).
//
// Adapted from AINumbers repo/chaingraph/kernels/lint-forbidden-hash.mjs
// (Phase B slice S-B1, OCG 0.2→0.8 upgrade).

import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const REGISTRY_PATH = resolve(REPO, 'tools', 'data', 'chaingraph.json');
const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'));

// Banned patterns -> human reason. The OCG-CANON marker block is explicitly allowed.
// NOTE: a literal "sha256:" prefix ON THE EXECUTION_HASH FIELD is banned for OCS —
// unlike some AINumbers artifacts, OCS's frozen v0.4 envelope uses BARE HEX (no
// prefix) for execution_hash, per repo/tools/*.html convention (see constraint-stacker.html).
const BANNED = [
  // Scheme A (array-replacer): JSON.stringify(<anything>, Object.keys(<anything>).sort()) — the 2nd arg is a
  // recursive-property allowlist, NOT a sort, so it collapses nested data into an input-independent hash.
  // There is no legitimate use of Object.keys().sort() as a JSON.stringify replacer — canonical OCG sorts
  // INSIDE cgCanon, then JSON.stringify(canon) with no replacer.
  { re: /JSON\.stringify\([\s\S]{0,200}?,\s*Object\.keys\([\s\S]{0,160}?\)\.sort\(\)\s*\)/, why: 'Scheme A: array-replacer collapses nested data (input-independent hash). Use cgCanon: JSON.stringify(cgCanon({policy_parameters, output_payload})).' },
  // Scheme C: a fake/32-bit hash function (simpleHash / FNV / djb2) mislabeled sha256 and fed into execution_hash.
  { re: /function\s+simpleHash\s*\(/, why: 'Scheme C: simpleHash is a 32-bit hash mislabeled "sha256:". Not SHA-256. Use real crypto.subtle SHA-256 via executionHash().' },
  { re: /function\s+(fnv1a|djb2)Hash\s*\(/i, why: 'Scheme C: FNV/djb2 is a 32-bit hash, not SHA-256. Use real crypto.subtle SHA-256 via executionHash().' },
  // Scheme E (no canon): JSON.stringify({policy_parameters, output_payload}) hashed WITHOUT a recursive
  // key-sort. The canonical form wraps it: JSON.stringify(cgCanon({...})) — which is `stringify(cgCanon(`
  // not `stringify({`, so this only fires on the unwrapped (wrong) form.
  { re: /JSON\.stringify\(\s*\{\s*policy_parameters\b/, why: 'Scheme E: non-canonical preimage — {policy_parameters, output_payload} hashed without recursive key-sort. Wrap it: JSON.stringify(cgCanon({policy_parameters, output_payload})).' },
];

// Positive checks: each artifact tool MUST define the canonical kernel functions,
// and MUST NOT emit a 'sha256:' + prefix on the artifact execution_hash field.
// (Intentionally NOT checking that canonicalPreimage's keys are exactly
// policy_parameters/output_payload — velocity-dispersion uses shorthand keys
// and is being fixed in a later slice; do not flag it here.)
const POSITIVE = [
  { name: 'canonicalPreimage', re: /function\s+canonicalPreimage\s*\(/, why: 'missing canonicalPreimage() — artifact tool must define the vendored OCG canonicalizer.' },
  { name: 'executionHash', re: /function\s+executionHash\s*\(/, why: 'missing executionHash() — artifact tool must define the vendored OCG hash function.' },
];
const SHA256_PREFIX_RE = /execution_hash\s*:\s*(['"`])sha256:['"`]\s*\+/;

let violations = 0, checked = 0;
for (const [slug, entry] of Object.entries(registry.tools ?? {})) {
  if (!entry.artifact_qualified) continue;
  const abs = resolve(REPO, 'tools', `${slug}.html`);
  if (!existsSync(abs)) {
    console.error(`✗ ${slug}\n    artifact_qualified but tools/${slug}.html not found`);
    violations++;
    continue;
  }
  checked++;
  const src = readFileSync(abs, 'utf8');
  let toolBad = false;

  for (const b of BANNED) {
    if (b.re.test(src)) {
      console.error(`✗ ${slug}\n    ${b.why}`);
      violations++;
      toolBad = true;
    }
  }
  for (const p of POSITIVE) {
    if (!p.re.test(src)) {
      console.error(`✗ ${slug}\n    ${p.why}`);
      violations++;
      toolBad = true;
    }
  }
  if (SHA256_PREFIX_RE.test(src)) {
    console.error(`✗ ${slug}\n    execution_hash emitted with a 'sha256:' + prefix — OCS convention is bare hex (no prefix).`);
    violations++;
    toolBad = true;
  }

  if (!toolBad) console.log(`✓ ${slug}`);
}

console.log(`\n${checked} artifact-qualified tool(s) checked.`);
if (violations === 0) {
  console.log('✓ hash lint clean — no forbidden canonicalization/hash patterns in any live artifact tool.');
  process.exit(0);
}
console.error(`\n✗ ${violations} forbidden-hash violation(s).`);
process.exit(1);
