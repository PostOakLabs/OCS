/*
  imbh-constraints — core engine
  The Omega Centauri Society — omegacentauri.me

  Code: MIT License. Author: The Omega Centauri Society (Tim Swanson).
  Library version: 1.0.0
  Schema version: 1.0

  THE evidence-aggregation engine for the Omega Centauri IMBH debate,
  generalized to any contested-compact-object-mass problem: a declarative
  schema for heterogeneous mass constraints (detection / upper / lower /
  no-evidence / parameter-dependent) plus the window-and-tension math that
  was previously duplicated across constraint-stacker.html, the evidence
  dashboard, and the ocs-mcp-worker kernel.

  ---------------------------------------------------------------------------
  WHY THIS FILE IS A CLASSIC SCRIPT AND NOT AN ES MODULE
  ---------------------------------------------------------------------------
  Site architecture rule 3: tools must run from file:// with no network calls.
  ES module scripts are fetched under CORS and a file:// page has an opaque
  origin, so `<script type="module">` + `import` fails outright on file://.
  This file is therefore a classic script that assigns a single global, the
  same pattern data/measurements.js already proved across ~104 pages.

  Consumed two ways, no build step:

    browser   <script src="lib/imbh-constraints.core.js"></script>
              → globalThis.IMBHConstraints

    Node/ESM  import { computeWindow } from './lib/imbh-constraints.mjs';
              → imbh-constraints.mjs is a thin named-export facade over this
                file; it is the importable surface for tests and downstream
                reuse. Both paths execute this one authored source.

  ---------------------------------------------------------------------------
  DOCTRINE: TENSION RECORDS ARE NEVER COLLAPSED
  ---------------------------------------------------------------------------
  The Häberle 2024 lower bound (≥8,200 M☉) and the Bañares 2025 upper limit
  (≤6,000 M☉) are mutually incompatible, both current, both valid. A window
  returned by this library therefore reports `tension: true` and PRESERVES
  both bounds with their sources. It must never average, midpoint, or
  otherwise reconcile them into a single number. Callers that want a scalar
  must make that choice explicitly and own it. See computeWindow().
*/

(function (root, factory) {
  var api = factory();
  root.IMBHConstraints = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // ---------------------------------------------------------------------
  // Physical constants (SI). Must stay identical to the values in
  // tools/constraint-stacker.html and the ocs-mcp-worker kernel; the
  // parity gate in ocs-mcp-worker CI fails if they ever drift.
  // ---------------------------------------------------------------------
  var G_SI    = 6.674e-11;   // m³ kg⁻¹ s⁻²
  var C_SI    = 2.998e8;     // m/s
  var MSUN_KG = 1.989e30;    // kg

  // ---------------------------------------------------------------------
  // Schema
  // ---------------------------------------------------------------------
  // A constraint is a published statement about the mass of a candidate
  // compact object. `limitType` is the epistemic kind of that statement —
  // the distinction the whole engine turns on:
  //
  //   detection           a central value with uncertainty. Does NOT bound
  //                       the window: a detection is consistent with its own
  //                       error bars, and treating it as a bound would
  //                       silently discard those errors.
  //   upper               M < value at the quoted significance. Bounds hi.
  //   lower               M > value. Bounds lo.
  //   noEvidence          consistent with zero. Epistemically distinct from
  //                       a numerical upper limit — carries no number and so
  //                       bounds nothing. (Baumgardt 2017 is the type case.)
  //   parameterDependent  the limit is a curve, not a scalar; it is only
  //                       realized once the caller supplies the nuisance
  //                       parameters. (Chen 2025 JWST: depends on ADAF
  //                       radiative efficiency ε and ambient density ρ∞.)
  var LIMIT_TYPES = ['detection', 'upper', 'lower', 'noEvidence', 'parameterDependent'];

  // Observational channel. Lanes are the unit of caller-facing visibility
  // toggling, and their order is the canonical display/report order.
  var METHODS = ['kinematics', 'propermotion', 'timing', 'accretion', 'nbody'];

  function isPlainObject(v) {
    return !!v && typeof v === 'object' && !Array.isArray(v);
  }

  /**
   * Validate one constraint against the schema.
   * Returns an array of human-readable problems; empty means valid.
   * Pure — never throws on bad input, so callers can report every problem
   * in a set at once rather than dying on the first.
   */
  function validateConstraint(c, index) {
    var where = 'constraint' + (index === undefined ? '' : '[' + index + ']');
    var errs = [];
    if (!isPlainObject(c)) return [where + ': not an object'];
    if (typeof c.id !== 'string' || !c.id) errs.push(where + ': missing string `id`');
    var tag = where + ' (' + (c.id || '?') + ')';
    if (LIMIT_TYPES.indexOf(c.limitType) === -1) {
      errs.push(tag + ': `limitType` must be one of ' + LIMIT_TYPES.join(' | ') + ', got ' + JSON.stringify(c.limitType));
    }
    if (METHODS.indexOf(c.method) === -1) {
      errs.push(tag + ': `method` must be one of ' + METHODS.join(' | ') + ', got ' + JSON.stringify(c.method));
    }
    var hasValue = c.value !== null && c.value !== undefined;
    if (hasValue && (typeof c.value !== 'number' || !isFinite(c.value))) {
      errs.push(tag + ': `value` must be a finite number or null, got ' + JSON.stringify(c.value));
    }
    if (hasValue && typeof c.value === 'number' && c.value <= 0) {
      errs.push(tag + ': `value` must be positive (masses are in M☉), got ' + c.value);
    }
    // A bounding constraint without a number cannot bound anything.
    if ((c.limitType === 'upper' || c.limitType === 'lower') && !hasValue) {
      errs.push(tag + ': limitType `' + c.limitType + '` requires a numeric `value`');
    }
    // noEvidence carrying a number is a category error: it would read as a
    // bound to anyone scanning the table.
    if (c.limitType === 'noEvidence' && hasValue) {
      errs.push(tag + ': limitType `noEvidence` must have `value: null` (it is consistent-with-zero, not a numeric limit)');
    }
    return errs;
  }

  /** Validate a whole set. Returns { valid, errors }. */
  function validateConstraintSet(constraints) {
    if (!Array.isArray(constraints)) {
      return { valid: false, errors: ['constraint set: expected an array, got ' + typeof constraints] };
    }
    var errors = [];
    var seen = Object.create(null);
    for (var i = 0; i < constraints.length; i++) {
      errors = errors.concat(validateConstraint(constraints[i], i));
      var id = constraints[i] && constraints[i].id;
      if (typeof id === 'string' && id) {
        if (seen[id]) errors.push('constraint[' + i + ']: duplicate id `' + id + '`');
        seen[id] = true;
      }
    }
    return { valid: errors.length === 0, errors: errors };
  }

  // ---------------------------------------------------------------------
  // Parameter-dependent limit: JWST accretion (Chen et al. 2025,
  // arXiv:2511.20945)
  // ---------------------------------------------------------------------
  //   L_predicted = ε · Ṁ_Bondi · c²        with  Ṁ_Bondi = 4π G² M² ρ∞ / c_s³
  // Solving L_predicted = L_limit for M:
  //   M = sqrt( L_limit · c_s³ / (ε · 4π G² ρ∞ · c²) )
  //
  // c_s³ is written as explicit multiplication rather than Math.pow: the
  // worker kernel runs under a guest runtime that bans transcendentals, and
  // an integer exponent must not be the reason the two copies drift.
  var JWST_DEFAULTS = {
    L_limit: 1e28,  // W  (10^35 erg/s; matches jwst-accretion.html)
    c_s:     1.0e4  // m/s (~10 km/s, typical globular-cluster core sound speed)
  };

  /**
   * JWST-derived upper limit on mass, in M☉.
   * Returns null when the inputs do not define a physical limit, rather than
   * NaN/Infinity: a null propagates as "this lane bounds nothing", which is
   * the honest reading, whereas NaN would silently poison a comparison.
   */
  function jwstUpperLimitMsun(epsilon, rho_inf, opts) {
    var o = opts || JWST_DEFAULTS;
    var c_s = o.c_s, L = o.L_limit;
    var c_s3 = c_s * c_s * c_s;
    var num = L * c_s3;
    var den = epsilon * 4 * Math.PI * G_SI * G_SI * rho_inf * C_SI * C_SI;
    if (!isFinite(den) || den === 0) return null;
    var ratio = num / den;
    if (!isFinite(ratio) || ratio < 0) return null;
    var v = Math.sqrt(ratio) / MSUN_KG;
    return isFinite(v) ? v : null;
  }

  // ---------------------------------------------------------------------
  // M–σ prediction (Gültekin et al. 2009, ApJ 698:198, Table 3 E sample)
  //   log(M_BH/M☉) = 8.12 + 4.24 · log(σ/200)
  // Reported for context only: it is an extrapolation of a galaxy-scale
  // relation far below its calibrated range, so it never enters the window.
  // ---------------------------------------------------------------------
  var OC_SIGMA_KMS = 20.0;
  function mSigmaPrediction(sigma_kms) {
    var s = (sigma_kms === undefined) ? OC_SIGMA_KMS : sigma_kms;
    return Math.pow(10, 8.12) * Math.pow(s / 200, 4.24);
  }

  // ---------------------------------------------------------------------
  // The window
  // ---------------------------------------------------------------------
  /**
   * Aggregate heterogeneous constraints into the currently allowed mass range.
   *
   * @param {Array}  constraints  constraint set (see schema above)
   * @param {Object} options
   *   @param {Object|string} options.show  active lanes: {kinematics:true,...}
   *                                        or a comma-joined method string
   *   @param {number} options.epsilon      ADAF radiative efficiency ε
   *   @param {number} options.rho          ambient density ρ∞ (kg/m³)
   *   @param {Object} options.jwst         override JWST_DEFAULTS
   *
   * @returns {{lo:?number, hi:?number, tension:boolean, lowSrc:?Object, hiSrc:?Object}}
   *   lo/hi are M☉, null when unbounded on that side.
   *
   * When lo > hi the constraints are mutually unsatisfiable. Both bounds and
   * both sources are still returned, with tension:true. This is deliberate
   * and load-bearing: the incompatibility IS the scientific result, and a
   * caller must not be handed a reconciled number that hides it.
   */
  function computeWindow(constraints, options) {
    var opts = options || {};
    var show = normalizeShow(opts.show);
    var epsilon = numberOr(opts.epsilon, 1e-3);
    var rho = numberOr(opts.rho, 1e-21);

    var lo = -Infinity, hi = Infinity;
    var lowSrc = null, hiSrc = null;
    var list = Array.isArray(constraints) ? constraints : [];

    for (var i = 0; i < list.length; i++) {
      var m = list[i];
      if (!m || !show[m.method]) continue;

      if (m.limitType === 'lower' && m.value !== null && m.value !== undefined) {
        if (m.value > lo) { lo = m.value; lowSrc = m; }
      } else if (m.limitType === 'upper' && m.value !== null && m.value !== undefined) {
        if (m.value < hi) { hi = m.value; hiSrc = m; }
      } else if (m.limitType === 'parameterDependent' && m.method === 'accretion') {
        var v = jwstUpperLimitMsun(epsilon, rho, opts.jwst);
        if (v !== null && v < hi) { hi = v; hiSrc = assign({}, m, { value: v }); }
      }
      // 'detection' and 'noEvidence' bound nothing — see the schema notes.
    }

    if (lo === -Infinity) lo = null;
    if (hi === Infinity) hi = null;
    return {
      lo: lo,
      hi: hi,
      tension: (lo !== null && hi !== null && lo > hi),
      lowSrc: lowSrc,
      hiSrc: hiSrc
    };
  }

  /** Constraints in the set that belong to an active lane. */
  function activeConstraints(constraints, show) {
    var s = normalizeShow(show);
    return (Array.isArray(constraints) ? constraints : []).filter(function (m) {
      return !!(m && s[m.method]);
    });
  }

  /** Active lanes, in canonical METHODS order. */
  function activeLanes(show) {
    var s = normalizeShow(show);
    return METHODS.filter(function (m) { return !!s[m]; });
  }

  // Accepts {kinematics:true,...} or "kinematics,timing" or undefined.
  function normalizeShow(show) {
    var out = {};
    if (typeof show === 'string') {
      var parts = show.split(',');
      for (var i = 0; i < parts.length; i++) if (parts[i]) out[parts[i]] = true;
      return out;
    }
    if (isPlainObject(show)) {
      for (var k in show) if (Object.prototype.hasOwnProperty.call(show, k)) out[k] = !!show[k];
      return out;
    }
    // Default: every lane active.
    for (var j = 0; j < METHODS.length; j++) out[METHODS[j]] = true;
    return out;
  }

  function numberOr(v, fallback) {
    var n = Number(v);
    return isFinite(n) ? n : fallback;
  }

  function assign(target) {
    for (var i = 1; i < arguments.length; i++) {
      var src = arguments[i];
      if (!src) continue;
      for (var k in src) if (Object.prototype.hasOwnProperty.call(src, k)) target[k] = src[k];
    }
    return target;
  }

  // ---------------------------------------------------------------------
  // Formatting
  // ---------------------------------------------------------------------
  // Deterministic en-US thousands grouping. Intl/toLocaleString are banned:
  // their output is locale- and runtime-dependent, and these strings feed the
  // execution_hash, which must be reproducible everywhere.
  function fmtEnUS(n) {
    n = Number(n);
    if (isNaN(n)) return 'NaN';
    if (!isFinite(n)) return n > 0 ? '∞' : '-∞';
    var sign = (n < 0) ? '-' : '';
    var s = Math.abs(n).toString();
    if (s.indexOf('e') !== -1 || s.indexOf('E') !== -1) return sign + s;
    var split = s.split('.');
    var i = split[0], f = split[1] || '';
    if (f.length > 3) {
      var keep = f.slice(0, 3);
      var nd = f.charCodeAt(3) - 48;
      var d = (i + keep).split('').map(function (c) { return c.charCodeAt(0) - 48; });
      if (nd >= 5) {
        var j = d.length - 1;
        for (; j >= 0; j--) { if (d[j] === 9) { d[j] = 0; } else { d[j]++; break; } }
        if (j < 0) d.unshift(1);
      }
      var a = d.join('');
      i = a.slice(0, a.length - keep.length) || '0';
      f = a.slice(a.length - keep.length);
    }
    f = f.replace(/0+$/, '');
    i = i.replace(/^0+(?=\d)/, '');
    return sign + i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f ? '.' + f : '');
  }

  function fmtMass(M) {
    if (M === null || M === undefined || isNaN(M)) return '—';
    if (M >= 1e6) return (M / 1e6).toFixed(2) + '×10⁶';
    if (M >= 1e4) return (M / 1e3).toFixed(1) + '×10³';
    if (M >= 1000) return fmtEnUS(Math.round(M));
    return Math.round(M).toString();
  }

  function srcLabel(m) {
    return m ? (m.authors + ' ' + m.year) : null;
  }

  /** One-line human verdict. Names both sides when in tension. */
  function buildVerdictString(win) {
    if (win.tension) {
      var lo = win.lowSrc ? srcLabel(win.lowSrc) : 'lower bound';
      var hi = win.hiSrc ? srcLabel(win.hiSrc) : 'upper limit';
      return 'tension — ' + lo + ' (' + fmtMass(win.lo) + ' M☉) exceeds ' + hi + ' (' + fmtMass(win.hi) + ' M☉)';
    }
    if (win.lo !== null && win.hi !== null) return 'allowed window: ' + fmtMass(win.lo) + '–' + fmtMass(win.hi) + ' M☉';
    if (win.lo !== null) return 'lower bound only: > ' + fmtMass(win.lo) + ' M☉';
    if (win.hi !== null) return 'upper limit only: < ' + fmtMass(win.hi) + ' M☉';
    return 'no constraints active';
  }

  // ---------------------------------------------------------------------
  // ChainGraph output payload
  // ---------------------------------------------------------------------
  /**
   * Build the constraint_stacker output_payload from policy parameters.
   *
   * This is the payload that feeds the execution_hash, so it is byte-exact
   * by contract: the ocs-mcp-worker parity gate asserts this function and
   * kernels/constraint-stacker.kernel.mjs agree across the fixture corpus,
   * and the anchored golden (tools/data/anchored-evidence.json,
   * execution_hash 533362…) pins it against the published record.
   * Field order, rounding and wording are all load-bearing. Do not "tidy".
   *
   * @param {Object} policy_parameters  { input_parameters: { epsilon, rho, show } }
   * @param {Array}  constraints        constraint set
   */
  function computeStackerPayload(policy_parameters, constraints) {
    var pp = policy_parameters || {};
    var ip = pp.input_parameters || {};
    var eps = numberOr(ip.epsilon, 1e-3);
    var rho = numberOr(ip.rho, 1e-21);
    var show = normalizeShow(ip.show);

    var win = computeWindow(constraints, { show: show, epsilon: eps, rho: rho });
    var lanes = activeLanes(show);

    return {
      output_payload: {
        allowed_window_M_solar: {
          lower: win.lo !== null ? Math.round(win.lo) : null,
          upper: win.hi !== null ? Math.round(win.hi) : null
        },
        tension_detected: !!win.tension,
        tension_direction: win.tension ? 'lower_bound_exceeds_upper_limit' : null,
        n_constraints_active: activeConstraints(constraints, show).length,
        constraint_lanes_active: lanes,
        lower_bound_source: srcLabel(win.lowSrc),
        upper_limit_source: srcLabel(win.hiSrc),
        epsilon_adaf: eps,
        rho_inf_kg_m3: rho,
        verdict: buildVerdictString(win)
      }
    };
  }

  // ---------------------------------------------------------------------
  // Dataset adapter
  // ---------------------------------------------------------------------
  /**
   * Read the shipped compilation from a loaded measurements.js.
   * data/measurements.js stays untouched: it is a classic script assigning
   * window.OCS_MEASUREMENTS and ~104 pages depend on that exact shape, so
   * the library adapts to it rather than the reverse.
   *
   * @param {Object} [scope]  defaults to globalThis; Node tests pass the vm
   *                          sandbox they evaluated measurements.js in.
   */
  function constraintsFromMeasurements(scope) {
    var s = scope || (typeof globalThis !== 'undefined' ? globalThis : {});
    var data = s.OCS_MEASUREMENTS || (s.window && s.window.OCS_MEASUREMENTS);
    if (!data || !Array.isArray(data.imbh)) {
      throw new Error('constraintsFromMeasurements: OCS_MEASUREMENTS.imbh not found — is data/measurements.js loaded?');
    }
    return data.imbh;
  }

  return {
    VERSION: '1.0.0',
    SCHEMA_VERSION: '1.0',
    LIMIT_TYPES: LIMIT_TYPES,
    METHODS: METHODS,
    CONSTANTS: { G_SI: G_SI, C_SI: C_SI, MSUN_KG: MSUN_KG, OC_SIGMA_KMS: OC_SIGMA_KMS },
    JWST_DEFAULTS: JWST_DEFAULTS,
    validateConstraint: validateConstraint,
    validateConstraintSet: validateConstraintSet,
    jwstUpperLimitMsun: jwstUpperLimitMsun,
    mSigmaPrediction: mSigmaPrediction,
    computeWindow: computeWindow,
    activeConstraints: activeConstraints,
    activeLanes: activeLanes,
    normalizeShow: normalizeShow,
    fmtEnUS: fmtEnUS,
    fmtMass: fmtMass,
    buildVerdictString: buildVerdictString,
    computeStackerPayload: computeStackerPayload,
    constraintsFromMeasurements: constraintsFromMeasurements
  };
});
