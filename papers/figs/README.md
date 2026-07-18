# Paper E figures — scripts, Monte Carlo, and reproduction

Numerical backing for *Engineered Intermediate-Mass Black Hole Systems* (Paper E,
`../engineered-imbh-paper.tex`). Every quoted number in the paper's §2.4, §2.7, §3.1
and §5 regenerates from these scripts. All random draws use fixed seed `20260717`;
byte-identical reruns are expected on any NumPy ≥1.26.

## Files

| File | What it is |
|---|---|
| `common.py` | Shared constants (fiducial 2×10⁴ M☉ Kerr hole, ω Cen core parameters). Change here, re-run all figs. |
| `fig1_envelope.py` | **The flyby Monte Carlo** (see below). Outputs `fig1_envelope.pdf` + `fig1_results.json`. |
| `fig2_constraint_plane.py` | (P_comp, 1−f_sink) constraint plane: JWST waste-heat wedge, transport floor, Bondi fuel ceiling. |
| `fig3_lnk.py` | Worked-example ln K computation (2×10⁶ prior draws; Appendix B model). Prints the §5 numbers. |
| `fig4_r_statistic.py` | Schematic PSD defining the MAD-regulation statistic R (illustrative, no data). |
| `fig1_results.json` | Machine-readable MC output: per-radius median/16–84% survival times, encounter rates, kick variances. |

Reproduce everything:

```sh
cd paper/figs
python fig1_envelope.py && python fig2_constraint_plane.py && python fig3_lnk.py && python fig4_r_statistic.py
```

## The flyby Monte Carlo (fig1)

**Question:** how long does a structure on a circular orbit of semi-major axis *a*
around the cluster-core IMBH survive cumulative stellar-flyby perturbation?

**Method** (Paper E Appendix A): per radius bin, 2×10⁵ encounters are sampled from the
gravitationally focused impact-parameter distribution (truncated at b = 30a), a
Maxwellian speed distribution (σ = 21 km/s), and a two-component mass function
(0.35 M☉ MS + 0.6 M☉ WD tail). Each encounter contributes an impulsive eccentricity
kick δ = 2(m★/M)·min[1,(a/b)²]·(v_orb/v). Per history (2×10⁴ per bin), survival is the
random-walk first passage to orbit-crossing eccentricity e = 0.5, capped at 12 Gyr.

**Deliberately conservative:** no adiabatic suppression is applied, although deep in
the envelope the encounter duration exceeds the orbital period by orders of magnitude
and adiabatic invariance suppresses the real coupling exponentially. Single-passage
disruption is impossible at these mass ratios (δ ≲ 10⁻² even penetrating).

**Headline result** (this run overturned the draft's own earlier estimate): flybys
never set the outer boundary. The median lifetime is ~3×10⁹ yr and roughly flat from
10⁻³ to 4×10³ AU, because ⟨δ²⟩ ∝ a⁻¹ while the encounter rate Γ ∝ a in the focused
regime, so their product is scale-free. The operative outer boundary is cluster tidal
stripping at ~0.1 r_infl ≈ 4×10³ AU.

## Browser standalone

An independent JavaScript reimplementation of the same physics runs at
[omegacentauri.me/tools/flyby-survival.html](https://omegacentauri.me/tools/flyby-survival.html)
(40k in-browser draws, hash-state deep links, no network calls); the companion fuel
budget calculator is
[imbh-fuel-budget.html](https://omegacentauri.me/tools/imbh-fuel-budget.html).
Cross-check status: agrees with this MC within ×1.5, fully explained by the σ default
(site SSOT 18.2 km/s from `measurements.js clusterParams` vs this paper's 21 km/s
fiducial). **Known follow-up:** harmonize the σ fiducial across paper and site when
Appendix A gets its parameter-variation production pass.

## Provenance

Draft v0.3, last revised 2026-07-17. License follows the repo: code MIT, prose CC BY 4.0.
