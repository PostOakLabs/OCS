# Paper E figures — scripts, Monte Carlo, and reproduction

Numerical backing for *Engineered Intermediate-Mass Black Hole Systems* (Paper E,
`../engineered-imbh-paper.tex`). Every quoted number in the paper's §2.4, §2.7, §3.1
and §5 regenerates from these scripts. All random draws use fixed seeds derived from
`20260717`; byte-identical reruns are expected on any NumPy ≥1.26.

## Files

| File | What it is |
|---|---|
| `common.py` | Shared constants (fiducial 2×10⁴ M☉ Kerr hole, ω Cen core parameters), the perturber mass function, the radius-dependent MIR limit, and the Gnedin & Ostriker (1999) adiabatic kernel. Change here, re-run all figs. |
| `fig1_envelope.py` | **The flyby Monte Carlo** (see below). Outputs `fig1_envelope.pdf` + `fig1_results.json`. |
| `fig2_constraint_plane.py` | (P_comp, 1−f_sink) constraint plane: JWST waste-heat wedge, transport floor, Bondi fuel ceiling. The floor renders as a labelled adopted-parameter line over hatching, not as a hard boundary of the allowed region (§6.1). |
| `fig3_lnk.py` | Worked-example ln K computation (2×10⁶ prior draws; Appendix B model). Prints the §5 numbers, the data-only statistic ξ, and the channel capacity. Every prior boundary is a command-line switch (see below). |
| `fig4_r_statistic.py` | Schematic PSD defining the MAD-regulation statistic R (illustrative, no data). |
| `fig1_results.json` | Machine-readable MC output: per-radius median/16–84% survival times, encounter rates, kick variances, and the adiabatic parameter, for **every** configuration under `per_config`. |

Reproduce everything:

```sh
cd paper/figs
python fig1_envelope.py && python fig2_constraint_plane.py && python fig3_lnk.py && python fig4_r_statistic.py
```

## The flyby Monte Carlo (fig1)

**Question:** how long does a structure on a circular orbit of semi-major axis *a*
around the cluster-core IMBH survive cumulative stellar-flyby perturbation?

**Method** (Paper E Appendix A): per radius bin, 2×10⁵ encounters are sampled from the
gravitationally focused impact-parameter distribution (truncated at b = 30a), a speed
distribution drawn as a Rayleigh of scale σ = 21 km/s shifted upward by 0.3σ (mean
1.55σ), and a mass function (0.35 M☉ MS + 0.6 M☉ WD tail, plus segregated remnants).
Each encounter contributes an impulsive eccentricity kick δ = 2(m★/M)·min[1,(a/b)²]·(v_orb/v).
Per history (2×10⁴ per bin), survival is the random-walk first passage to orbit-crossing
eccentricity e = 0.5, capped at 12 Gyr. The radius grid starts at the Schwarzschild
ISCO (6 r_g), inside which no circular orbits exist.

**Two curves, and the difference between them matters.** The *impulsive* curves apply
no adiabatic suppression and are the conservative floor the paper quotes. The
*adiabatically corrected* curve applies the Gnedin & Ostriker (1999) kernel
A(x) = (1 + x²)^(−5/2) per encounter, with x = (b/a)(v_orb/v), and is the physical
estimate. Across the whole envelope x runs from 2.2 at the cluster stripping radius to
4.1×10³ at the ISCO, so unbound cluster stars are adiabatically decoupled from every
orbit in the envelope: the corrected lifetimes sit at the 12 Gyr cap inside ~3 AU and
never fall below ~3×10⁸ yr at the outer edge.

**Perturber mass** (referee R5, 2026-07-30): stellar-mass black holes are now 31 M☉,
the mean mass of holes inspiraling into the IMBH in the González Prieto et al. (2025)
ω Cen models, which name 10 M☉ as the assumption they are correcting. Kick variance
scales as ⟨m²⟩, so this shortens the impulsive floor by a factor 8.0 at fixed f_BH.
The `fbh_0.01_m10` configuration reproduces the pre-R5 10 M☉ curve for comparison.

**Headline results** (impulsive floor, medians at 10 / 10² / 10³ AU):

| configuration | 10 AU | 10² AU | 10³ AU | envelope minimum |
|---|---|---|---|---|
| stars + WDs only | 3.4×10⁹ | 3.3×10⁹ | 2.5×10⁹ | 1.8×10⁹ |
| f_BH = 0.1% | 1.0×10⁹ | 9.3×10⁸ | 5.8×10⁸ | 1.0×10⁸ |
| **f_BH = 1% (fiducial)** | **6.6×10⁷** | **6.3×10⁷** | **5.2×10⁷** | **2.7×10⁷** |
| f_BH = 3% | 2.2×10⁷ | 2.0×10⁷ | 1.9×10⁷ | 1.1×10⁷ |
| f_BH = 1%, 10 M☉ (pre-R5) | 5.4×10⁸ | 5.1×10⁸ | 3.5×10⁸ | 2.0×10⁸ |
| f_BH = 1%, **adiabatic (physical)** | 7.3×10⁹ | 4.5×10⁹ | 1.7×10⁹ | 3.0×10⁸ |

The profile is roughly flat because ⟨δ²⟩ ∝ a⁻¹ while the encounter rate Γ ∝ a in the
focused regime, so their product is scale-free — but that cancellation is a property
of the impulsive kernel, and the adiabatic curve is not flat. The operative outer
boundary is cluster tidal stripping at ~0.1 r_infl ≈ 4×10³ AU either way.

The script also prints the seed-to-seed spread of the min-of-bins statistic over five
seeds, which is where Appendix A's ±20–40 per cent figure comes from.

## The ln K computation (fig3)

`fig3_lnk.py` implements the v1.0 continuous MIRI likelihood (OCS-MIRI-1, referee R5
5.3): a two-temperature swarm SED integrated against the real JWST/MIRI point-source
sensitivity curve (`miri_sensitivity.json`, OCS-MIRI-DATA), detected if it exceeds the
crowding-penalized limit in any of the nine imaging filters (logical OR, never a sum).
This replaces the earlier piecewise hard-threshold model. Every prior boundary is still
a command-line switch, because ln K here is a prior-volume ratio and the boundaries are
the levers:

```sh
python fig3_lnk.py --leak-floor-dex -6      # softer transport bound
python fig3_lnk.py --pcomp-floor-dex -3     # P_comp prior floor at 1e-3 Lsun
python fig3_lnk.py --pcomp-ceiling 1e3      # ADIOS-suppressed natural fuel ceiling
python fig3_lnk.py --soft-threshold 0.5     # logistic instead of hard per-filter threshold
python fig3_lnk.py --split-floor-dex -1     # warm mass-fraction floor raised to 10%
python fig3_lnk.py --r-range 0.02 1000
python fig3_lnk.py --crowding-factor 1.0    # no crowding penalty (sanity check)
```

Measured (central ln K, band over f_d ∈ [0.1, 0.9], ξ = excluded active-prior fraction):

| configuration | ξ | ln K | band |
|---|---|---|---|
| **fiducial** | 0.755 | **−0.474** | [−1.138, −0.079] |
| leak floor 10⁻⁶ | 0.620 | −0.371 | [−0.817, −0.064] |
| P_comp floor 10⁻³ L☉ | 0.549 | −0.321 | [−0.681, −0.056] |
| ADIOS ceiling 10³ L☉ | 0.595 | −0.353 | [−0.766, −0.061] |
| radius prior [0.02, 10³] AU | 0.812 | −0.521 | [−1.313, −0.085] |
| temperature split floor 10⁻¹ | 0.747 | −0.468 | [−1.116, −0.078] |
| soft threshold 0.5 dex | 0.770 | −0.486 | [−1.182, −0.080] |

The largest lever is the P_comp floor (+0.153 nats over the fiducial), ahead of the
transport floor (+0.103) and now the fuel ceiling (+0.121) too. The temperature-split
prior is the weakest lever measured (+0.006 nats): total waste luminosity and swarm
radius dominate detectability, not how that luminosity partitions between the warm and
cool blackbody components.

The channel is one-sided: P(no detection | H_q) = 1, so ln K ≥ ln f_d = −0.693 for any
depth of photometry. At the fiducial dormancy prior the channel has spent 68 per cent
of that capacity (up from 41 per cent under the retired hard-threshold model, because
the real MIRI depths exclude far more of the active-installation prior volume than the
old order-of-magnitude piecewise limits) and has 0.22 nats of headroom left, in total,
forever.

The far-infrared corner (swarms cold enough that their Wien tail is negligible at every
MIRI wavelength, ≤25.5 μm) is not clamped by an assumed placeholder limit: it falls out
of the physics as undetected by any filter in the array, which is the honest state,
since no far-infrared instrument is currently operating (OCS-MIRI-DATA).

## Browser standalone

An independent JavaScript reimplementation of the same physics runs at
[omegacentauri.me/tools/flyby-survival.html](https://omegacentauri.me/tools/flyby-survival.html)
(40k in-browser draws, hash-state deep links, no network calls); the companion fuel
budget calculator is
[imbh-fuel-budget.html](https://omegacentauri.me/tools/imbh-fuel-budget.html).
Cross-check status: the tool tracks the **pre-R5 impulsive, 10 M☉** configuration and
agrees with `fbh_0.01_m10` within ×1.5, fully explained by the σ default (site SSOT
18.2 km/s from `measurements.js clusterParams` vs this paper's 21 km/s fiducial).
**Known follow-up:** expose the perturber mass and the adiabatic kernel in the tool, or
label it explicitly as the conservative impulsive case.

## Provenance

Draft v0.6, last revised 2026-07-30. License follows the repo: code MIT, prose CC BY 4.0.
