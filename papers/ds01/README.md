# DS-01 (Gaia DR3 6083772968079356544): data products and analysis scripts

Mirror of the data products and analysis scripts behind the DS-01 cataclysmic-variable-candidate
paper (MNRAS submission and RNAAS note, Omega Centauri Society). The manuscript sources are not
mirrored here until publication. Data and code licences follow `LICENSE-data.md` and `LICENSE-code.md`
at the repository root. A Zenodo DOI for this directory is added at publication.

| Path | Contents |
|---|---|
| `data/` | Fermi-LAT per-bin light curve `lc_j1325.json` (4FGL J1325.4-4706 fit); Gaia Discrete Source Classifier query (`.adql`) and its output (`.csv`) |
| `scripts/`, `out/` | Archival query scripts and their outputs (Gaia, survey cone searches, HEASARC, Swift, MAST, eROSITA, Einstein) |
| `bounds/pm-member/` | Proper-motion membership statistics: scripts and JSON outputs (`out/q1_chi2.json`, `out/q5_window.json`, ...) |
| `bounds/field-interloper/` | Field-interloper estimate: scripts and JSON outputs (`out/q5_fraction.json`, ...) |

All archival inputs are public. Several scripts read raw downloads from a local cache path
(`C:\farm\cache\omegacen\...`); those raw caches are not mirrored and are re-fetched by the
`fetch*` scripts and `scripts/q*` queries. Pipeline outputs of the Fermi-LAT fit other than
`data/lc_j1325.json`, the Einstein IPC re-extraction, and the UV spectral-energy-distribution
re-derivation are not part of this mirror.
