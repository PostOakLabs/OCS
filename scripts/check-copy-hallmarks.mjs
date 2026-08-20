#!/usr/bin/env node
/**
 * check-copy-hallmarks.mjs — gate against AI-writing hallmarks in reader-facing copy.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * PROVENANCE / SHARED-INFRA LINEAGE (standing order 9)
 *   Vendored from: AINumbers/repo/scripts/check-copy-hallmarks.mjs
 *   Source commit: 555a032f028be6f2e86e10579c253f552726aa5e
 *                  ("copy-hallmarks: flag \"It's not X, it's Y\" two-tone pivot", #520)
 *   Vendored on:   2026-07-23  (OCS-COPY-GATE, session d31bd1f6)
 *   Rule: single lineage — fix upstream (AINumbers) FIRST and re-vendor here.
 *         Do NOT diverge the DETECTION LOGIC (the regex constants + parser).
 *         Only CONFIG and two POLICY deviations below are OCS-specific.
 *
 * OCS CONFIG/POLICY DEVIATIONS FROM UPSTREAM (config only, logic identical):
 *   1. FILE SCOPE — upstream recurses every *.html under the repo. OCS gates
 *      only reader-facing HTML: root-level *.html + tools/*.html, plus README.md
 *      (scanned as markdown text: em-dash + category-3 prose tells only). Subdirs
 *      (papers/, archive/, latex/, "Claude Design demo/") are NOT reader-facing
 *      site copy and are out of scope.
 *   2. JARGON NEUTRALIZED — upstream bans AINumbers build codes ("Wave N",
 *      "W-A".."W-F", "D0"). These cannot describe OCS content and "D0"/"Wave N"
 *      risk false positives on a science site (wave physics, spectral terms), so
 *      JARGON is emptied here. The code path is retained (jargon count stays 0).
 *   3. ITALICS = BASELINE+RATCHET, not zero-tolerance. Upstream treats body
 *      italics as a zero-tolerance category-3 hit. OCS's anti-AI-tell keep-policy
 *      (CLAUDE.md; memory ocs-anti-ai-tell-style) LEGITIMATELY retains some body
 *      <em>: run-in paragraph labels ("Tidal stress."), first-use technical terms
 *      the text reuses, and titles. So OCS snapshots body italics as a baseline
 *      and ratchets down, exactly like em-dash and bold. Italic/bold INSIDE
 *      headings (h1-h6) stays ZERO-TOLERANCE (category 3) — a styled heading is
 *      an unambiguous AI tell with no legitimate keep-case.
 *   4. NO MANIFEST/CHAINGRAPH GATING — upstream also gates chaingraph.json
 *      descriptions (served over MCP). OCS's equivalent is
 *      tools/data/tools-manifest.json; per the WU, SCOPE = reader-facing
 *      HTML/README only. Manifest gating is left as a possible follow-up WU.
 *   5. PAPER-SPECIFIC AI-TELL CATALOGUE (OCS-TELL-GATE-1, 2026-08-20) — vendors
 *      the pattern catalogue from board/notes/AI-TELL-AUDIT-1.md §4.3. These
 *      checks are SCOPED TO THE 9-PAPER CORPUS ONLY (repo/papers/source/*.tex +
 *      each paper's matching full-text HTML page — see PAPERS below), NOT the
 *      general reader-facing HTML scan. Reason: the audit's heading-formula
 *      class ("What this tool does", "Why X matters") is universal HOUSE STYLE
 *      on the ~100+ tools/*.html calculator pages — gating it site-wide would
 *      fail every tool page. Exceptions (structural colon headings, pre-reg
 *      ledgers, run-in labels, two documented deliberate keeps) are catalogued
 *      in board/notes/COPY-EXCEPTIONS.md for human reference; the zero-tolerance
 *      regexes below are already narrow enough (require the "What/Why ... ,
 *      and ..." pivot or a trailing "?") that none of the exceptions trip them.
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Hard-fails on:
 *   1. Em-dashes (—) in the human-visible text of any in-scope HTML page or
 *      README.md (script/style/pre/code/HTML-comments excluded). Baseline+ratchet.
 *   2. (JARGON neutralized for OCS — see deviation 2.)
 *   3. ANTI-AI-TELL copy (Tim 2026-07-11, PERMANENT — memory
 *      `feedback-anti-ai-tell-copy-ban` / standing order 5): italic/bold INSIDE
 *      headings (h1-h6), "not just X but" / "isn't just" / "more than just",
 *      dramatic-fragment openers ("The result?"), validation-phrasing ("you're
 *      not alone/imagining"), "it's not X, it's Y" pivots, a filler-vocab
 *      denylist (delve, tapestry, testament to, quiet(ly) X, seamless,
 *      game-changer, elevate your X, unlock potential, "it's worth noting", "in
 *      today's fast-paced"), and decorative emoji in HEADERS. Zero-tolerance,
 *      no baseline.
 *   4. Bold and body ITALICS emphasis in visible prose (h1-h6 headings and
 *      th/dt/label/legend/button excluded) — baseline+ratchet, snapshotted via
 *      --update, no file may exceed its baselined count, files absent from the
 *      baseline must be clean.
 *
 * The category-3 ANTI-AI-TELL patterns carry NO baseline — zero tolerance
 * everywhere, since this WU swept and fixed every pre-existing hit first.
 *
 * SCOPE DECISION — body-prose emoji is ADVISORY, not blocking (inherited from
 * upstream): tool pages use single-glyph emoji as functional UI chrome
 * (save/export/copy icons, status markers). Header emoji IS blocking.
 *
 * Usage:
 *   node scripts/check-copy-hallmarks.mjs            # gate (preflight + CI)
 *   node scripts/check-copy-hallmarks.mjs --update   # regenerate the baseline
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { resolve, dirname, relative, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BASELINE_PATH = resolve(REPO, 'scripts', 'copy-hallmarks-baseline.json');
const PAPER_BASELINE_PATH = resolve(REPO, 'scripts', 'copy-hallmarks-paper-baseline.json');
const UPDATE = process.argv.includes('--update');

const EMDASH = /—/g;
// JARGON neutralized for OCS (deviation 2) — code path retained, never fires.
const JARGON = [];
// Blocking, zero-tolerance, no baseline (COPYTELL-SWEEP-1) — HIGH-PRECISION twotone family.
const TWOTONE_HIGHPRECISION = /\b(?:is|are|was|were) not (?:a|an|the )?[\w-]+\.\s+(?:It|They|This|That) (?:is|are)\b/g;
// Advisory only, PERMANENTLY — heuristic, catches legitimate 3-item lists too often for a hard gate.
const TRIAD = /\b\w+,\s*\w+,\s*(?:and|&)\s*\w+\b/g;
// Structural UI chrome exempt from the bold/italics count (not prose emphasis) —
// plus tabular/form labels. <button> is already stripped upstream via BUTTON_TAG.
const STRUCTURAL_BOLD_EXEMPT = /<(th|dt|label|legend)\b[^>]*>[\s\S]*?<\/\1>/gi;
const BOLD = /<(b|strong)\b[^>]*>[^<]+<\/\1>/gi;
const ITALIC = /<(em|i)\b[^>]*>[^<]+<\/\1>/gi;

// --- ANTI-AI-TELL BAN (Tim 2026-07-11, PERMANENT — feedback-anti-ai-tell-copy-ban) ---
// Blocking, zero-tolerance, no baseline. Each entry: [regex, label].
const NOTJUSTBUT = [
  [/\bnot\s+just\b(?:(?!\bbut\b)[^.?!]){0,80}\bbut\b/gi, '"not just X but" construction'],
  [/\bisn['’]?t\s+just\b/gi, '"isn\'t just"'],
  [/\bmore\s+than\s+just\b/gi, '"more than just"'],
];
const DRAMATIC_FRAGMENT = /\bThe (?:result|catch|takeaway|verdict|kicker|bottom line)\?/gi;
const VALIDATION_PHRASING = /\byou['’]?re\s+not\s+(?:alone|imagining\s+(?:it|things))\b/gi;
// The comma-pivot two-tone cliché: "It's not X, it's Y" anchored on a leading
// pronoun so factual sentences starting with a noun don't trip it.
const TWOTONE_COMMA = /\b(?:it['’]?s|it is|this is|that['’]?s|there['’]?s)\s+not\s+[^,.!?]{1,70},\s+(?:it['’]?s\s+about|it['’]?s|it is|they['’]?re)\b/gi;
const FILLER_VOCAB = [
  [/\bdelv(?:e|es|ed|ing)\b/gi, 'delve'],
  [/\btapestr(?:y|ies)\b/gi, 'tapestry'],
  [/\btestament\s+to\b/gi, 'testament to'],
  [/\bquiet(?:ly)?\s+(?:revolution|shift|force|power|evolution)\b/gi, 'quiet(ly) X'],
  [/\bseamless(?:ly)?\b/gi, 'seamless'],
  [/\bgame[\s-]?chang(?:er|ing)\b/gi, 'game-changer'],
  [/\belevat(?:e|es|ed|ing)\s+(?:your|our|its|their)\s+\w+/gi, 'elevate your/our/its X'],
  [/\bunlock(?:s|ed|ing)?\s+(?:your\s+|the\s+full\s+|new\s+|greater\s+)?(?:potential|value|growth|opportunit(?:y|ies)|insight(?:s)?|power|possibilit(?:y|ies))\b/gi, 'unlock potential/value/growth (marketing sense)'],
  [/\bit['’]?s\s+worth\s+noting\b/gi, "it's worth noting"],
  [/\bin\s+today['’]?s\s+fast-paced\b/gi, "in today's fast-paced"],
];
// Overuse tells: individually legit words, but repeating them across a page reads
// as an AI hallmark. A file NOT in the baseline may use each at most OVERUSE_CAP
// times; legacy debt is shielded by the baseline (ratchet — counts only go down).
const OVERUSE_CAP = 1;
const OVERUSE_VOCAB = [
  [/\bhonest(?:ly|y)?\b/gi, 'honest'],
];
// Emoji ranges (misc symbols, emoticons, transport, supplemental, dingbats).
const EMOJI = /[\u{2600}-\u{27BF}\u{1F300}-\u{1FAFF}]/gu;
// Functional UI/status glyphs exempt from the emoji ban. OCS adds ☉ (U+2609,
// the astronomical Sun / solar-mass unit, used pervasively as "M☉") — a science
// unit symbol, not decorative narrative emoji (config adaptation, deviation 2).
const EMOJI_UI_EXEMPT = new Set(['✓', '✗', '✔', '✔️', '❌', '✅', '⚠', '⚠️', '🔒', '🔏', '🚫', '☑', '☑️', '➡', '➡️', '→', '⭐', '★', '☆', '❓', '❗', '‼', '⏳', '⏱', '⏱️', '☉']);
function nonExemptEmoji(text) {
  return (text.match(EMOJI) || []).filter((ch) => !EMOJI_UI_EXEMPT.has(ch));
}
// Elements exempt from the emoji ban — status/count badges and interactive controls.
const BADGE_ELEMENT = /<(span|div|a|p)\b[^>]*\bclass\s*=\s*["'][^"']*\b(?:badge|pill|chip)\b[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi;
const CONTROL_ELEMENT = /<(button|div|span)\b[^>]*\bclass\s*=\s*["'][^"']*\b(?:btn|icon)\b[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi;
const BUTTON_TAG = /<button\b[^>]*>[\s\S]*?<\/button>/gi;

// --- PAPER AI-TELL CATALOGUE (OCS-TELL-GATE-1, AI-TELL-AUDIT-1 §4.3) ---
// Scoped to the 9-paper corpus only — see deviation 5 above.
const PAPERS = [
  { key: 'accretion-limit', tex: 'papers/source/accretion-limit-paper.tex', html: 'omega-centauri-accretion-limit.html' },
  { key: 'axi-note', tex: 'papers/source/axi-note.tex', html: 'omega-centauri-axi-note.html' },
  { key: 'campaign', tex: 'papers/source/campaign-paper.tex', html: 'omega-centauri-technosignature-campaign.html' },
  { key: 'census', tex: 'papers/source/census-paper.tex', html: 'omega-centauri-xray-census.html' },
  { key: 'economics', tex: 'papers/source/economics-paper.tex', html: 'inward-migration-economics.html' },
  { key: 'engineered-imbh', tex: 'papers/source/engineered-imbh-paper.tex', html: 'engineered-imbh-systems.html' },
  { key: 'inward-review', tex: 'papers/source/inward-review.tex', html: 'inward-migration-fermi-paradox-review.html' },
  { key: 'mass-tension', tex: 'papers/source/mass-tension-paper.tex', html: 'omega-centauri-mass-tension.html' },
  { key: 'mth', tex: 'papers/source/mth-paper.tex', html: 'macro-transcension-hypothesis.html' },
];

// Class 1 + NEW-A + NEW-B: heading formula (pivot or interrogative) — zero-tolerance.
const HEADING_FORMULA = [
  /\b(What|Why)\b.*?(,\s*and\s*(what|why)|\?)/i,
  /,\s+(and\s+(what|why|its)|(reported|surfaced|scored)\s+(and|rather than))/i,
];
// NEW-D: idiom family — zero-tolerance, no legitimate use in this corpus.
const IDIOM_FAMILY = /earns? (its|their) (keep|place)|pays its way|paid for itself/gi;
// NEW-C: verbless numeric-announce fragment — zero-tolerance. Anchored at a
// sentence boundary (start-of-text or after .!?) since HTML prose has no
// reliable line breaks per sentence.
const VERBLESS_FRAGMENT = /(?:^|[.!?]\s+)(One|Two|Three|Four|Five|Six)\s+[A-Za-z-]+\.(?=\s|$)/g;
// Pre-existing debt found while wiring this check (OCS-TELL-GATE-1, 2026-08-20):
// "Three caveats." in inward-review.tex/.html predates this gate and was never
// covered by AI-TELL-FIX-1..4 (those batches fixed HEADING/idiom findings, not
// the NEW-C verbless form, which AI-TELL-AUDIT-1 only *recommended* banning).
// Per the WU's hard rule ("never the paper text" — this is an editorial call,
// not a build-script fix), this exact known string is exempted here rather than
// silently weakening the pattern; tracked in board/notes/COPY-EXCEPTIONS.md and
// queued as follow-up OCS-TELL-GATE-1-FOLLOWUP. Any OTHER verbless fragment,
// including a new one in this same paper, still fails.
const VERBLESS_KNOWN_DEBT = {
  'inward-review': ['Three caveats.'],
};
// NEW-C: numeric-announce opener — ratchet, per-file budget 3.
const NUMERIC_OPENER = /\b(One|Two|Three|Four|Five|Six)\s+(things?|statements?|reasons?|consequences?|features?|caveats?|checks?|asymmetries|conventions?|considerations?|principles?|corollaries|questions?|effects?|explanations?|regimes?|further)\b/g;
const NUMERIC_OPENER_BUDGET = 3;
// Class 2: negation-definition — ratchet.
const NEGATION_DEFINITION = [
  /\bis not (a|an|the)\b[^.;]{0,60}; it is\b/gi,
  /\bnot (just|merely|only)\b[^.;]{0,80}\bbut\b/gi,
  /\bnot because\b[^.;]{0,60}\bbut because\b/gi,
];
// Class 5: anthropomorphized machinery — ratchet.
const ANTHROPOMORPHISM = /\b(the (gate|module|leg|model|analysis|instrument|pipeline|data)) (saw|says so|behaved|did its job|delivered|pays|spoke)\b/gi;
// Class 8: hedge adverbs — ratchet (audit: currently ~0-2, ratchet toward 0).
const HEDGE_ADVERB = /\b(arguably|importantly|crucially|notably|it is tempting to)\b/gi;
// NEW-E: cross-paper duplicated frames — zero-tolerance, new check kind: flag
// when a frame matches in MORE THAN ONE DISTINCT PAPER (a paper's own .tex and
// its mirrored .html both matching is the same paper, not a duplicate).
const DUP_FRAMES = [
  [/Whatever (occupies|sits at|lies at) the cent(er|re)/gi, 'Whatever occupies/sits at/lies at the cent(er|re)…'],
  [/Claims and non-claims/gi, '"Claims and non-claims" heading'],
];

/** Strip LaTeX comments: everything from an unescaped % to end of line. */
function stripTexComments(tex) {
  return tex.split('\n').map((line) => {
    let out = '';
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '%' && line[i - 1] !== '\\') break;
      out += line[i];
    }
    return out;
  }).join('\n');
}

/** \section{...} and \subsection{...} heading bodies (tex). */
function texHeadings(tex) {
  const out = [];
  const re = /\\(?:sub)?section\*?\{([^}]*)\}/g;
  let m;
  while ((m = re.exec(tex))) out.push(m[1]);
  return out;
}

/** <h2>/<h3> heading text, tags stripped (paper full-text pages only). */
function paperHtmlHeadings(prose) {
  const out = [];
  const re = /<h[23]\b[^>]*>([\s\S]*?)<\/h[23]>/gi;
  let m;
  while ((m = re.exec(prose))) out.push(m[1].replace(/<[^>]+>/g, ' '));
  return out;
}

function countAll(text, res) {
  const list = Array.isArray(res) ? res : [res];
  let n = 0;
  for (const re of list) n += (text.match(re) || []).length;
  return n;
}

/** Count VERBLESS_FRAGMENT hits, excluding this paper's documented known-debt strings. */
function countVerbless(text, paperKey) {
  const debt = new Set(VERBLESS_KNOWN_DEBT[paperKey] || []);
  const matches = text.match(VERBLESS_FRAGMENT) || [];
  let n = 0;
  for (const m of matches) {
    const trimmed = m.replace(/^[.!?]\s+/, '');
    if (!debt.has(trimmed)) n++;
  }
  return n;
}

/** Scan one paper (tex text + html body text) for the AI-tell catalogue. */
function scanPaper(p, texRaw, htmlRaw) {
  const tex = stripTexComments(texRaw);
  const htmlProse = proseHtml(htmlRaw);
  const htmlText = visibleText(htmlRaw);

  const headings = [...texHeadings(tex), ...paperHtmlHeadings(htmlProse)];
  let headingFormula = 0;
  const headingHits = [];
  for (const h of headings) {
    if (HEADING_FORMULA.some((re) => re.test(h))) {
      headingFormula++;
      headingHits.push(h.trim().slice(0, 80));
    }
  }

  const bodies = [tex, htmlText];
  let idiom = 0, verbless = 0, negdef = 0, anthro = 0, hedge = 0, numOpener = 0;
  for (const b of bodies) {
    idiom += countAll(b, IDIOM_FAMILY);
    verbless += countVerbless(b, p.key);
    negdef += countAll(b, NEGATION_DEFINITION);
    anthro += countAll(b, ANTHROPOMORPHISM);
    hedge += countAll(b, HEDGE_ADVERB);
    numOpener += countAll(b, NUMERIC_OPENER);
  }

  const dupFrameMatches = {};
  for (const [re, label] of DUP_FRAMES) {
    if (tex.match(re) || htmlText.match(re)) dupFrameMatches[label] = true;
  }

  return { headingFormula, headingHits, idiom, verbless, negdef, anthro, hedge, numOpener, dupFrameMatches };
}

/** In-scope reader-facing HTML: root-level *.html + tools/*.html (deviation 1). */
function scopedHtmlFiles() {
  const out = [];
  for (const name of readdirSync(REPO)) {
    if (name.endsWith('.html') && statSync(join(REPO, name)).isFile()) out.push(join(REPO, name));
  }
  const toolsDir = join(REPO, 'tools');
  if (existsSync(toolsDir) && statSync(toolsDir).isDirectory()) {
    for (const name of readdirSync(toolsDir)) {
      if (name.endsWith('.html') && statSync(join(toolsDir, name)).isFile()) out.push(join(toolsDir, name));
    }
  }
  return out;
}

/** Strip script/style/pre/code bodies + HTML comments, keep other tags intact. */
function proseHtml(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<pre\b[\s\S]*?<\/pre>/gi, ' ')
    .replace(/<code\b[\s\S]*?<\/code>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(BADGE_ELEMENT, ' ')
    .replace(BUTTON_TAG, ' ')
    .replace(CONTROL_ELEMENT, ' ');
}

/** Human-visible text: proseHtml() with all remaining tags stripped too. */
function visibleText(html) {
  return proseHtml(html).replace(/<[^>]+>/g, ' ');
}

/** Header-only visible text (tags stripped) — for the emoji-in-header check. */
function headerText(prose) {
  const out = [];
  const re = /<h[1-6]\b[^>]*>([\s\S]*?)<\/h[1-6]>/gi;
  let m;
  while ((m = re.exec(prose))) out.push(m[1].replace(/<[^>]+>/g, ' '));
  return out.join(' ');
}

/** Header blocks with tags intact — for italic/bold-in-heading (zero-tolerance). */
function headerProse(prose) {
  const out = [];
  const re = /<h[1-6]\b[^>]*>[\s\S]*?<\/h[1-6]>/gi;
  let m;
  while ((m = re.exec(prose))) out.push(m[0]);
  return out.join(' ');
}

/** README.md as prose text: drop fenced + inline code, keep the rest as text. */
function markdownText(md) {
  return md
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ');
}

const findings = {}; // rel path -> { emdash, jargon:[], twotoneHP, triad, hallmarks:[], emojiProse, bold, italics, overuse }

function scanText(rel, text, { html = false, prose = '' } = {}) {
  const emdash = (text.match(EMDASH) || []).length;
  const jargon = [];
  for (const [re, label] of JARGON) {
    const m = text.match(re) || [];
    if (m.length) jargon.push(`${label} ×${m.length} (${[...new Set(m)].slice(0, 3).join(', ')})`);
  }
  const twotoneHP = (text.match(TWOTONE_HIGHPRECISION) || []).length;
  const triad = (text.match(TRIAD) || []).length;

  const hallmarks = [];
  let bold = 0;
  let italics = 0;
  if (html) {
    // Body italics/bold (headings removed) = baseline+ratchet.
    const bodyProse = prose.replace(/<h[1-6]\b[^>]*>[\s\S]*?<\/h[1-6]>/gi, ' ');
    italics = (bodyProse.match(ITALIC) || []).length;
    const proseForBold = bodyProse.replace(STRUCTURAL_BOLD_EXEMPT, ' ');
    bold = (proseForBold.match(BOLD) || []).length;
    // Italic/bold INSIDE headings = zero-tolerance category-3 tell.
    const hp = headerProse(prose);
    const headingItalics = (hp.match(ITALIC) || []).length;
    const headingBold = (hp.match(BOLD) || []).length;
    if (headingItalics) hallmarks.push(`italic-in-heading ×${headingItalics}`);
    if (headingBold) hallmarks.push(`bold-in-heading ×${headingBold}`);
  }
  for (const [re, label] of NOTJUSTBUT) {
    const m = text.match(re) || [];
    if (m.length) hallmarks.push(`${label} ×${m.length}`);
  }
  const dramatic = (text.match(DRAMATIC_FRAGMENT) || []).length;
  if (dramatic) hallmarks.push(`dramatic-fragment ×${dramatic}`);
  const twotoneComma = (text.match(TWOTONE_COMMA) || []).length;
  if (twotoneComma) hallmarks.push(`"it's not X, it's Y" pivot ×${twotoneComma}`);
  const validation = (text.match(VALIDATION_PHRASING) || []).length;
  if (validation) hallmarks.push(`validation-phrasing ×${validation}`);
  for (const [re, label] of FILLER_VOCAB) {
    const m = text.match(re) || [];
    if (m.length) hallmarks.push(`filler-vocab "${label}" ×${m.length}`);
  }
  let emojiProse = 0;
  if (html) {
    const emojiHeaders = nonExemptEmoji(headerText(prose)).length;
    if (emojiHeaders) hallmarks.push(`emoji-in-header ×${emojiHeaders}`);
    emojiProse = nonExemptEmoji(text).length;
  }

  const overuse = {};
  for (const [re, label] of OVERUSE_VOCAB) {
    const n = (text.match(re) || []).length;
    if (n) overuse[label] = n;
  }

  if (emdash || jargon.length || twotoneHP || triad || hallmarks.length || emojiProse || bold || italics || Object.keys(overuse).length) {
    findings[rel] = { emdash, jargon, twotoneHP, triad, hallmarks, emojiProse, bold, italics, overuse };
  }
}

for (const file of scopedHtmlFiles()) {
  const rel = relative(REPO, file).replace(/\\/g, '/');
  const raw = readFileSync(file, 'utf8');
  const prose = proseHtml(raw);
  const text = visibleText(raw);
  scanText(rel, text, { html: true, prose });
}

// README.md — markdown, scanned as text for em-dash + category-3 tells (deviation 1).
const readmePath = resolve(REPO, 'README.md');
if (existsSync(readmePath)) {
  scanText('README.md', markdownText(readFileSync(readmePath, 'utf8')), { html: false });
}

// --- Paper AI-tell catalogue: scan the 9-paper corpus (deviation 5). ---
const paperFindings = {};
for (const p of PAPERS) {
  const texPath = resolve(REPO, p.tex);
  const htmlPath = resolve(REPO, p.html);
  if (!existsSync(texPath) || !existsSync(htmlPath)) continue;
  paperFindings[p.key] = scanPaper(p, readFileSync(texPath, 'utf8'), readFileSync(htmlPath, 'utf8'));
}
// NEW-E cross-paper duplicate frames: flag a frame that matches in >1 distinct paper.
const dupFrameOffenders = {}; // label -> [paper keys]
for (const [key, f] of Object.entries(paperFindings)) {
  for (const label of Object.keys(f.dupFrameMatches)) {
    (dupFrameOffenders[label] ||= []).push(key);
  }
}

if (UPDATE) {
  const baseline = {};
  for (const [rel, f] of Object.entries(findings)) {
    const overDebt = {};
    for (const [k, v] of Object.entries(f.overuse || {})) if (v > OVERUSE_CAP) overDebt[k] = v;
    const debt = f.emdash + f.jargon.length + f.bold + f.italics + Object.keys(overDebt).length;
    if (debt) {
      baseline[rel] = { emdash: f.emdash, jargon: f.jargon.length, bold: f.bold, italics: f.italics };
      if (Object.keys(overDebt).length) baseline[rel].overuse = overDebt;
    }
  }
  writeFileSync(BASELINE_PATH, JSON.stringify(baseline, null, 2) + '\n');
  console.log(`copy-hallmarks: baseline written for ${Object.keys(baseline).length} file(s).`);

  const paperBaseline = {};
  for (const [key, f] of Object.entries(paperFindings)) {
    const entry = {};
    if (f.negdef) entry.negdef = f.negdef;
    if (f.anthro) entry.anthro = f.anthro;
    if (f.hedge) entry.hedge = f.hedge;
    if (f.numOpener > NUMERIC_OPENER_BUDGET) entry.numOpener = f.numOpener;
    if (Object.keys(entry).length) paperBaseline[key] = entry;
  }
  writeFileSync(PAPER_BASELINE_PATH, JSON.stringify(paperBaseline, null, 2) + '\n');
  console.log(`copy-hallmarks: paper baseline written for ${Object.keys(paperBaseline).length} paper(s).`);
  process.exit(0);
}

const baseline = existsSync(BASELINE_PATH) ? JSON.parse(readFileSync(BASELINE_PATH, 'utf8')) : {};
const paperBaseline = existsSync(PAPER_BASELINE_PATH) ? JSON.parse(readFileSync(PAPER_BASELINE_PATH, 'utf8')) : {};
const failures = [];
const improvements = [];
const advisories = [];

for (const [key, f] of Object.entries(paperFindings)) {
  const b = paperBaseline[key] || {};
  if (f.headingFormula) failures.push(`paper:${key}: ${f.headingFormula} heading-formula hit(s) (zero-tolerance): ${f.headingHits.join(' | ')}`);
  if (f.idiom) failures.push(`paper:${key}: ${f.idiom} "earns its keep" idiom-family hit(s) (zero-tolerance)`);
  if (f.verbless) failures.push(`paper:${key}: ${f.verbless} verbless numeric-announce fragment(s) (zero-tolerance)`);
  const negdefAllowed = b.negdef || 0;
  if (f.negdef > negdefAllowed) failures.push(`paper:${key}: ${f.negdef} negation-definition hit(s) (baseline ${negdefAllowed})`);
  else if (f.negdef < negdefAllowed) improvements.push(`paper:${key}: negdef ${negdefAllowed} -> ${f.negdef}`);
  const anthroAllowed = b.anthro || 0;
  if (f.anthro > anthroAllowed) failures.push(`paper:${key}: ${f.anthro} anthropomorphized-machinery hit(s) (baseline ${anthroAllowed})`);
  else if (f.anthro < anthroAllowed) improvements.push(`paper:${key}: anthro ${anthroAllowed} -> ${f.anthro}`);
  const hedgeAllowed = b.hedge || 0;
  if (f.hedge > hedgeAllowed) failures.push(`paper:${key}: ${f.hedge} hedge-adverb hit(s) (baseline ${hedgeAllowed})`);
  else if (f.hedge < hedgeAllowed) improvements.push(`paper:${key}: hedge ${hedgeAllowed} -> ${f.hedge}`);
  const numAllowed = Math.max(NUMERIC_OPENER_BUDGET, b.numOpener || 0);
  if (f.numOpener > numAllowed) failures.push(`paper:${key}: ${f.numOpener} numeric-announce opener(s) (budget ${numAllowed})`);
  else if (b.numOpener != null && f.numOpener < b.numOpener && f.numOpener <= NUMERIC_OPENER_BUDGET) improvements.push(`paper:${key}: numOpener debt cleared, drop from baseline`);
}
for (const [label, keys] of Object.entries(dupFrameOffenders)) {
  if (keys.length > 1) failures.push(`cross-paper duplicate frame (zero-tolerance): ${label} appears in: ${keys.join(', ')}`);
}

for (const [rel, f] of Object.entries(findings)) {
  const b = baseline[rel] || { emdash: 0, jargon: 0, bold: 0, italics: 0 };
  const bBold = b.bold || 0;
  const bItalics = b.italics || 0;
  if (f.emdash > b.emdash) failures.push(`${rel}: ${f.emdash} em-dash(es) in visible text (baseline ${b.emdash})`);
  else if (f.emdash < b.emdash) improvements.push(`${rel}: em-dash ${b.emdash} -> ${f.emdash}`);
  if (f.jargon.length > b.jargon) failures.push(`${rel}: build jargon in visible text: ${f.jargon.join('; ')} (baseline ${b.jargon})`);
  if (f.bold > bBold) failures.push(`${rel}: ${f.bold} bold/strong hit(s) in visible text (baseline ${bBold})`);
  else if (f.bold < bBold) improvements.push(`${rel}: bold ${bBold} -> ${f.bold}`);
  if (f.italics > bItalics) failures.push(`${rel}: ${f.italics} italic (em/i) hit(s) in body prose (baseline ${bItalics})`);
  else if (f.italics < bItalics) improvements.push(`${rel}: italics ${bItalics} -> ${f.italics}`);
  const bOver = b.overuse || {};
  for (const [k, v] of Object.entries(f.overuse || {})) {
    const allowed = bOver[k] != null ? bOver[k] : OVERUSE_CAP;
    if (v > allowed) failures.push(`${rel}: "${k}" ×${v} in visible text — overused (max ${allowed})`);
    else if (bOver[k] != null && v < bOver[k]) improvements.push(`${rel}: "${k}" ${bOver[k]} -> ${v}`);
  }
  if (f.hallmarks.length) failures.push(`${rel}: ANTI-AI-TELL hit(s): ${f.hallmarks.join('; ')}`);
  if (f.twotoneHP) failures.push(`${rel}: ${f.twotoneHP} HIGH-PRECISION twotone construction(s) ("It is not X. It is Y." family) — rewrite as a direct statement`);
  if (f.triad) advisories.push(`${rel}: ${f.triad} possible rule-of-three triad(s)`);
  if (f.emojiProse) advisories.push(`${rel}: ${f.emojiProse} emoji glyph(s) in body text (advisory — see script header comment)`);
}
for (const rel of Object.keys(baseline)) {
  if (!findings[rel]) improvements.push(`${rel}: clean (baseline entry can be dropped)`);
}

if (advisories.length) {
  console.log(`copy-hallmarks ADVISORY (not failing):\n  ` + advisories.join('\n  '));
}
if (improvements.length) {
  console.log(`copy-hallmarks: ${improvements.length} file(s) beat the baseline — tighten with --update:\n  ` + improvements.slice(0, 10).join('\n  '));
}
if (failures.length) {
  console.error(`\ncopy-hallmarks: ${failures.length} FAILURE(s) — AI-writing hallmarks in reader-facing copy:\n  ` + failures.join('\n  '));
  console.error(`\nFix the copy (see CLAUDE.md anti-AI-tell rules + memory feedback-anti-ai-tell-copy-ban). Em-dash/bold/italics: baseline burns down with --update. Category-3 hits (heading emphasis, "not just X but", "it's not X, it's Y" pivot, dramatic fragments, validation-phrasing, filler-vocab, emoji-in-headers): zero-tolerance, no baseline — rewrite the copy.`);
  process.exit(1);
}
console.log(`copy-hallmarks: OK (${Object.keys(baseline).length} baselined file(s) within budget, 0 category-3 hits; ${Object.keys(paperFindings).length} paper(s) checked against the AI-tell catalogue, 0 zero-tolerance hits).`);
