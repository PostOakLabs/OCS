# Inner pages AI-tell sweep

Scope: omega-centauri, hypothesis, fermi, roadmap, references (glossary/footnote prose only), faq, paper, proposals, live-review, contact, mcp. Rules: CLAUDE.md "Anti-AI-tell prose rules" plus the 2026-08-20 extension.

## Counts (visible em-dashes, copy-hallmarks baseline; bold/italics unchanged except faq italics)

| Page | em-dash before | after | twotone/aphorism rewrites | other |
|---|---|---|---|---|
| omega-centauri | 8 | 3 | 1 | |
| hypothesis | 34 | 13 | 2 | |
| fermi | 10 | 2 | 1 | 1 interrogative heading |
| roadmap | 26 | 23 | 2 | |
| references | 126 | 118 | 0 | glossary li only; bibliography entries untouched |
| faq | 242 | 134 | 13 | 3 banned words ("honestly", "Crucially", "exactly the"); italics 101 -> 99 |
| paper | 1 | 1 | 1 | |
| proposals | 9 | 8 | 1 | |
| live-review | 10 | 10 | 1 | |
| contact | 3 | 3 | 0 | clean |
| mcp | 21 | 19 | 0 | |

Em-dash method: every `<p>/<li>/<td>/<dd>` with 2 or more dashes was rewritten so at most one remains. Short insets became parentheses or commas, other extra dashes became semicolons, colons or commas. All diffs were reviewed word by word; four auto-conversions were corrected by hand (FAQ M1/M2 labels, Vaire sentence, a double parenthesis, a doubled colon in fermi). Proposal card titles ("Pulsar timing — Deep ...") are link titles and were left alone. Two paper.html abstract dashes written as `&mdash;` were not touched. FAQ JSON-LD `text` copies were updated only where the rewritten sentence is duplicated verbatim.

## Twotone / aphorism / banned-word rewrites

| Page | Before | After |
|---|---|---|
| omega-centauri | may end up — not by design, but by physics. | may end up, driven by physics. |
| fermi | the reason we observe no alien civilizations is not that they don't exist, but that the most advanced ones followed the physics ... | we observe no alien civilizations because the most advanced ones followed the physics ... |
| fermi (heading) | Is Something Already There? | Looking for Something Already There |
| hypothesis | These two metrics are not contradictory but measure different things; | These two metrics measure different things; |
| hypothesis | This is not a coincidence; it is what thermodynamics predicts | This convergence is what thermodynamics predicts |
| roadmap | predicted, not merely compatible. | predicted by the framework. |
| roadmap | Phases 3-5, not because efficiency is low, but because the absolute power budget is insufficient. | Phases 3-5 because the absolute power budget is insufficient. |
| live-review | The non-detection does not rule out an IMBH; it merely confirms that any IMBH | The non-detection is consistent with an IMBH and confirms only that any IMBH |
| proposals | rule out the OCS hypothesis, not just support it. | rule out the OCS hypothesis. |
| paper | is validated, not only proposed: | is also validated: |
| faq | taps ... rotational mass-energy, not merely the infalling gas. | ... in addition to the infalling gas. |
| faq | as an operational reality, not just a background hazard. | as an operational reality. |
| faq | information is not lost but encoded in subtle correlations | information survives, encoded in subtle correlations |
| faq | the swarm is not a fixed structure but an adaptive system, it concentrates | the swarm is an adaptive system: it concentrates |
| faq | It is not merely a curiosity; it is a genuine scientific puzzle | It is a genuine scientific puzzle |
| faq | is then not a paradox but a predicted consequence | is then a predicted consequence |
| faq | may be invisible not because they are absent but because they have retreated inward | may be present yet invisible, having retreated inward |
| faq (x2, incl. JSON-LD) | a serious engineering proposal, not just science fiction; it is | a serious engineering proposal; it is |
| faq | Byzantine fault tolerance in the goal space, not just the computation space. | This gives Byzantine fault tolerance in the goal space as well as the computation space. |
| faq | The 17% c figure is therefore not a conservative choice but close to the engineering optimum | The 17% c figure is therefore close to the engineering optimum |
| faq (x2) | Omega Centauri is not static; it travels | Omega Centauri travels |
| faq | while honestly acknowledging | while acknowledging |
| faq (x2) | Crucially, it requires no propellant. | It requires no propellant. |
| faq | gas-poor for billions of years; exactly the kind of cleared, settled environment | ... years, which is the kind of cleared, settled environment |

## Kept on purpose

- faq / hypothesis "Hypothetical near-term industry claim (treat with caution ...)" and other speculative-vs-established labels: unchanged.
- faq "Harrison is not arguing for inward ... but rather that ...": the contrast distinguishes two named authors' positions.
- roadmap falsification table ("Does not falsify the IMBH, but does falsify the specific utilisation model"; "would not falsify the framework wholesale but would establish ..."): the negation states what an outcome does and does not rule out.
- faq "The civilization's horizon is therefore not threatened ...": plain negation, not an antithesis.
- faq "The two mechanisms should not be conflated" / "does not violate thermodynamics": misconception corrections.
- references: Wright 2020 and Hayden & Preskill 2007 annotations ("not unstable ... but drifts", "not destroyed but scrambled"): bibliography entries, out of scope.
- hypothesis h2 "Why Black Holes Beat Everything Else": the single "Why" heading on that page. FAQ question headings left as interrogatives.
- Paper titles on paper.html, the mission quote, all IMBH bounds (Häberle >=8,200 and Bañares-Hernández <=6,000 M☉) and every number/citation untouched.
- Decorative bold/italics: not swept beyond FAQ (99 vs 101); these are baseline+ratchet categories with legitimate run-in labels, and no count rose.

## Gates

- `sh scripts/pre-push`: all gates passed (copy-hallmarks OK, 0 category-3 hits).
- `check-copy-hallmarks.mjs --update` run to ratchet down; compared with origin/main baseline, no file rose. The index.html entry (1 -> 0 on main already) was left at the origin value to avoid conflicting with the other PR.
- `node --test` per file: lib-imbh-constraints 68/0, tier-c-hash-roundtrip 36/0, tier-c-known-value 136/0 (pass/fail).
