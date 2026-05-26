/*
  OCS Shared Measurements — measurements.js
  Omega Centauri Society — omegacentauri.me

  Code wrapper: MIT License
  Curated data tables: CC0 1.0 Universal
  Author: The Omega Centauri Society (Tim Swanson)
  Schema version: 1.0
  Last updated: 2026-05-14

  This file is the single source of truth for IMBH mass measurements,
  globular cluster properties, and Omega Centauri pulsar timing data
  used by /tools/*.html. It is loaded via:

      <script src="data/measurements.js"></script>

  ...exposing window.OCS_MEASUREMENTS. No fetch(), no module system,
  no build step — works under file:// without CORS issues.

  Adding a new measurement: append to the relevant array, follow the
  existing schema, include DOI, and bump meta.lastUpdated. See
  CONTRIBUTING.md.
*/

window.OCS_MEASUREMENTS = {

  /* ================================================================
     IMBH mass estimates / limits for Omega Centauri (NGC 5139)
     ================================================================
     Schema:
       id              short stable identifier
       year            publication year
       authors         "First Author et al." or full short list
       value           central value or limit value, in M_sun.
                       null for "no evidence" or parameter-dependent.
       uncertaintyLo   for symmetric error bars (lower extent), M_sun
       uncertaintyHi   upper extent, M_sun
       limitType       "detection" | "upper" | "lower" | "noEvidence" | "parameterDependent"
       sigma           confidence in sigma if limit (e.g. 3 = 3σ)
       confidenceLevel optional, fractional (e.g. 0.90 for 90% CL)
       method          "kinematics" | "propermotion" | "timing" | "nbody" | "accretion"
       methodLabel     human-readable
       journal         short journal reference
       doi             DOI string (no leading url)
       url             optional fallback url
       notes           1-2 sentence summary; appears in detail card
  */
  imbh: [
    {
      id: "noyola2008",
      year: 2008,
      authors: "Noyola, Gebhardt & Bergmann",
      value: 4e4,
      uncertaintyLo: 1e4,
      uncertaintyHi: 1e4,
      limitType: "detection",
      method: "kinematics",
      methodLabel: "Stellar kinematics (Gemini/GMOS integral-field)",
      journal: "ApJ 676:1008",
      doi: "10.1086/529002",
      notes: "Positive detection from central kinematic mass profile using Gemini/GMOS integral-field spectroscopy. The headline number that opened the modern OC IMBH debate."
    },
    {
      id: "vandermarel2010",
      year: 2010,
      authors: "van der Marel & Anderson",
      value: 1.2e4,
      limitType: "upper",
      sigma: 3,
      method: "kinematics",
      methodLabel: "Stellar kinematics (HST proper motions)",
      journal: "ApJ 710:1063",
      doi: "10.1088/0004-637X/710/2/1063",
      notes: "Re-analysis with an improved kinematic centre placed a 3σ upper limit, contradicting the Noyola detection. The first major challenge to the IMBH hypothesis for OC."
    },
    {
      id: "baumgardt2017",
      year: 2017,
      authors: "Baumgardt",
      value: null,
      limitType: "noEvidence",
      method: "nbody",
      methodLabel: "N-body modelling",
      journal: "MNRAS 464:2174",
      doi: "10.1093/mnras/stw2488",
      notes: "Best-fit N-body models without an IMBH match observations as well as those with one. This is 'consistent with zero' — epistemically distinct from a numerical upper limit."
    },
    {
      id: "haberle2024",
      year: 2024,
      authors: "Häberle et al.",
      value: 8200,
      limitType: "lower",
      method: "propermotion",
      methodLabel: "Proper motion (HST, 7 fast stars)",
      journal: "Nature 631:285",
      doi: "10.1038/s41586-024-07511-z",
      notes: "Lower bound from seven fast-moving stars in the central 3 arcsec, requiring a compact enclosed mass. Authors propose a best-fit mass range of 39,000–47,000 M☉."
    },
    {
      id: "banares2025",
      year: 2025,
      authors: "Bañares-Hernández et al.",
      value: 6000,
      limitType: "upper",
      sigma: 3,
      method: "timing",
      methodLabel: "Stellar kinematics + pulsar timing (combined)",
      journal: "A&A 693:A104",
      doi: "10.1051/0004-6361/202451763",
      notes: "Joint kinematic + pulsar timing analysis. Favors an extended central mass distribution (~2–3 × 10⁵ M☉) over a single IMBH. The 3σ upper limit is in tension with the Häberle lower bound."
    },
    {
      id: "omegacat6_2025",
      year: 2025,
      authors: "Häberle et al. (oMEGACat VI)",
      value: null,
      limitType: "noEvidence",
      method: "kinematics",
      methodLabel: "3D kinematics (HST proper motion + VLT RVs)",
      journal: "ApJ (April 2025)",
      doi: "10.3847/1538-4357/adbe67",
      notes: "Comprehensive 3D kinematic catalog (~1.4M proper motions). No point estimate of IMBH mass — included as the canonical kinematic dataset that downstream analyses use."
    },
    {
      id: "chen2025jwst",
      year: 2025,
      authors: "Chen et al.",
      value: null,
      limitType: "parameterDependent",
      method: "accretion",
      methodLabel: "JWST NIRSpec (no accretion signature)",
      journal: "arXiv:2511.20945",
      doi: "10.48550/arXiv.2511.20945",
      url: "https://arxiv.org/abs/2511.20945",
      notes: "JWST NIRSpec observations show no detectable accretion signature. The mass upper limit derived from this depends sensitively on assumed ADAF radiative efficiency and ambient gas density — see the JWST Accretion Limit tool for the full curve.",
      isParameterDependent: true
    },
    {
      id: "trapum2026",
      year: 2026,
      authors: "TRAPUM (Padmanabh et al.)",
      value: 1e5,
      limitType: "upper",
      sigma: 1.65,
      confidenceLevel: 0.90,
      method: "timing",
      methodLabel: "Pulsar timing (MeerKAT + Parkes, 2021–2025)",
      journal: "arXiv:2603.21845",
      doi: "10.48550/arXiv.2603.21845",
      url: "https://arxiv.org/abs/2603.21845",
      notes: "Independent constraint from Fourier-domain acceleration searches and timing of OC millisecond pulsars. Discovered a new isolated MSP (PSR J1326-4728S) along the way."
    }
  ],

  /* ================================================================
     Globular cluster properties (Tool 5 — Cluster Comparator)
     ================================================================
     Source: Baumgardt & Hilker (2018) for cluster properties unless
     noted; IMBH values via imbhRefs[] cross-reference.
  */
  clusters: [
    {
      id: "ngc5139",
      name: "Omega Centauri (NGC 5139)",
      totalMass: 4.0e6,
      halfLightRadius: 7.0,
      ageGyr: 12.1,  // oMEGACat IV mean (Häberle et al. 2024); individual populations span ~11–14 Gyr
      isOmegaCentauri: true,
      imbhRefs: ["noyola2008", "vandermarel2010", "baumgardt2017",
                 "haberle2024", "banares2025", "chen2025jwst",
                 "trapum2026", "omegacat6_2025"],
      imbhSummary: {
        value: 8200,
        limitType: "lower",
        reference: "Häberle et al. 2024",
        doi: "10.1038/s41586-024-07511-z",
        note: "Disputed by Bañares 2025 (3σ <6,000 M☉) and Chen 2025 (JWST accretion). Active tension in the literature."
      }
    },
    {
      id: "ngc7078",
      name: "M15 (NGC 7078)",
      totalMass: 5.6e5,
      halfLightRadius: 1.06,
      ageGyr: 12.0,
      imbhSummary: {
        value: 2000,
        limitType: "upper",
        sigma: 3,
        reference: "Kirsten & Vlemmings 2012",
        doi: "10.1051/0004-6361/201219049",
        note: "Radio + VLBI proper motion limit. Earlier Gerssen 2002 claim of ~4,000 M☉ was contested and is no longer favored."
      }
    },
    {
      id: "ngc6388",
      name: "NGC 6388",
      totalMass: 1.5e6,
      halfLightRadius: 0.67,
      ageGyr: 12.0,
      imbhSummary: {
        value: 1.7e4,
        limitType: "detection",
        reference: "Lützgendorf et al. 2011",
        doi: "10.1051/0004-6361/201117636",
        note: "Detection from integral-field kinematics; debated. Cseh et al. 2010 radio non-detection sets upper limit at lower mass under standard accretion assumptions."
      }
    },
    {
      id: "ngc6656",
      name: "M22 (NGC 6656)",
      totalMass: 4.8e5,
      halfLightRadius: 3.36,
      ageGyr: 12.0,
      imbhSummary: {
        value: null,
        limitType: "noEvidence",
        reference: "Strader et al. 2012",
        doi: "10.1038/nature11490",
        note: "Two stellar-mass black hole candidates detected via radio, not an IMBH. Subsequent searches set upper limits ~1.5×10³ M☉."
      }
    },
    {
      id: "ngc104",
      name: "47 Tucanae (NGC 104)",
      totalMass: 7.0e5,
      halfLightRadius: 3.66,
      ageGyr: 11.8,
      imbhSummary: {
        value: 2300,
        limitType: "detection",
        reference: "Kızıltan et al. 2017",
        doi: "10.1038/nature21361",
        note: "Inferred from pulsar timing accelerations. Disputed by Mann et al. 2019 N-body analysis favoring a stellar-mass BH cluster instead."
      }
    },
    {
      id: "ngc6715",
      name: "M54 (NGC 6715)",
      totalMass: 1.4e6,
      halfLightRadius: 2.45,
      ageGyr: 12.5,
      imbhSummary: {
        value: 9400,
        limitType: "detection",
        reference: "Ibata et al. 2009",
        doi: "10.1088/0004-637X/699/1/L169",
        note: "Detection from HST stellar kinematics. M54 is the nuclear cluster of the Sagittarius dwarf galaxy, so any IMBH is more naturally interpreted as a former dwarf-galaxy nucleus than a true GC IMBH."
      }
    }
  ],

  /* ================================================================
     Omega Centauri pulsars (Tool 9 — Pulsar Timing)
     ================================================================
     TODO: populate when building Tool 9. Source: TRAPUM 2026 +
     Chen et al. 2023 (MNRAS 520:3847).
  */
  pulsars: [
    /* Representative OC pulsars from MeerKAT/Parkes timing programs (Chen et al. 2023,
       TRAPUM 2026). Angular distances are projected separations from the cluster
       photometric centre; timing precision values are typical post-fit RMS residuals
       reported in the discovery papers. PLACEHOLDER VALUES — replace with current
       per-pulsar table when TRAPUM updates its OC ephemerides catalog. */
    {
      id: "j1326_4728a", name: "PSR J1326-4728A",
      period_ms: 4.53, dist_arcsec: 28, timing_us: 2.5,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated millisecond pulsar in OC core region."
    },
    {
      id: "j1326_4728b", name: "PSR J1326-4728B",
      period_ms: 9.10, dist_arcsec: 47, timing_us: 8.0,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary millisecond pulsar; timing affected by orbital model."
    },
    {
      id: "j1326_4728c", name: "PSR J1326-4728C",
      period_ms: 6.34, dist_arcsec: 86, timing_us: 4.5,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP in the cluster halo."
    },
    {
      id: "j1326_4728d", name: "PSR J1326-4728D",
      period_ms: 3.85, dist_arcsec: 153, timing_us: 12,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Outer-region MSP; less constraining for IMBH due to large r."
    },
    {
      id: "j1326_4728s", name: "PSR J1326-4728S",
      period_ms: 4.54, dist_arcsec: 38, timing_us: 3.0,
      discovery: "TRAPUM (Padmanabh et al.) 2026", doi: "10.48550/arXiv.2603.21845",
      notes: "Newly discovered isolated MSP, closer to cluster centre — informative for IMBH constraint."
    }
  ],

  /* ================================================================
     Metadata
     ================================================================ */
  meta: {
    lastUpdated: "2026-05-14",
    schemaVersion: "1.0",
    sources: [
      "10.1086/529002",
      "10.1088/0004-637X/710/2/1063",
      "10.1093/mnras/stw2488",
      "10.1038/s41586-024-07511-z",
      "10.1051/0004-6361/202451763",
      "10.3847/1538-4357/adbe67",
      "10.48550/arXiv.2511.20945",
      "10.48550/arXiv.2603.21845"
    ],
    methodColors: {
      kinematics:   "#1dba90",  // teal-bright
      propermotion: "#a080f0",  // purple-glow
      timing:       "#f0a020",  // amber-bright
      nbody:        "#9890c0",  // text-secondary (grey)
      accretion:    "#d04040"   // red-bright
    }
  }
};
