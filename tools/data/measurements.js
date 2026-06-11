/*
  OCS Shared Measurements — measurements.js
  Omega Centauri Society — omegacentauri.me

  Code wrapper: MIT License
  Curated data tables: CC0 1.0 Universal
  Author: The Omega Centauri Society (Tim Swanson)
  Schema version: 1.0
  Last updated: 2026-06-04

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
      methodLabel: "JWST NIRCam + MIRI photometry (no accretion signature)",
      journal: "arXiv:2511.20945",
      doi: "10.48550/arXiv.2511.20945",
      url: "https://arxiv.org/abs/2511.20945",
      notes: "JWST NIRCam + MIRI photometric observations (not NIRSpec) show no detectable accretion signature. The mass upper limit derived from this depends sensitively on assumed ADAF radiative efficiency and ambient gas density — see the JWST Accretion Limit tool for the full curve.",
      isParameterDependent: true
    },
    {
      id: "gonzalezprieto2025",
      year: 2025,
      authors: "González Prieto, Rodriguez & Cabrera",
      value: 5e4,
      uncertaintyLo: 2e4,
      uncertaintyHi: 2e4,
      limitType: "detection",
      method: "nbody",
      methodLabel: "Monte Carlo N-body (loss-cone dynamics, TDE + BH mergers)",
      journal: "ApJL",
      doi: "10.3847/2041-8213/adfd4a",
      url: "https://arxiv.org/abs/2507.06316",
      notes: "Monte Carlo N-body models of OC with detailed loss-cone dynamics. Seeds of 500–5,000 M☉ grow to ~50,000 M☉ over 12 Gyr via TDE accretion and compact-object mergers while reproducing observed surface brightness and velocity dispersion. Model-derived estimate, not a direct kinematic measurement."
    },
    {
      id: "trapum2026",
      year: 2026,
      authors: "TRAPUM (Colom i Bernadich et al.)",
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
     Source: Baumgardt & Hilker (2018) for most cluster properties (masses, radii)
     unless noted. OC totalMass uses the Harris/dynamical 4.0×10⁶ value (B&H give 3.5×10⁶).
     halfLightRadius values are in parsecs (B&H half-mass radii); Harris catalogue gives
     angular half-light radii (arcmin) which at cluster distances convert to somewhat
     different pc values due to distance and photometric vs. mass-based conventions.
     IMBH values via imbhRefs[] cross-reference.
  */
  clusters: [
    {
      id: "ngc5139",
      name: "Omega Centauri (NGC 5139)",
      totalMass: 4.0e6,   // Harris/dynamical estimate; Baumgardt & Hilker 2018 give 3.5×10⁶ M☉ (source differs — see FAQ)
      halfLightRadius: 7.0,  // parsecs, Baumgardt & Hilker 2018 half-mass radius ~6.9 pc; Harris r_h ~5.0′ = ~8 pc at 5.49 kpc (different convention)
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
        value: 500,
        limitType: "upper",
        sigma: 3,
        reference: "Kirsten & Vlemmings 2012",
        doi: "10.1051/0004-6361/201218928",
        note: "Radio + VLBI proper motion: < 500 M☉ (3σ). DOI corrected (was 201219049). Earlier Gerssen 2002 claim of ~4,000 M☉ was contested and is no longer favored."
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
      totalMass: 9.5e5,   // Baumgardt & Hilker 2018: ~0.9–1.0×10⁶ M☉; earlier 7.0×10⁵ was ~30% low
      halfLightRadius: 3.66,  // parsecs, Baumgardt & Hilker 2018; Harris r_h ~3.17′ = ~4.2 pc at 4.5 kpc (different convention)
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
    /* All 19 OC millisecond pulsars from TRAPUM 2026 (arXiv:2603.21845, Colom i Bernadich et al.)
       and Dai et al. 2023 (MNRAS 520:3847, DOI 10.1093/mnras/stad029). Periods and angular
       separations from TRAPUM Table 1. Pulsars A–E are from Dai 2023; F–S from TRAPUM 2026
       discovery census; S is the new TRAPUM 2026 detection.
       pdot_s: spin-period derivative in s/s (null = no timing solution yet).
               Positive = conventional spin-down; negative = apparent spin-up from cluster
               line-of-sight acceleration (cluster potential accelerates pulsar toward observer).
       theta_arcmin: projected angular separation from cluster photometric centre (arcmin).
       dist_arcsec: same in arcseconds (theta_arcmin × 60); preserved for pulsar-timing.html compat.
       timing_us: post-fit RMS timing residual (µs); estimated for pulsars without published values.
       binary: true if in a binary system (binary pulsars require orbital model in pdot).
    */
    {
      id: "j1326_4728a", name: "PSR J1326-4728A",
      period_ms: 4.109, theta_arcmin: 1.93, dist_arcsec: 115.8, timing_us: 2.0,
      pdot_s: 2.73e-20, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; positive ṗ reflects intrinsic spin-down plus cluster acceleration."
    },
    {
      id: "j1326_4728b", name: "PSR J1326-4728B",
      period_ms: 4.792, theta_arcmin: 0.76, dist_arcsec: 45.6, timing_us: 4.0,
      pdot_s: -5.43e-20, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP; negative ṗ indicates dominant line-of-sight cluster acceleration toward observer."
    },
    {
      id: "j1326_4728c", name: "PSR J1326-4728C",
      period_ms: 6.868, theta_arcmin: 1.98, dist_arcsec: 118.8, timing_us: 3.0,
      pdot_s: 1.01e-20, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; measured spin-down contributes to IMBH acceleration probe."
    },
    {
      id: "j1326_4728d", name: "PSR J1326-4728D",
      period_ms: 4.579, theta_arcmin: 2.50, dist_arcsec: 150.0, timing_us: 5.0,
      pdot_s: -4.12e-20, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; negative ṗ (apparent spin-up from cluster gravitational acceleration)."
    },
    {
      id: "j1326_4728e", name: "PSR J1326-4728E",
      period_ms: 4.208, theta_arcmin: 1.58, dist_arcsec: 94.8, timing_us: 2.5,
      pdot_s: 1.63e-20, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP with clean spin-down measurement."
    },
    {
      id: "j1326_4728f", name: "PSR J1326-4728F",
      period_ms: 2.273, theta_arcmin: 1.00, dist_arcsec: 60.0, timing_us: 10.0,
      pdot_s: null, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; no timing solution for spin-period derivative yet."
    },
    {
      id: "j1326_4728g", name: "PSR J1326-4728G",
      period_ms: 3.304, theta_arcmin: 1.96, dist_arcsec: 117.6, timing_us: 4.0,
      pdot_s: 2.77e-20, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP with measured spin-period derivative."
    },
    {
      id: "j1326_4728h", name: "PSR J1326-4728H",
      period_ms: 2.520, theta_arcmin: 0.56, dist_arcsec: 33.6, timing_us: 1.5,
      pdot_s: 3.99e-20, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Closest pulsar to cluster centre; most constraining for any central-mass IMBH model."
    },
    {
      id: "j1326_4728i", name: "PSR J1326-4728I",
      period_ms: 18.95, theta_arcmin: 3.53, dist_arcsec: 211.8, timing_us: 10.0,
      pdot_s: null, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP with long period; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728j", name: "PSR J1326-4728J",
      period_ms: 3.686, theta_arcmin: 1.80, dist_arcsec: 108.0, timing_us: 10.0,
      pdot_s: null, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728k", name: "PSR J1326-4728K",
      period_ms: 4.716, theta_arcmin: 1.89, dist_arcsec: 113.4, timing_us: 5.0,
      pdot_s: -0.91e-20, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP; small negative ṗ indicates mild line-of-sight cluster acceleration."
    },
    {
      id: "j1326_4728l", name: "PSR J1326-4728L",
      period_ms: 3.537, theta_arcmin: 3.32, dist_arcsec: 199.2, timing_us: 10.0,
      pdot_s: null, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP in outer cluster region; no spin-derivative measurement."
    },
    {
      id: "j1326_4728m", name: "PSR J1326-4728M",
      period_ms: 4.604, theta_arcmin: 2.40, dist_arcsec: 144.0, timing_us: 10.0,
      pdot_s: null, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728n", name: "PSR J1326-4728N",
      period_ms: 6.884, theta_arcmin: 2.66, dist_arcsec: 159.6, timing_us: 10.0,
      pdot_s: null, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728o", name: "PSR J1326-4728O",
      period_ms: 6.160, theta_arcmin: 1.50, dist_arcsec: 90.0, timing_us: 10.0,
      pdot_s: null, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728p", name: "PSR J1326-4728P",
      period_ms: 2.795, theta_arcmin: 1.00, dist_arcsec: 60.0, timing_us: 10.0,
      pdot_s: null, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Isolated MSP; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728q", name: "PSR J1326-4728Q",
      period_ms: 4.130, theta_arcmin: 2.30, dist_arcsec: 138.0, timing_us: 10.0,
      pdot_s: null, binary: true,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Binary MSP; no spin-derivative measurement yet."
    },
    {
      id: "j1326_4728r", name: "PSR J1326-4728R",
      period_ms: 10.29, theta_arcmin: 3.90, dist_arcsec: 234.0, timing_us: 10.0,
      pdot_s: null, binary: false,
      discovery: "Chen et al. 2023", doi: "10.1093/mnras/stad029",
      notes: "Outer-halo isolated MSP; no spin-derivative measurement."
    },
    {
      id: "j1326_4728s", name: "PSR J1326-4728S",
      period_ms: 4.538, theta_arcmin: 2.32, dist_arcsec: 139.2, timing_us: 3.0,
      pdot_s: null, binary: false,
      discovery: "TRAPUM (Colom i Bernadich et al.) 2026", doi: "10.48550/arXiv.2603.21845",
      notes: "Newly discovered isolated MSP (TRAPUM 2026); no spin-derivative yet — recent discovery."
    }
  ],

  /* ================================================================
     OC physical constants — single source of truth for all tools
     ================================================================
     Tools should read these as window.OCS_MEASUREMENTS.clusterParams.X
     rather than hardcoding values. Prevents the 5,030–5,494 pc drift
     that accumulated when each tool chose its own distance.
  */
  clusterParams: {
    OC_distance_pc: 5490,   // parsecs; Harris 2010 / oMEGACat consensus value (range in literature: 5,030–5,494)
    OC_sigma0_kms:  18.2,   // km/s; core velocity dispersion, van de Ven et al. 2006 (ApJ 641:L37)
  },

  /* ================================================================
     Metadata
     ================================================================ */
  meta: {
    lastUpdated: "2026-06-11",
    schemaVersion: "1.0",
    sources: [
      "10.1086/529002",
      "10.1088/0004-637X/710/2/1063",
      "10.1093/mnras/stw2488",
      "10.1038/s41586-024-07511-z",
      "10.1051/0004-6361/202451763",
      "10.3847/1538-4357/adbe67",
      "10.48550/arXiv.2511.20945",
      "10.48550/arXiv.2603.21845",
      "10.3847/2041-8213/adfd4a"
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
