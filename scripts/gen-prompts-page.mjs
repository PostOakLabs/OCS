#!/usr/bin/env node
// gen-prompts-page.mjs — renders root prompts.html from the SSOT surfaces
// (PROMPTS-PAGE-1). Prompt text lives ONLY in tools/data/showcase-prompts.json
// and tools/data/tools-manifest.json; this script renders it. Re-run after
// editing the JSON:
//
//   node scripts/gen-prompts-page.mjs
//
// Section order per OCS-EXAMPLE-PROMPTS-MASTER_2026-09-10.md §3:
// Showcase · Deep dives · Everyday · By domain (V/M/U/G) · machine chains ·
// reading-path chains. Chrome copy follows the anti-AI-tell ban
// (STANDING-ORDERS 5): no em-dashes, no <em>/<i>, no rule-of-three filler.
// The three machine chain ids are the manifest chainsNote's set, verbatim.

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');

const sp = JSON.parse(readFileSync(resolve(REPO, 'tools/data/showcase-prompts.json'), 'utf8'));
const manifest = JSON.parse(readFileSync(resolve(REPO, 'tools/data/tools-manifest.json'), 'utf8'));

const prompts = sp.prompts;
const chains = manifest.chains ?? {};
const chainCount = Object.keys(chains).length;
const MACHINE_CHAINS = [
  { id: 'imbh-evidence-window', card: 'run-the-evidence-window',
    desc: 'Turns the ten published constraint measurements into the allowed IMBH mass window, with tension detection and gate rules in the result.' },
  { id: 'evidence-threshold-routing', card: 'threshold-routing-drill',
    desc: 'Routes a ln K evidence value through the pre-registered gate branches and prescribes the action.' },
  { id: 'accretion-eligibility-fastfail', card: 'fastfail-eligibility-gate',
    desc: 'Fast-fail eligibility gates for an accretion candidate, with gate rules and execution hashes in the result.' },
];

const GROUP_LABEL = {
  'showcase': 'Showcase',
  'persona': 'Deep dive',
  'everyday': 'Everyday',
  'imbh-evidence': 'By domain · IMBH evidence',
  'fermi-seti': 'By domain · Fermi / SETI',
  'education': 'By domain · Education',
  'agentic': 'By domain · Agentic and meta',
};

const DOORWAY_LEGEND = {
  R: 'hosted MCP worker (mcp.omegacentauri.me/mcp)',
  P: 'tool page with hash-state deeplink',
  Z: 'zkVM compute proof (risc0 groth16 receipt)',
  A: 'anchored evidence (RFC3161 + OpenTimestamps)',
  C: 'machine-executable worker chain via run_chain',
  N: 'narrative chain or scenario page',
  F: 'shipped fixtures and paper JSON',
  X: 'external data or MCP',
};

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function cardHtml(e) {
  const chips = (e.tools ?? []).map((t) => {
    if (t.endsWith('.html')) {
      const href = t.startsWith('tools/') ? `/${t}` : `/${t}`;
      return `<a class="chip" href="${esc(href)}">${esc(t.replace(/^tools\//, '').replace(/\.html$/, ''))}</a>`;
    }
    return `<a class="chip chip-worker" href="/mcp.html">${esc(t)}</a>`;
  }).join('\n      ');
  const pages = (e.tools ?? []).filter((t) => t.endsWith('.html'));
  const deeplink = pages.length === 1
    ? `\n      <a class="deeplink" href="/${esc(pages[0])}">Open tool page &#8599;</a>`
    : '';
  return `    <article class="card" id="${esc(e.id)}">
      <div class="card-eyebrow">${esc(GROUP_LABEL[e.group] ?? e.group)} · ${esc(e.doorways)}</div>
      <h3>${esc(e.title)}</h3>
      <p class="one-line">${esc(e.one_line)}</p>
      <div class="badges">
        <span class="badge-row">${[...(e.doorways ?? '')].filter((c) => DOORWAY_LEGEND[c]).map((c) => `<span class="badge" title="${esc(DOORWAY_LEGEND[c])}">${c}</span>`).join(' ')}</span>
        <span class="requires">Requires: ${(e.requires ?? []).map(esc).join(' · ')}</span>
      </div>
      <div class="chips">
      ${chips}
      </div>
      <div class="body-wrap">
        <pre class="prompt-body" id="body-${esc(e.id)}">${esc(e.body)}</pre>
        <button class="copy-btn" onclick="copyPrompt('body-${esc(e.id)}',this)">Copy prompt</button>
      </div>
      <div class="card-verify">Verify: ${esc(e.verify_surface)}${deeplink}</div>
    </article>`;
}

const byGroup = (g) => prompts.filter((p) => p.group === g).map(cardHtml).join('\n');

const chainLines = Object.entries(chains).map(([key, c]) => {
  // manifest `page` already carries the tools/ prefix; em-dashes in a few
  // manifest titles are rendered as middots (reader-facing copy ban) while
  // the manifest itself stays untouched.
  const page = typeof c === 'object' && c.page ? c.page : `tools/${key}.html`;
  const title = ((typeof c === 'object' && (c.title ?? key)) || key).replace(/ — /g, ' · ').replace(/—/g, '-');
  const register = typeof c === 'object' && c.register ? c.register : '';
  return `      <li><a href="/${esc(page)}">${esc(title)}</a>${register ? ` <span class="register">${esc(register)}</span>` : ''} <span class="register">reading path, not runnable</span></li>`;
}).join('\n');

const machineStrip = MACHINE_CHAINS.map((m) => `      <li><code>run_chain</code> &#8594; <code>${esc(m.id)}</code> · ${esc(m.desc)} <a href="/prompts.html#${esc(m.card)}">Drill: ${esc(m.card)}</a></li>`).join('\n');

const legend = Object.entries(DOORWAY_LEGEND).map(([k, v]) => `<span class="badge">${k}</span> ${esc(v)}`).join(' &nbsp;·&nbsp; ');

const html = `<!DOCTYPE html>
<!--
  Example Prompts Library
  Rendered by scripts/gen-prompts-page.mjs from tools/data/showcase-prompts.json
  and tools/data/tools-manifest.json. Edit the JSON, then re-run the generator.
  The Omega Centauri Society · omegacentauri.me
  Prose CC BY 4.0 · Code MIT
-->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Example Prompts Library · OCS</title>
<meta name="description" content="Thirty copy-paste verification prompts for the Omega Centauri Society estate: run the tools, check the hashes, verify without trusting us. Plus all 42 catalog chains as reading paths.">
<link rel="canonical" href="https://omegacentauri.me/prompts.html">
<meta name="theme-color" content="#0d0a24">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Space+Mono:ital,wght@0,400;0,700&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
<style>
:root{
  --void:#03020a;--nebula:#0d0a24;
  --teal-bright:#1dba90;--teal-glow:#4de8c0;--teal-dark:#042a24;
  --amber-glow:#ffc840;--purple-glow:#a080f0;--purple-bright:#7055d4;
  --text-primary:#e8e4ff;--text-secondary:#9890c0;--text-dim:#504870;
  --border-subtle:rgba(112,85,212,0.2);--border-teal:rgba(29,186,144,0.25)
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--void);color:var(--text-primary);font-family:'Crimson Pro',Georgia,serif;font-size:17px;line-height:1.8;min-height:100vh;background-image:radial-gradient(ellipse at 30% 0%,rgba(112,85,212,.08),transparent 50%),radial-gradient(ellipse at 80% 80%,rgba(29,186,144,.05),transparent 50%)}
a{color:var(--purple-glow);text-decoration:none}a:hover{color:var(--teal-glow)}
.nav{border-bottom:1px solid var(--border-subtle);background:rgba(7,5,21,.9);backdrop-filter:blur(8px);position:sticky;top:0;z-index:100}
.nav-inner{max-width:860px;margin:0 auto;padding:13px 24px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.nav-brand{font-family:'Orbitron',sans-serif;font-weight:900;font-size:14px;letter-spacing:.12em;color:var(--text-primary)}.nav-brand:hover{color:var(--amber-glow)}
.nav-cur{font-family:'Space Mono',monospace;font-size:11px;color:var(--text-secondary);margin-right:auto}
.nav-link{font-family:'Space Mono',monospace;font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--text-secondary)}.nav-link:hover{color:var(--teal-glow)}
.wrap{max-width:860px;margin:0 auto;padding:50px 24px 90px}
.hero-eyebrow{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--amber-glow);margin-bottom:10px}
h1{font-family:'Orbitron',sans-serif;font-weight:900;font-size:30px;line-height:1.1;margin-bottom:12px;background:linear-gradient(120deg,#e8e4ff 0%,var(--purple-glow) 55%,var(--teal-glow) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.lede{color:var(--text-secondary);font-size:18px;max-width:700px;margin-bottom:22px;line-height:1.65}
.info-bar{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:30px;font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:.07em}
.info-tag{padding:3px 10px;border-radius:20px;border:1px solid currentColor}
h2{font-family:'Orbitron',sans-serif;font-size:20px;font-weight:600;letter-spacing:.04em;margin:52px 0 8px;color:var(--text-primary)}
h2:first-of-type{margin-top:36px}
.section-note{color:var(--text-dim);font-size:14px;margin-bottom:20px;font-family:'Space Mono',monospace;letter-spacing:.03em}
h3.sub{font-family:'Space Mono',monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--teal-glow);margin:30px 0 14px}
.legend{background:rgba(112,85,212,.05);border:1px solid var(--border-subtle);border-radius:8px;padding:14px 18px;margin:0 0 10px;color:var(--text-secondary);font-size:14px;line-height:2.1}
.legend .badge{vertical-align:middle}
.card{background:rgba(13,10,36,.7);border:1px solid var(--border-subtle);border-radius:10px;padding:22px 22px 16px;margin-bottom:22px;transition:border-color .18s}
.card:hover{border-color:var(--purple-bright)}
.card:target{border-color:var(--amber-glow)}
.card-eyebrow{font-family:'Space Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-glow);margin-bottom:8px}
.card h3{font-family:'Orbitron',sans-serif;font-size:15px;font-weight:600;letter-spacing:.03em;line-height:1.4;margin-bottom:8px}
.one-line{color:var(--text-secondary);font-size:15px;line-height:1.6;margin-bottom:12px}
.badges{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:10px;font-family:'Space Mono',monospace;font-size:10px}
.badge{display:inline-block;padding:1px 7px;border-radius:9px;border:1px solid var(--border-teal);color:var(--teal-bright);background:rgba(29,186,144,.06);font-size:9px;letter-spacing:.08em}
.requires{color:var(--text-dim);letter-spacing:.05em}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.chip{display:inline-block;font-family:'Space Mono',monospace;font-size:9px;letter-spacing:.05em;padding:2px 9px;border-radius:10px;border:1px solid var(--border-subtle);color:var(--text-secondary)}
.chip:hover{border-color:var(--teal-glow);color:var(--teal-glow)}
.chip-worker{border-color:var(--border-teal);color:var(--teal-bright)}
.body-wrap{position:relative;margin-bottom:12px}
.prompt-body{background:rgba(26,16,64,.35);border:1px solid rgba(112,85,212,.3);border-radius:5px;padding:1rem 1.2rem;font-family:'Crimson Pro',serif;font-size:.95rem;color:var(--text-secondary);white-space:pre-wrap;margin:0;line-height:1.65;overflow-x:auto}
.copy-btn{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.07em;text-transform:uppercase;padding:6px 14px;border-radius:6px;border:1px solid var(--border-teal);color:var(--teal-glow);background:rgba(29,186,144,.06);cursor:pointer;margin-top:10px}
.copy-btn:hover{background:rgba(29,186,144,.18)}
.card-verify{color:var(--text-dim);font-size:13px;font-family:'Space Mono',monospace;letter-spacing:.03em;line-height:1.9}
.deeplink{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.07em;text-transform:uppercase;padding:4px 12px;border-radius:6px;border:1px solid var(--border-subtle);color:var(--purple-glow);margin-left:10px}
.deeplink:hover{border-color:var(--amber-glow);color:var(--amber-glow)}
.machine-strip{list-style:none;padding:0}
.machine-strip li{background:rgba(4,42,36,.4);border:1px solid var(--border-teal);border-radius:8px;padding:12px 16px;margin-bottom:10px;color:var(--text-secondary);font-size:15px;line-height:1.7}
.machine-strip code{font-family:'Space Mono',monospace;font-size:12px;color:var(--teal-glow)}
.machine-strip a{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.07em;text-transform:uppercase;margin-left:8px;white-space:nowrap}
.chain-list{list-style:none;padding:0;columns:1}
@media(min-width:700px){.chain-list{columns:2;column-gap:28px}}
.chain-list li{break-inside:avoid;margin-bottom:9px;font-size:15px;line-height:1.55;color:var(--text-secondary)}
.register{display:inline-block;font-family:'Space Mono',monospace;font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);border:1px solid var(--border-subtle);border-radius:8px;padding:0 6px;margin-left:6px;vertical-align:1px}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border-subtle);font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:.05em;text-align:center;line-height:1.9}
footer a{color:var(--text-secondary)}footer a:hover{color:var(--teal-glow)}
</style>
</head>
<body>
<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-brand">&#9658; OCS</a>
    <span class="nav-cur">Example Prompts Library</span>
    <a href="/" class="nav-link">&larr; Main portal</a>
    <a href="/tools/" class="nav-link">Tools</a>
    <a href="/mcp.html" class="nav-link">MCP</a>
    <a href="/paper.html" class="nav-link">Papers</a>
  </div>
</nav>
<div class="wrap">
  <div class="hero-eyebrow">Verification-first copy-paste prompts</div>
  <h1>Example Prompts Library</h1>
  <p class="lede">Thirty prompts that run this estate's tools and check its claims. Each one ends at a surface you can verify without trusting us: your own hash recompute, an independent verifier, or the primary literature. Paste one into any capable assistant, or work it by hand.</p>
  <div class="info-bar">
    <span class="info-tag">${prompts.length} prompts</span>
    <span class="info-tag">${Object.keys(GROUP_LABEL).length} groups</span>
    <span class="info-tag">${chainCount} reading chains</span>
    <span class="info-tag">${MACHINE_CHAINS.length} machine chains</span>
    <span class="info-tag">SSOT: tools/data/showcase-prompts.json</span>
  </div>
  <div class="legend">
    ${legend}
  </div>

  <h2>Showcase</h2>
  <p class="section-note">The flagship computations, proven end to end.</p>
${byGroup('showcase')}

  <h2>Deep dives</h2>
  <p class="section-note">Long-form adversarial tours for researchers who want to break something.</p>
${byGroup('persona')}

  <h2>Everyday</h2>
  <p class="section-note">Short tasks a first-time reader can run in minutes.</p>
${byGroup('everyday')}

  <h2>By domain</h2>
  <h3 class="sub">IMBH evidence</h3>
${byGroup('imbh-evidence')}
  <h3 class="sub">Fermi / SETI</h3>
${byGroup('fermi-seti')}
  <h3 class="sub">Education</h3>
${byGroup('education')}
  <h3 class="sub">Agentic and meta</h3>
${byGroup('agentic')}

  <h2>Machine chains</h2>
  <p class="section-note">Three worker chains are machine-executable via <code>run_chain</code> on mcp.omegacentauri.me/mcp, with structured inputs and gate rules in the result. These are the only runnable chains; everything below them is a reading path.</p>
  <ul class="machine-strip">
${machineStrip}
  </ul>

  <h2>Catalog chains (reading paths)</h2>
  <p class="section-note">${chainCount} narrative chains from tools-manifest.json. A human reader (or an agent reading prose) follows them page by page; they are not runnable pipelines.</p>
  <ul class="chain-list">
${chainLines}
  </ul>
</div>
<footer>
  &#9658; THE OMEGA CENTAURI SOCIETY &nbsp;&middot;&nbsp;
  <a href="/">omegacentauri.me</a> &nbsp;&middot;&nbsp;
  <a href="/tools/">Tools</a> &nbsp;&middot;&nbsp;
  <a href="/mcp.html">MCP Connector</a> &nbsp;&middot;&nbsp;
  <a href="/paper.html">Papers</a>
  <br>
  Prompt text is data: <a href="/tools/data/showcase-prompts.json">tools/data/showcase-prompts.json</a> is the single source of truth, and this page is generated from it.
</footer>
<script>
function copyPrompt(id,btn){var el=document.getElementById(id);if(!el)return;var t=el.textContent;
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){done(btn)},function(){fallback(t,btn)})}else{fallback(t,btn)}}
function fallback(t,btn){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy')}catch(e){}document.body.removeChild(ta);done(btn)}
function done(btn){var old=btn.textContent;btn.textContent='Copied';setTimeout(function(){btn.textContent=old},1400)}
</script>
</body>
</html>
`;

writeFileSync(resolve(REPO, 'prompts.html'), html);
console.log(`prompts.html written: ${prompts.length} prompt cards, ${chainCount} chain one-liners, ${MACHINE_CHAINS.length} machine chains.`);
