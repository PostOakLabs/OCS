# Paper D outline — The Economics of Inward Migration

**Working title:** *The Economics of Inward Migration: Relocation versus Densification for Computation-Maximizing Civilizations*

**Author:** Tim Swanson — The Omega Centauri Society / Post Oak Labs
**Target:** omegacentauri.me → arXiv (no specific journal named — per Tim, 2026-07-11)
**Length target:** parity with Papers A–C (~500–600 lines of .tex, 8–10 figures/tables)
**File plan:** `economics-paper.tex`, bibliography = `references.bib` + `inward-extra.bib` + new `economics-extra.bib`

## Mandate

Paper B (inward-review), open problem P3, states the gap this paper fills:

> "Bostrom's opportunity-cost argument prices delay; Bennett et al. price dormancy; nobody has priced *relocation*. ... This is a well-posed optimization problem awaiting treatment."

Paper D solves P3 quantitatively, and in doing so makes B's open problems P1 (optimization premise / mixed populations) and P4 (incomplete compliance — "how much thinning suffices") tractable. It converts Paper A's qualitative concession ("the MTH thins the loud population") into numbers.

## Core decision model

A lineage at a planetary system, with utility = discounted integrated computation, chooses among:

- **Strategy S (stay/densify):** local Matrioshka-style densification. Power ceiling ~ stellar output; erasure floor = CMB (2.7 K); radiator-limited per Bradbury 1999. Payoff immediate, capped.
- **Strategy M (migrate):** beamed-sail relocation to nearest suitable IMBH cluster. Transit 10⁴–10⁶ yr (distance d, speed 0.1–0.2c); payoff deferred but multiplied by Paper A §4 factors: ×80–600 energy per unit fuel, ×10⁹ instantaneous power, ×10¹² erasure-cost reduction.
- **Strategy H (hybrid seed-and-stay):** send self-replicating seed (Freitas 1982 bootstrap) at negligible mass cost while continuing S locally; merge or fork later. Dominance conditions for H are the paper's most interesting result candidate — if H dominates broadly, migration compliance is nearly free and the Fermi implication sharpens.

Decision variables and parameters:
- discount rate ρ (including ρ→0 patient limit and hyperbolic variants)
- transit risk of loss per ly, payload replication factor
- distance distribution to P2-class targets (from Galactic GC census — reuse Paper A selection criteria; note Huang, Tao & Zhang 2026 crystallization metric as an independent ranking input)
- goal-stability hazard rate λ (links to open problem P2; sensitivity analysis rather than resolution)

Deliverable: closed-form crossover surfaces in (ρ, d, risk) space; regions where S, M, H each dominate. All input magnitudes already exist in Paper A §4 and site calculators.

## Section plan

1. **Introduction** — the pricing gap (Bostrom priced delay; Bennett–Hanson–Riedel priced dormancy; relocation unpriced). Claims/non-claims register, same epistemic-status-box convention as A–C.
2. **The decision problem stated** — agents, utility, strategy set {S, M, H}, parameters. Epistemic status: decision theory over established physics; no claim ETI exists.
3. **Payoff kernels** — computation-rate integrals for each strategy from the Paper A stack (Kerr efficiency, BZ, Landauer/horizon sink, Eddington throughput; Matrioshka radiator limits for S). Figure: computation-per-joule and computation-per-second vs time for S, M, H at fiducial d = 5 kpc.
4. **Crossover analysis** — the main result. Analytic crossover surfaces; heatmap figures in (ρ, d) at several risk levels. Expected headline: M or H dominates for ρ below a critical ρ* ≈ (payoff-multiplier)/(transit time) scale — i.e., any lineage patient enough to plan over ≥10⁵ yr migrates or seeds; only steep discounters stay.
5. **Population consequences** — embed the per-lineage rule into a grabby-aliens-style mixed population (Hanson et al. 2021; Olson 2015): fractions of maximizers/expansionists/satisficers as prior, derive fraction migrating and hence the predicted thinning of the loud population. Answers B's P4: how much compliance suffices to reconcile silence with the selection effect. Table: silence-compatibility vs (compliance fraction, Drake rarity factor).
6. **New residues** — observational corollaries (feeds B's P5): the S/M ratio predicts relative sky abundance of Matrioshka-type mid-IR sources vs quiet-cluster residues; a testable population statement (WISE/JWST nulls already bound the S branch — cite Wright 2014, Griffith 2015, Curtis et al. 2026 Dyson Minds archival-anomaly agenda). Hybrid strategy predicts *both* residue types in fixed proportion — a discriminator no prior paper states.
7. **Limits and objections** — goal stability (P2) as hazard-rate sensitivity, not solved; anthropic/self-indication caveats; decision-theory model dependence (expected-utility vs satisficing); honest statement that parameter priors are unmeasurable and the value is in the structure of the crossover, not point estimates.
8. **Conclusion** — the gradient argument of A–B is necessary but not sufficient; this paper supplies the sufficiency condition (patience above threshold) and the population-level dial (compliance fraction) that observations can now constrain.

## Figures/tables planned

1. Strategy schematic (S/M/H timeline diagram, TikZ, style-matched to A's phase figure)
2. Payoff kernels vs time (loglog)
3. Crossover heatmap in (ρ, d), 3 risk panels
4. ρ* vs target distance for Galactic GC census (named targets: ω Cen, 47 Tuc, M54...)
5. Mixed-population thinning table (compliance × rarity → expected loud count)
6. Residue-ratio prediction (Matrioshka-IR vs quiet-cluster counts)
7. Sensitivity to goal-stability hazard λ
8. Comparative table: Bostrom delay cost / Bennett dormancy cost / this paper's relocation cost — one framework

## New citations needed (economics-extra.bib)

- Decision theory under deep time: Bostrom 2003 (have), Sandberg intergalactic spreading, Armstrong & Sandberg 2013 (have as Armstrong2013)
- Hanson grabby aliens (have), Olson 2015 (have)
- Discounting literature: Ramsey 1928, hyperbolic discounting (Laibson 1997) — for the ρ variants
- Self-replicating probe economics: Freitas 1982 (have), Matloff on sail mass ratios
- Curtis et al. 2026 Dyson Minds (now in references.bib), Huang et al. 2026 crystallization (now in references.bib)

## Consistency requirements with A–C

- Same fiducial: M = 2×10⁴ M☉, d(ω Cen) = 5.49 kpc, transit speed 0.1–0.2c
- Same epistemic-status boxes, same claims/non-claims section, same AI-assistance disclosure block
- Same falsificationist framing: §6 residues must state what observation kills which strategy-dominance claim
- Cross-references: cite A as Swanson2026MTH, B as Swanson2026Review (add key), C as Swanson2026Campaign
- Site tie-in: crossover calculator as a new tool page (candidate: `tools/migration-economics.html`), supplementary material pattern identical to A–C

## Anti-AI-tell style rules for drafting (apply from first draft)

- ≤1 em-dash per paragraph; no `--- X ---` insets
- No "not X but Y" unless the negation carries argumentative weight
- No section-closing aphorisms except conclusion's final sentence
- `\emph{}` only for first-use technical terms
- Ban list: "precisely", "exactly the", "is itself the point", "honest/honestly" (use "conservative"/"quantitative"), "at bottom"
