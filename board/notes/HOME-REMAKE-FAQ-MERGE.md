# HOME-REMAKE FAQ merge report

Date: 2026-10-15. Worktree: .wt/home-remake (branch feat/home-remake). Only faq.html was edited; nothing committed.

Rule applied: per question keep the longer answer (plain-text length, SVG excluded), then check for conflicts and port specific facts. faq.html structure, classes, anchors and numbering kept. data-en/data-zh stripped. Home `<br><br>` converted to `<p>`. Home answers have no diagrams, so the faq figure was kept in A.7 where the home text won. All `Back to main page` links retargeted from index.html#faq to index.html since the homepage FAQ section is being removed.

Result: 60 questions (56 paired, 1 faq-only framework reference, 3 home-only; the brief expected 2 home-only, the third is "What would happen if we built a Dyson sphere around our own Sun instead?"). faq.html: 175,234 chars before, 237,357 bytes after. Parse check: 218 open / 218 close divs, no mismatched tags, every original id present, 0 data-en/data-zh, 0 index.html#faq.

Source tally (56 pairs + 3 new): faq+port=2, home=27, merged=1, home+port=5, faq=20, home+fig=1. The D.1a framework reference is untouched.

| Anchor | Source | Home chars | Faq chars | Note |
|---|---|---|---|---|
| bh-what | faq+port | 1864 | 2029 | mass-bound note appended |
| phys-ergosphere | home | 5064 | 1354 |  |
| bh-confirmed | merged | 3169 | 2261 | faq base (fig, both bounds, decision tree) + 2 home paragraphs (anisotropy; 2025 accretion silence) |
| bh-falsify | home | 2603 | 1286 |  |
| bh-lisa-bayes | home+port | 2726 | 1730 | mass-bound note appended |
| fermi-transcension | faq | 1374 | 1811 |  |
| fermi-macro | faq | 849 | 1211 |  |
| fermi-paradox | home | 2097 | 1056 |  |
| fermi-aestivation | home | 3042 | 973 |  |
| fermi-barrow | home | 1511 | 983 |  |
| fermi-dyson-vs | faq | 782 | 1444 |  |
| miss-synth | faq | 674 | 1532 |  |
| miss-decel | faq | 681 | 1538 |  |
| phys-bz | faq | 1717 | 2373 |  |
| phys-isco | faq | 867 | 1290 |  |
| phys-hawking | faq | 1175 | 1572 |  |
| phys-tde | home | 2331 | 1724 |  |
| phys-kugelblitz | home | 4623 | 1561 |  |
| comp-star-lifting | faq | 720 | 1438 |  |
| bh-comparable | home | 1490 | 1226 |  |
| phys-timedilation | home | 2995 | 2015 |  |
| bh-mass-uncertainty | home | 2231 | 1566 |  |
| ocs-what | faq | 670 | 864 |  |
| fermi-eti-now | faq | 786 | 1169 |  |
| comp-reversible | faq | 1227 | 2044 |  |
| miss-why-oc | faq | 1012 | 1533 |  |
| miss-journey | faq | 1023 | 1434 |  |
| miss-ai-need | faq | 980 | 1120 |  |
| comp-bh-powervscompute | faq | 1019 | 1525 |  |
| fermi-comm | home+port | 2137 | 1272 | 35,400 -> 35,800 (2 x 17,900) |
| fermi-scientific | faq | 1094 | 1371 |  |
| oc-data-sources | faq | 1295 | 1328 | faq chosen on data conflict (distance SSOT 5.49 kpc) |
| oc-framework-status | faq | 1155 | 1356 |  |
| oc-no-imbh | faq+port | 1407 | 1489 | mass-bound note appended |
| phys-reconnection | home | 2336 | 1335 |  |
| comp-computronium | home | 3690 | 1611 |  |
| comp-prior-art | home | 2307 | 1308 |  |
| miss-approach | home | 1684 | 1403 |  |
| comp-merge | faq | 1253 | 1401 |  |
| comp-kessler | home | 1630 | 1541 |  |
| miss-vn | home | 2575 | 1248 |  |
| miss-faster | home | 2676 | 1331 |  |
| oc-native | home | 2723 | 1606 |  |
| bh-classes | home+fig | 2572 | 826 | faq figure retained |
| bh-sgra | home+port | 2127 | 1995 | mass-bound note appended |
| bh-dark-swarm | home+port | 3919 | 1557 | Banares-Hernandez 6,000 upper limit ported from faq |
| oc-pops | home+port | 4450 | 1385 | age error 0.15 -> 0.01 stat (Clontz 2024, as elsewhere on site) |
| oc-msps | home | 5143 | 1475 |  |
| comp-coherence | home | 2266 | 1244 |  |
| comp-radiation | home | 2609 | 1392 |  |
| phys-infoparadox | home | 2943 | 1753 |  |
| fermi-technosig | home | 2596 | 1440 |  |
| fermi-alignment | home | 2427 | 1405 |  |
| oc-fate | home | 2605 | 1219 |  |
| comp-matrioshka | home | 2302 | 1642 |  |
| ocs-misconceptions | home | 2035 | 1940 |  |
| fermi-frameworks | faq (only) | - | 6167 | untouched |

New anchors: bh-lisa-what (A.5a), fermi-dyson-sun (D.7a), fermi-technosig-look (D.9a), with sidebar TOC links. Suffix numbering used so no existing question number changed.

## Conflicts / ported facts

1. bh-confirmed (A.2). Home (longer, 3169) never states the Banares-Hernandez 2025 upper limit; it only says JWST limits are most constraining below ~6,000 Msun and quotes 39,000-47,000 Msun. Faq states Haeberle >=8,200 Msun (>=21,100 Msun with acceleration constraints, 99% CL) against Banares-Hernandez <6,000 Msun at 3 sigma, plus Fig. 2 and a decision tree. Result: merged = faq answer kept whole plus two home paragraphs (mass-anisotropy degeneracy; 2025 JWST/ATCA accretion silence, Chen arXiv:2511.20945, Mahida ApJ 996, 122).
2. oc-data-sources (F.5). Home says B&V 5.43 kpc is the value some analyses ("e.g., Haeberle et al. 2024") use; faq gives Haeberle 2025 oMEGACat VI 5.494 +/- 0.061 kpc as the site value (5.49 kpc, ~17,900 ly) with age and total-mass sections. Faq kept (also marginally longer). Dropped home-only: older RR Lyrae 15.8-17.0 kly and the LISA FY2026 funding line.
3. bh-dark-swarm (A.6). Home (longer) quotes Haeberle 8,200 Msun but has no Banares-Hernandez limit. Ported from the faq answer: Banares-Hernandez 2025 combine kinematics with MSP timing, find the data inconsistent with a point mass above ~6,000 Msun at 3 sigma, and prefer an extended dark mass. Inserted before the paragraph on why the IMBH hypothesis remains favored. Not resolved: home says the Chen/Mahida non-detections "tighten the preferred mass to >~20,000 Msun", which sits oddly beside the 6,000 Msun limit (needs a check). Home swarm BH mass ~10-100 Msun vs faq ~10-50 Msun: home kept.
4. One-sentence mass-bound note (Haeberle >=8,200 Msun vs Banares-Hernandez <6,000 Msun at 3 sigma, A&A 693, A104, pointing to A.2/A.3) appended to answers quoting a one-sided mass: bh-what (faq: ">=8,200-51,000 Msun"), bh-lisa-bayes (home: ~20,000-50,000 Msun), bh-sgra (home: "~8,200-50,000 Msun"), oc-no-imbh (faq: "Single IMBH confirmed (>=8,200 Msun)"). Wording and citation come from the site's own A.2/A.3 text.
5. oc-pops (F.2). Home age "12.08 +/- 0.15 Gyr" (Clontz 2024) vs 12.08 +/- 0.01 Gyr in faq F.5, macro-transcension-hypothesis.html, the campaign page and the bib (statistical; systematic ~0.5-1 Gyr). Changed the home sentence to 12.08 +/- 0.01 Gyr (statistical error; systematic uncertainty ~0.5-1 Gyr).
6. fermi-comm (D.10). Home round-trip "~35,400 years" is inconsistent with 17,900 years one-way (faq: 35,800). Changed to 35,800.
7. Flagged, not changed:
   - bh-sgra: home says OC is ~35% closer than Sgr A* (26,673 ly vs 17,900 ly); faq says ~40%. Arithmetic gives ~33%. Home kept.
   - oc-fate: home pericentre ~1-2 kpc, period ~120 Myr; faq pericentre ~1.2 kpc, period ~90-120 Myr. Home kept.
   - bh-what: home spaghettification text uses "OC IMBH (~8,000-50,000 solar masses)"; faq chosen, so not carried over.
   - bh-comparable (home chosen): the faq details 5.49 kpc, 47 Tuc MSP count and M31 are lost; the home generic phrase "~10,000-50,000 Msun black hole" has no bounds note.
8. Not touched: the JSON-LD FAQPage block (5 questions, dateModified 2026-05-25) still carries the old faq answer text; it now differs slightly from the on-page text for A.2, A.3, A.7, B.1 and D.1.
9. Added three badge CSS rules (.badge-physics, .badge-debate, .badge-speculative) to the faq.html stylesheet with literal colors, because home answers end with these labels.
