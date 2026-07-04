// syntax-check.mjs — parse every inline <script> in the site's tool/root HTML
// and report any SyntaxError. This is the check the Node hash-gates DON'T do:
// it confirms edits (comma fixes, async refactors, helper injection) didn't
// break JavaScript parsing in any page. Uses node:vm `new vm.Script(code)`
// which PARSES with classic-<script> (Program) semantics — exactly how a
// browser parses an inline classic script — and throws on a real SyntaxError
// without executing.
//
// Run:  node scripts/syntax-check.mjs
// Exit non-zero if any script fails to parse.
//
// Zero dependencies. Scans: tools/*.html (all ~98 calculator/workflow/scenario
// pages) and root *.html (index, faq, proposals, etc.) — OCS's file layout has
// no framework/build step, so every page is a standalone HTML file with inline
// <script> blocks.
//
// Adapted from AINumbers repo/chaingraph/kernels/syntax-check.mjs
// (Phase B slice S-B1, OCG 0.2→0.8 upgrade).

import vm from 'node:vm';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');

function htmlFiles() {
  const out = [];
  const add = (dir, filter) => {
    const abs = resolve(REPO, dir);
    if (!existsSync(abs)) return;
    for (const f of readdirSync(abs)) {
      if (f.endsWith('.html') && (!filter || filter(f))) out.push(resolve(abs, f));
    }
  };
  add('tools');   // ALL catalog tools (calculators, workflow-*, scenario-*, hubs)
  add('.');       // root pages: index, faq, membership, advisors, proposals, proposal_*, ...
  return out;
}

// Extract classic inline <script> bodies. Skip src=, type=module, JSON-LD, importmap.
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
    if (type && !['text/javascript', 'application/javascript', 'module'].includes(type)) continue; // skip ld+json, importmap, etc.
    if (type === 'module') continue; // new vm.Script can't represent a module; modules are not used by these tools
    if (!body.trim()) continue;
    scripts.push(body);
  }
  return scripts;
}

let failed = 0, filesChecked = 0, scriptsChecked = 0;
for (const file of htmlFiles()) {
  const html = readFileSync(file, 'utf8');
  const scripts = inlineScripts(html);
  filesChecked++;
  let fileBad = false;
  scripts.forEach((code, i) => {
    scriptsChecked++;
    try {
      new vm.Script(code, { filename: relative(REPO, file) + `#script${i + 1}` }); // parse-only (compile); throws SyntaxError on bad JS
    } catch (e) {
      if (e instanceof SyntaxError) {
        if (!fileBad) { console.error(`\n✗ ${relative(REPO, file)}`); fileBad = true; }
        console.error(`    script #${i + 1}: ${e.message}`);
        failed++;
      }
      // non-SyntaxError (shouldn't happen for parse-only) is ignored
    }
  });
}

console.log(`\nChecked ${scriptsChecked} inline scripts across ${filesChecked} files.`);
if (failed === 0) { console.log('✓ no JavaScript syntax errors in any page.'); process.exit(0); }
console.error(`✗ ${failed} script(s) failed to parse — fix before pushing.`);
process.exit(1);
