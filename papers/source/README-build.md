# Build instructions — mth-paper

Requires a TeX distribution (MiKTeX or TeX Live) with `newtx`, `pgfplots`, `natbib`, `booktabs`, `microtype`.

```powershell
cd "C:\dev\Claude\Projects\The Omega Centauri Society\paper"
pdflatex mth-paper
bibtex mth-paper
pdflatex mth-paper
pdflatex mth-paper
```

All six figures are TikZ/pgfplots (vector, in-document) — no external image files, so the same two source files (`mth-paper.tex` + `references.bib`) are the complete arXiv submission package.

## Verification status (2026-06-10)

- **Citations:** all 90+ entries in `references.bib` verified against ADS/arXiv/publisher pages by three independent verification passes. Two fabricated references found in site material were **excluded** ("Myung et al. 2021 Nat. Rev. Phys." and "Sheikh et al. 2021 ApJL 915 L14" do not exist). Corrections applied: Sandberg et al. is 2016 (JBIS 69), Zocchi et al. 2019 is MNRAS 482:4713 (not L9), Soltis et al. is ApJL 908:L5, Bekki & Tsujimoto is ApJ 886:121, Clontz et al. is ApJ 977:14, Mahida et al. is 2026 (ApJ 996:122), Tchekhovskoy 2015 chapter DOI ends `_3`.
- **Arithmetic:** all fiducial numbers re-derived by hand (Eddington luminosity/rate, η(a★) values, ISCO radii, dτ/dt, Hawking temperatures, Bekenstein–Hawking bit counts, spin-up mass budget, tidal field). Two site-derived figures were corrected in the paper: the IMBH/Dyson instantaneous-power ratio is ~10⁹ (the site's ~10¹² is wrong), and ISCO tidal gradients are ~1 s⁻² (not negligible for km-scale rigid structures).
- **Not yet done:** LaTeX compile (sandbox unavailable — run the block above locally and send me any errors).

## Claims register discipline

Established physics: Secs. 4, 5.1–5.3. Speculative (boxed, labeled): Secs. 3, 6. The paper takes the gas-starvation null as default throughout.
