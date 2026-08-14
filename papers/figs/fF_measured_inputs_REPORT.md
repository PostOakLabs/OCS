# Paper F measured-input extraction — report

**WU:** OCS-F-DATA-1. Data-only extraction from the full texts of the four cited sources into `fF_measured_inputs.json`. No `.tex`/`.py` edits made — the editorial (Fable) session integrates.

## Discrepancies vs. `fF_posterior_v2.py`'s hardcoded values

1. **Haggard+2013 distance is wrong in the script.** `D_REF_X = 4.8 * kpc` (script line 46, comment "distance at which Haggard+13 luminosity was quoted"). The paper actually states **5.2 kpc** (Harris 1996 catalog), not 4.8. Neither 4.8 nor 5.43 appears anywhere in Haggard et al. 2013. The tex's own appendix (§Conventions) already flags "a 4.8 vs 5.43 kpc mismatch shifts the X-ray leg by 28 per cent" — the correct fix is 5.2 kpc, not 5.43, and the shift from 4.8→5.2 is a factor (5.2/4.8)² = 1.17× in flux normalization, not the 28% (5.43/4.8) the tex anticipated.

2. **Haggard+2013's flux limit confidence is mislabeled.** Script comment and tex §2 both call `FX_LIM_3SIG = 5.0e-16 erg/cm²/s` a "3σ" limit. The paper states this is a **95% confidence** limit (Table 1 footnote c, and the count-rate limit is also stated at 95%), not 3σ explicitly. 95% and 3σ are numerically close for some one-sided conventions but are not the same stated quantity — the paper never uses the word "sigma" for this number.

3. **`LIR_LIM = 3.0e31` erg/s is not traceable to Chen+2025.** The script labels it "band-peak nuLnu proxy (Chen+25)". Chen et al.'s actual Table 1 per-filter luminosity limits (extracted in full in the JSON) range from ~2.7×10²⁶ to ~1.5×10³² erg/s depending on filter and completeness fraction (99.7% F444W = 1.5×10³²; 99.7% F200W = 7.5×10³¹); no explicit 3×10³¹ figure appears anywhere in the paper. This constant needs a stated derivation (e.g., "F770W at X% completeness") or should be replaced with the actual per-filter table.

4. **Paper F's tex claims Chen+2025 IR limits are quoted "for masses up to ~2×10⁴ M☉".** Chen+2025's own stated accretion-constraint mass threshold is **10,000 M☉** (§VI Conclusions: "M_BH ≲ 10,000 M☉ ... is allowed by both JWST limits and the 5.5 GHz radio limit"), not 2×10⁴. Flag for the editorial session — likely a rounding/misquote in §2.

5. **Mahida+2026 distance (5.494±0.061 kpc) vs. Chen+2025 distance (5.49 kpc) vs. Paper F's D_REF_IR (5.43 kpc).** All three are close but not identical. Mahida cites Häberle et al. 2025 (oMEGACat VI kinematic distance) explicitly; Chen's source citation wasn't fully resolved (numeric marker [16] only). Per the paper set's standing σ-fiducial-decision precedent (never silently harmonize small cross-paper offsets), this is noted rather than "fixed."

## Internal inconsistencies within the source papers themselves (not Paper F's fault, but the machinery should not silently pick one)

6. **Mahida+2026 contradicts itself on its own headline number.** Abstract and §IV.1 both state the conservative adiabatic 3σ efficiency limit as **ε ≲ 4×10⁻³**. §V (Summary/Conclusion) instead states **ε ≤ 4×10⁻⁶** — a three-orders-of-magnitude discrepancy, apparently a typo (10⁻³ vs 10⁻⁶) since 2 of 3 mentions agree on 4×10⁻³. Paper F's tex does not currently quote Mahida's ε limit directly (it derives its own), so this doesn't currently propagate, but if a future draft cites Mahida's headline number directly, use 4×10⁻³ and flag the §V value as likely erratum.

7. **Mahida+2026's Table 1 observing hours don't sum to its own prose total.** Table 1's 25 individual blocks sum to ~148.1 hr; the Abstract says "~170 hours" and §II.3 says "172 hours." The paper doesn't reconcile this. Relevant to Paper F §6 (duty-cycle section) if block-level epoch counting is used — the discrepancy means Table 1 is likely not fully exhaustive of the data folded into the final image.

8. **Tremou+2018's own ω Cen flux limit differs between its Table 2 (<8.8 μJy) and its prose (<8.9 μJy, §V.2.1).** Both are verbatim from the source. Also its VLA-stack mass limit is given as two different numbers in one sentence, "<800 M☉ (<730 M☉)" (§IV.2), undisambiguated.

9. **Tremou+2018 cites Haggard+2013's X-ray limit as "<1.7×10³⁰ erg/s"**, while Haggard's own paper states 1.6×10³⁰ erg/s (both labeled 95% confidence). Minor transcription rounding in Tremou, noted for completeness — not a Paper F error.

## Notable non-null items worth the editorial session's attention

- **Mahida+2026's adopted gas density is n = 0.2 ± 0.1 cm⁻³**, imported from other clusters via pulsar-derived free-electron densities (Strader et al. 2012 precedent), *not* a direct ω Cen measurement — same epistemic status as Paper F's own 47 Tuc-analogy prior (median 0.23 cm⁻³, 0.5 dex), just a different source cluster set and narrower width. Worth a one-line cross-reference in §Priors if the editorial session wants it.
- **Haggard+2013's extraction aperture is 6″ radius** at the AvdM10 center (a separate ~1″/2-pixel localization radius is used earlier for source detection, not the flux limit).
- **Tremou+2018's Bondi/FP formalism uses n = 0.2 cm⁻³, T = 10⁴ K, γ=1**, essentially the same regime as Paper F's own priors — useful as an independent literature anchor for Paper F's gas-density discussion in §Data availability's request-to-source-teams framing.
- Per-epoch Chandra source counts/background (requested in Paper F's Data-availability paragraph) are **not tabulated separately** in Haggard+2013 — only the combined 290.9 ks total across 4 exposures (2 epochs: 2000-01-24/25 and 2012-04-16/17, ObsIDs 653, 1519, 13726, 13727). Getting per-epoch numbers would require the archival Chandra data directly, not the paper.
- ω Cen's inclusion in Tremou+2018's 14-cluster ATCA stack is not explicitly stated (only inferable from the absence of ω Cen in the stated exclusion list).

## Sources not fully resolvable from the extracted text

- Chen+2025's citation [16] for its adopted 5.49 kpc distance was not resolved to a full author/year (only the in-text numeric marker was captured); same for its ATCA follow-up ref [26] behind the 3.3 μJy radio figure used in Fig. 7.
