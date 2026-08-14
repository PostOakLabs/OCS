# Paper F v0.3 manuscript integration — edit log (WU OCS-F-V03-2)

Target: `paper/accretion-limit-paper.tex`. Contract: `figs/fF_v3_DELTA.md` (7 flags + headline table),
`figs/fF_measured_inputs.json`, `figs/fF_v3_results.json`, `figs/fF_v3_pgf.txt`, `figs/fF_epochs.json`,
`figs/fF_maveric_context.json`, board row OCS-F-V03-1.

Line numbers are post-edit, in the file as it stands after this WU.
Nothing outside the brief's 10 items was restructured; no other paper's files were touched.

---

## Item 1 — v0.3 headline numbers, Fig. 1 coordinates, script pointers — DONE

**Preamble pointers (lines 7–17).** `fF_posterior_v3.py` is now named as the computation of record with its
three outputs; `fF_posterior_v2.py` + `fF_v2_results.json` are retained in the chain as superseded;
`fF_measured_inputs.json` added as the provenance pointer; a v0.3 block records what changed and why.
Priors-table caption script pointer `fF_posterior_v2.py` → `fF_posterior_v3.py` (line 136).

**Abstract (line 54).** Radio-free anchor at 8,200 M☉: `8.9e-9` → `8.8e-9`. The RIAF anchors (2.8e-10,
1.0e-11) and the 90/44/31/2 per cent exclusion statements survive rounding to the abstract's own precision
and are unchanged; each was checked against `anchors_riaf`, `anchors_riaf_noradio` and `exclfrac_anchors`
rather than assumed.

**Anchor table `tab:anchors` (lines 247–249; Table 3 in v0.2, now Table 4 since the new `tab:irfilters` precedes it).** jet column `1.4e-9 / 6.5e-10 / 2.1e-11` → `9.9e-10 / 4.9e-10 /
1.8e-11` (the −25 per cent family). RIAF-no-radio at 8,200: `8.9e-9` → `8.8e-9`. RIAF, thin-disk, and both
P_excl columns verified unchanged at quoted precision (RIAF 0.1913/0.3149/0.8989; no-radio
0.0037/0.0174/0.4388).

**Results prose (line 258).** Red-curve quotation `8.9e-9` → `8.8e-9`.

**Sensitivity table `tab:sens` (lines 277–280).** widened prior `3.3e-9 / 1.7e-9` → `3.2e-9 / 1.6e-9`;
widened + wind floor `6.5e-10` → `6.4e-10`; ε-grid floor at 1e-11 `4.8e-9 / 2.9e-9 / 3.8e-10` → `4.6e-9 /
2.8e-9 / 3.6e-10`. The `n_e ÷ 10` row is unchanged at quoted precision. The surrounding claims (factor ~6
for each prior test, factor ~10 for the grid floor) were re-derived from the v0.3 anchors and still hold
(5.7× and 6.2×; 8.2× at the low anchor).

**Conclusion (line 339).** `8.9e-9` → `8.8e-9`.

**Deeper mid-infrared forecast (line 327).** The v0.2 sentence claimed a threefold MIRI depth gain moves
ε95 by "only ~7 per cent". Under the per-filter likelihood, `anchors_fc_miri_jet / anchors_jet` gives
0.691 / 0.711 / 0.787, so the gain is 31 / 29 / 21 per cent at the three anchors. Sentence rewritten to
carry 29 per cent at the fast-star anchor with the other two in parentheses, to state that this remains an
order of magnitude short of the radio leg, and to name the ~7 per cent as the earlier draft's figure under
the retired proxy. The instrument-priority conclusion for Paper C (radio first, density second) is unchanged
and still supported: SKA-era radio buys 10×, deeper MIRI 1.4×.

**Figure 1 (lines 214–226).** All seven coordinate lists replaced verbatim from `fF_v3_pgf.txt`
(`eps95_riaf`, `eps95_jet`, `eps95_disk`, `eps95_riaf_noradio`, `NAT95`, `NAT05`, `NAT50`). The v3 export is
on the 41-point grid rather than v0.2's 21 points, so the curves are now plotted at the full computed
resolution; `NAT50` in particular was previously drawn on an 11-point subsample. `fill between[of=n95 and
n05]` still resolves, both paths carrying identical 41-point domains. Caption numbers (90 per cent RIAF, 44
per cent no-radio) verified against `exclfrac_anchors` and unchanged.

## Item 2 — X-ray confidence relabelled — DONE

**§2 X-ray (line 98).** "absorption-corrected at 3σ; ... 0 ± f_X,lim/3" replaced: the limit is stated at
95 per cent confidence by Haggard+2013, who never write a σ; the `aprates` bound is on a non-negative count
rate, so it is read one-sided and σ_FX = f_X,lim/1.645. The earlier draft's labelling is named as wrong
rather than quietly dropped, and the ladder is cross-referenced to the appendix.

**§3.3 likelihood (line 166).** "product of three Gaussians ... 0 ± f_X,lim/3 ... 0 ± (νL_ν)lim/3" →
"product of six Gaussians", X-ray at /1.645, four per-filter IR terms at their own σ_j, and the
reconstruction sentence now reads "divided by the quantile of the confidence the source itself states"
instead of "one third of the 3σ limit".

**Appendix `app:conventions` (line 361), new `Confidence conventions` paragraph + `tab:ladders`.** Both
ladders shipped from `fF_v3_results.json`: X-ray one-sided 95 % (primary) / two-sided 95 % / lim-over-3, and
the IR 99.7 / 95 (primary) / 68 per cent completeness rows plus tightest-single-filter. Spans stated (5 per
cent X-ray, 8 per cent IR), jet-family tightest-filter comparison stated, 5.43-vs-5.49 kpc IR reference
distance stated at 0.5 per cent.

**Appendix `app:mincheck` (line 391) — beyond the literal edit list, flagged here.** The cross-check
paragraph described `fF_joint_bound.py` as inverting "the 3σ per-band thresholds", which after the item-2
relabel read as though the sources' limits are 3σ. That script is unchanged and did use lim/3, so the
sentence was re-scoped ("as that draft labelled them") and one clause added noting its X-ray threshold
predates the relabel. No number moved. Same class of change as item 2; called out because it is not
literally on the list.

## Item 3 — infrared per-filter treatment — DONE

**§2 Infrared (lines 78–96).** The `3e31` proxy sentence is gone. Replacement states the per-filter Table 1
treatment, σ_j = L_lim,j/1.645 at the 95 per cent completeness row (matched to the X-ray leg's CL), that
completeness is a recovery fraction and the quantile mapping is a convention with the other two rows run,
that F770W dominates, that the independent-terms combination is optimistic and the tightest-single-filter
conservative reading sits within 5 per cent, and that limits are referenced at Chen's 5.49 kpc and rescaled.
New `tab:irfilters` carries the four filters with Vega mag limit, L_lim and σ_j. Adding it renumbers every later table by one (priors 1→2, families 2→3, anchors 3→4, sensitivity 4→5), which is invisible in the text because every cross-reference goes through `ef`.

**Mass validity (same paragraph).** "for masses up to ~2×10⁴ M☉" → Chen's own stated ≲10⁴ M☉, with the
caveat strengthened: the 4×10⁴ M☉ anchor is now described as a factor-of-four extrapolation, not a factor of
two. Per DELTA flag 4.

## Item 4 — appendix distance paragraph — DONE

**Appendix (line 359), new `X-ray reference distance` paragraph.** The old sentence ("the exact distance
should be confirmed ... a 4.8 vs 5.43 kpc mismatch shifts the X-ray leg by 28 per cent") is deleted, not
patched. Replacement: Haggard adopt 5.2 kpc; both halves of the old warning were wrong; the shift is zero
because the X-ray leg is evaluated on flux; the reference distance now serves as the consistency check
4πD²f_lim = 1.62e30 at 5.2 kpc against their stated 1.6e30, failing at 4.8 kpc (1.38e30), asserted at run
time by the script. Contrast with the IR limits, which are published as luminosities and do carry their
source distance, stated in the same paragraph. Per DELTA flag 2.

## Item 5 — duty-cycle epoch structure — DONE

**§6 (lines 314–318).** The "radio campaign spans months ... N ~ 6" description is replaced by the real
structure from `fF_epochs.json`: 25 blocks, three projects, 2010-01-22 to 2024-12-27, 177.19 hr, with the
per-project subtotals (CX556 20/147.09, C2877 3/11.79, C2158 2/18.31). The DELTA flag-1 direction is stated
as the export has it: the table rows **exceed** the paper's own ~170 hr / 172 hr prose totals. The 148-hr
framing is not used anywhere in the manuscript.

The epoch count feeds the argument, so the argument moved with it. The paragraph now separates the two
regimes explicitly: the time-average bound ε_on ≲ ε95/δ is the operative statement for the radio, because
the image is a weighted combination over the full fourteen-year span; the sampling-luck argument uses
N ≃ 30 independent epochs (25 radio blocks + 4 Chandra exposures + 1 JWST visit), which puts 50 per cent miss
probability at δ ≈ 0.02 rather than δ ≈ 0.1. The excluded band therefore extends down to a few per cent duty
cycle. The old N ~ 6 / δ ≈ 0.1 figures are named as the earlier draft's, which had treated the radio
campaign as a single epoch. Paper E's 10⁻⁴-duty TDE channel remains far below reach, so the section's
closing claim is unaffected.

## Item 6 — MAVERIC population context — DONE

**New §5.2 `sec:maveric` (lines 287–309), end of Results.** Text plus `tab:maveric`, four rows: MAVERIC ATCA
ω Cen (<8.8 µJy 3σ, M<1000 M☉, 4.9 kpc), VLA stack over 29 clusters (0.65 µJy/beam, <800 M☉), ATCA stack
over 14 clusters (1.42 µJy/beam, <970 M☉), and this paper's radio input (1.1 µJy/beam rms, 5.49 kpc). No
figure and no reconstructed survey points, per DELTA flag 7.

Every ambiguity in the staged anchors is stated rather than resolved: 8.8 µJy (Table 2) vs 8.9 µJy (§V.2.1);
the VLA stack given as both <800 and <730 M☉ in one sentence, with the weaker quoted; ω Cen's membership in
the ATCA stack not stated by the source; and Tremou's citation of Haggard's X-ray limit as 1.7e30 against
Haggard's own 1.6e30. Each survey's adopted distance is named (Tremou 4.9, Haggard 5.2, Chen/Mahida 5.49,
this paper 5.43 kpc), and the paragraph states that the survey mass limits are the sources' own
fundamental-plane inversions, the step §3.3 declines to take, so they are not ε and not convertible to it.
No MAVERIC number enters any computation.

## Item 7 — Mahida's own density as an independent anchor — DONE

**§3.2 priors (line 153).** One sentence added ahead of the structural-fact statement: Mahida+2026 adopt
n_e = 0.2 ± 0.1 cm⁻³ for the same cluster on the same kind of reasoning (pulsar-derived densities in other
globular clusters), an independent arrival at the median used here.

## Item 8 — distance-prior disclosure — DONE

**§3.2 priors (line 155).** New paragraph. The prior is **not** changed: it stays 5.43 ± 0.05 kpc. Disclosed:
Mahida's adopted 5.494 ± 0.061 kpc, the offset at 1.2σ of the prior, the ~2 per cent effect, and its
direction (all legs **loosen**, since a more distant source is fainter at fixed luminosity). The
never-silently-harmonize rule is stated as the reason. Per DELTA flag 5. The Mahida distance is quoted
without attributing it to a specific reference, since the kinematic-distance source is not in this paper's
bibliography.

## Item 9 — data availability — DONE

**§Data availability (line 341).** `fF_posterior_v2.py` / `fF_v2_results.json` → v3 as the shipped
computation, with v0.2 named as retained for comparison. Added: `fF_measured_inputs.json` described as the
provenance file carrying every observational number with source location and verbatim quotation, plus
`fF_epochs.json` and `fF_maveric_context.json`. A natural sentence existed for DELTA flag 6, so it is
included: Mahida's conservative efficiency limit appears as 4e-3 (abstract, §IV.1) and 4e-6 (§V), and their
Table 1 hours exceed their prose totals; neither enters any number here, and both are flagged for that
paper's authors. The sentence claims only that they are flagged, not that they have been reported — no
outreach has happened in this WU.

## Item 10 — version line — DONE (left alone)

`\date` still reads **Draft v0.2 (last revised 2026-08-13)**. The bump to v0.3 and the date are reserved to
the editorial session's sign-off, per the brief. Note for that session: the standing version-string
propagation rule means the bump must also hit `repo/<paper>.html` (nav chip + `class="venue"`) and the
Paper F card in `repo/paper.html`.

---

## Build

`pdflatex` → `bibtex` → `pdflatex` ×2, exit 0 each pass. 15 pages. Zero undefined citations, zero undefined
references, zero BibTeX warnings.

Box warnings, against a from-scratch build of the pre-edit `HEAD` version for comparison:

| | baseline (v0.2) | after this WU |
|---|---|---|
| Overfull hbox | 3 | 1 |
| Underfull hbox | 0 | 1 |

- The surviving overfull (88.4 pt, `tab:priors`) is pre-existing and untouched by this WU; the priors table's
  Basis column runs past the text block. Left for the editorial session, since fixing it means re-laying a
  table outside the edit list.
- The two overfulls this WU would otherwise have added (data availability, from the long `\texttt`
  filenames) and one pre-existing 9.4 pt overfull are resolved by wrapping that paragraph and the rewritten
  §2 X-ray paragraph in `sloppypar`. The cost is the one underfull line in data availability.

## Prose gates

- Banned-word grep (`precisely|exactly the|honest|honestly|at bottom|is itself the point`): zero hits in the
  whole file.
- Em-dash: one `---` in the file, in the pre-existing `\date` line. None introduced.
- No `\emph{}` added. No "not X but Y" constructions, section-closing aphorisms, or rhetorical fragments in
  the new text.

## Items flagged, not improvised

1. **Forecast row `fc_ne` reads 22 per cent, the text says "~25 per cent".** §7's density forecast claims a
   ±10 per cent density measurement tightens the baseline by ~25 per cent. `anchors_fc_ne / anchors_riaf`
   gives 0.785 / 0.777 / 0.755, so 22 per cent. This is **not** a v0.2→v0.3 move: v0.2's own ratio was also
   0.775, so the number was already loose before this WU and item 1 gives no v0.3 value to swap in. Left as
   written; the editorial session should decide whether to tighten "~25" to "~22" or widen the hedge.
2. **`tab:priors` overfull hbox**, as above.
3. **The abstract still says "170-hour ATCA radio campaign"**, which is Mahida's own prose figure, while §6
   now reports the table's 177.19 hr and flags the mismatch as the source's. This is deliberate: the abstract
   quotes the campaign as its authors describe it. If the editorial session prefers one number in both
   places, that is a judgement call about how loudly to carry another paper's internal discrepancy.
