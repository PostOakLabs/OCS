// lib-imbh-constraints.test.mjs — coverage for tools/lib/imbh-constraints.
//
// The library is the extracted core of constraint-stacker / the evidence
// dashboard / the ocs-mcp-worker kernel, so these tests carry two burdens:
//
//   1. the physics and schema logic are correct on their own terms, and
//   2. the extraction did not move a single byte of published output —
//      the anchored golden (tools/data/anchored-evidence.json,
//      execution_hash 533362…, RFC3161 + OTS anchored) is replayed here as
//      a fixture. If this file goes red, the published record and the code
//      disagree; that is never a "just update the fixture" situation.
//
// Run: node --test scripts/tests/lib-imbh-constraints.test.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  VERSION,
  LIMIT_TYPES,
  METHODS,
  JWST_DEFAULTS,
  CONSTANTS,
  validateConstraint,
  validateConstraintSet,
  jwstUpperLimitMsun,
  mSigmaPrediction,
  computeWindow,
  activeConstraints,
  activeLanes,
  normalizeShow,
  fmtEnUS,
  fmtMass,
  buildVerdictString,
  computeStackerPayload,
  constraintsFromMeasurements,
} from '../../tools/lib/imbh-constraints.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');

// measurements.js is a classic browser script; evaluate it the way the
// existing tier-c tests and the worker's measurements-sync gate do.
function loadMeasurements() {
  const src = readFileSync(resolve(REPO, 'tools/data/measurements.js'), 'utf8');
  const sandbox = { window: {}, console };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: 'measurements.js', timeout: 5000 });
  return sandbox.window;
}

const measurements = loadMeasurements();
const SHIPPED = constraintsFromMeasurements(measurements);

// Minimal hand-built sets, so window tests do not silently change meaning
// when a new paper is added to the shipped compilation.
const C = {
  lower8200:  { id: 'lo', year: 2024, authors: 'Lower Author', limitType: 'lower',  method: 'propermotion', value: 8200 },
  upper6000:  { id: 'hi', year: 2025, authors: 'Upper Author', limitType: 'upper',  method: 'timing',       value: 6000 },
  upper12000: { id: 'hi2', year: 2010, authors: 'Other Author', limitType: 'upper', method: 'kinematics',   value: 12000 },
  detection:  { id: 'det', year: 2008, authors: 'Det Author',  limitType: 'detection', method: 'kinematics', value: 4e4 },
  noEvidence: { id: 'nil', year: 2017, authors: 'Nil Author',  limitType: 'noEvidence', method: 'nbody',    value: null },
  jwst:       { id: 'jw',  year: 2025, authors: 'JWST Author', limitType: 'parameterDependent', method: 'accretion', value: null },
};

// ---------------------------------------------------------------------------
test('module surface', async (t) => {
  await t.test('exports a version and the schema vocabularies', () => {
    assert.equal(VERSION, '1.0.0');
    assert.deepEqual(LIMIT_TYPES, ['detection', 'upper', 'lower', 'noEvidence', 'parameterDependent']);
    assert.deepEqual(METHODS, ['kinematics', 'propermotion', 'timing', 'accretion', 'nbody']);
  });

  await t.test('physical constants match the values the pages and kernel use', () => {
    assert.equal(CONSTANTS.G_SI, 6.674e-11);
    assert.equal(CONSTANTS.C_SI, 2.998e8);
    assert.equal(CONSTANTS.MSUN_KG, 1.989e30);
  });
});

// ---------------------------------------------------------------------------
test('schema validation', async (t) => {
  await t.test('accepts the shipped compilation', () => {
    const { valid, errors } = validateConstraintSet(SHIPPED);
    assert.equal(valid, true, 'shipped measurements.js imbh[] must satisfy the schema:\n' + errors.join('\n'));
  });

  await t.test('rejects an unknown limitType', () => {
    const errs = validateConstraint({ ...C.lower8200, limitType: 'probably' });
    assert.equal(errs.length, 1);
    assert.match(errs[0], /limitType/);
  });

  await t.test('rejects an unknown method', () => {
    const errs = validateConstraint({ ...C.lower8200, method: 'astrology' });
    assert.match(errs.join(), /method/);
  });

  await t.test('rejects a bounding constraint with no number', () => {
    for (const limitType of ['upper', 'lower']) {
      const errs = validateConstraint({ ...C.lower8200, limitType, value: null });
      assert.match(errs.join(), /requires a numeric/, `${limitType} with null value must be rejected`);
    }
  });

  await t.test('rejects noEvidence carrying a number — it is not a numeric limit', () => {
    const errs = validateConstraint({ ...C.noEvidence, value: 5000 });
    assert.match(errs.join(), /noEvidence/);
  });

  await t.test('rejects non-finite, non-positive, and non-object input', () => {
    assert.match(validateConstraint({ ...C.lower8200, value: NaN }).join(), /finite/);
    assert.match(validateConstraint({ ...C.lower8200, value: Infinity }).join(), /finite/);
    assert.match(validateConstraint({ ...C.lower8200, value: -100 }).join(), /positive/);
    assert.match(validateConstraint(null).join(), /not an object/);
    assert.match(validateConstraint({ ...C.lower8200, id: '' }).join(), /`id`/);
  });

  await t.test('flags duplicate ids', () => {
    const { valid, errors } = validateConstraintSet([C.lower8200, { ...C.upper6000, id: 'lo' }]);
    assert.equal(valid, false);
    assert.match(errors.join(), /duplicate id/);
  });

  await t.test('a non-array set fails instead of throwing', () => {
    const { valid, errors } = validateConstraintSet('nope');
    assert.equal(valid, false);
    assert.match(errors.join(), /expected an array/);
  });

  await t.test('validation is pure — never throws on hostile input', () => {
    for (const bad of [undefined, 42, [], {}, { id: 1 }, Symbol.iterator]) {
      assert.doesNotThrow(() => validateConstraint(bad));
    }
  });
});

// ---------------------------------------------------------------------------
test('JWST parameter-dependent limit', async (t) => {
  // M = sqrt( L_limit · c_s³ / (ε · 4π G² ρ∞ · c²) ) / M_sun, closed form
  // recomputed here independently of the library's own expression.
  const closedForm = (eps, rho) => {
    const num = 1e28 * Math.pow(1.0e4, 3);
    const den = eps * 4 * Math.PI * (6.674e-11 ** 2) * rho * (2.998e8 ** 2);
    return Math.sqrt(num / den) / 1.989e30;
  };

  await t.test('matches the closed form across the slider range', () => {
    for (const eps of [1e-4, 1e-3, 1e-2, 0.1]) {
      for (const rho of [1e-23, 1e-21, 1e-19]) {
        const got = jwstUpperLimitMsun(eps, rho);
        const want = closedForm(eps, rho);
        assert.ok(Math.abs(got - want) / want < 1e-12, `ε=${eps} ρ=${rho}: got ${got}, want ${want}`);
      }
    }
  });

  await t.test('reproduces the anchored golden default (709 M☉ at ε=1e-3, ρ=1e-21)', () => {
    assert.equal(Math.round(jwstUpperLimitMsun(1e-3, 1e-21)), 709);
  });

  await t.test('scales as ε^-1/2 and ρ^-1/2', () => {
    const base = jwstUpperLimitMsun(1e-3, 1e-21);
    assert.ok(Math.abs(jwstUpperLimitMsun(4e-3, 1e-21) - base / 2) / base < 1e-12);
    assert.ok(Math.abs(jwstUpperLimitMsun(1e-3, 4e-21) - base / 2) / base < 1e-12);
  });

  await t.test('c_s³ uses integer multiplication, not Math.pow (guest-legal parity)', () => {
    // The worker kernel bans Math.pow. Same number either way, asserted so a
    // future "simplification" to Math.pow cannot drift the two copies.
    assert.equal(JWST_DEFAULTS.c_s ** 3, JWST_DEFAULTS.c_s * JWST_DEFAULTS.c_s * JWST_DEFAULTS.c_s);
  });

  await t.test('degenerate inputs yield null, never NaN or Infinity', () => {
    for (const [eps, rho] of [[0, 1e-21], [1e-3, 0], [NaN, 1e-21], [1e-3, NaN], [Infinity, 1e-21]]) {
      const v = jwstUpperLimitMsun(eps, rho);
      assert.ok(v === null || Number.isFinite(v), `ε=${eps} ρ=${rho} produced ${v}`);
    }
    assert.equal(jwstUpperLimitMsun(0, 1e-21), null);
    assert.equal(jwstUpperLimitMsun(1e-3, 0), null);
  });

  await t.test('honours an opts override', () => {
    const tighter = jwstUpperLimitMsun(1e-3, 1e-21, { L_limit: 1e27, c_s: 1.0e4 });
    assert.ok(tighter < jwstUpperLimitMsun(1e-3, 1e-21), 'a fainter luminosity limit must tighten the mass limit');
  });
});

// ---------------------------------------------------------------------------
test('M–sigma prediction', async (t) => {
  await t.test('matches Gültekin 2009 at the calibration pivot', () => {
    // At σ = 200 km/s the relation returns 10^8.12 by construction.
    assert.ok(Math.abs(mSigmaPrediction(200) - Math.pow(10, 8.12)) / Math.pow(10, 8.12) < 1e-12);
  });

  await t.test('OC default sigma gives the ~10^3 M☉ context value', () => {
    const m = mSigmaPrediction();
    assert.ok(m > 1e3 && m < 1e4, `expected ~10³–10⁴ M☉ for σ=20 km/s, got ${m}`);
  });

  await t.test('is monotonic in sigma', () => {
    assert.ok(mSigmaPrediction(10) < mSigmaPrediction(20));
    assert.ok(mSigmaPrediction(20) < mSigmaPrediction(40));
  });
});

// ---------------------------------------------------------------------------
test('window aggregation', async (t) => {
  await t.test('an open window reports both bounds and no tension', () => {
    const w = computeWindow([C.lower8200, C.upper12000], { show: 'propermotion,kinematics' });
    assert.equal(w.lo, 8200);
    assert.equal(w.hi, 12000);
    assert.equal(w.tension, false);
    assert.equal(w.lowSrc.id, 'lo');
    assert.equal(w.hiSrc.id, 'hi2');
  });

  await t.test('the tightest bound on each side wins', () => {
    const w = computeWindow([C.lower8200, C.upper6000, C.upper12000], { show: 'propermotion,timing,kinematics' });
    assert.equal(w.hi, 6000, 'the tightest upper limit must bound the window');
    assert.equal(w.hiSrc.id, 'hi');
  });

  await t.test('detections do not bound the window in either direction', () => {
    // A 4e4 detection sits far above the 12000 upper limit. If detections
    // bounded, this window would move or go into tension.
    const w = computeWindow([C.detection, C.upper12000], { show: 'kinematics' });
    assert.equal(w.lo, null);
    assert.equal(w.hi, 12000);
    assert.equal(w.tension, false);
  });

  await t.test('noEvidence bounds nothing — it is not an upper limit', () => {
    const w = computeWindow([C.noEvidence], { show: 'nbody' });
    assert.deepEqual([w.lo, w.hi, w.tension], [null, null, false]);
  });

  await t.test('unbounded sides are null, never ±Infinity', () => {
    const w = computeWindow([], { show: 'kinematics' });
    assert.equal(w.lo, null);
    assert.equal(w.hi, null);
    assert.equal(w.tension, false);
  });

  await t.test('hidden lanes drop out of the window', () => {
    const w = computeWindow([C.lower8200, C.upper6000], { show: 'propermotion' });
    assert.equal(w.lo, 8200);
    assert.equal(w.hi, null, 'the timing lane is hidden, so its upper limit must not bound');
    assert.equal(w.tension, false);
  });

  await t.test('the parameter-dependent lane realizes its curve from epsilon/rho', () => {
    const loose = computeWindow([C.jwst], { show: 'accretion', epsilon: 1e-3, rho: 1e-21 });
    const tight = computeWindow([C.jwst], { show: 'accretion', epsilon: 1e-1, rho: 1e-21 });
    assert.equal(Math.round(loose.hi), 709);
    assert.ok(tight.hi < loose.hi, 'a higher radiative efficiency must tighten the limit');
    assert.equal(loose.hiSrc.id, 'jw');
    assert.equal(loose.hiSrc.value, loose.hi, 'hiSrc must carry the realized value, not the null placeholder');
  });

  await t.test('realizing the curve does not mutate the input constraint', () => {
    const input = { ...C.jwst };
    computeWindow([input], { show: 'accretion', epsilon: 1e-3, rho: 1e-21 });
    assert.equal(input.value, null, 'the caller-owned constraint object must be left untouched');
  });

  await t.test('show accepts a string, an object, or nothing', () => {
    const set = [C.lower8200, C.upper6000];
    const viaString = computeWindow(set, { show: 'propermotion,timing' });
    const viaObject = computeWindow(set, { show: { propermotion: true, timing: true } });
    const viaDefault = computeWindow(set, {});
    assert.deepEqual([viaString.lo, viaString.hi], [8200, 6000]);
    assert.deepEqual([viaObject.lo, viaObject.hi], [8200, 6000]);
    assert.deepEqual([viaDefault.lo, viaDefault.hi], [8200, 6000], 'omitting show must mean all lanes active');
  });

  await t.test('normalizeShow turns a falsy object entry off', () => {
    assert.deepEqual(normalizeShow({ timing: false, nbody: true }), { timing: false, nbody: true });
  });

  await t.test('survives a malformed constraint set without throwing', () => {
    assert.doesNotThrow(() => computeWindow([null, undefined, {}, C.lower8200], { show: 'propermotion' }));
    const w = computeWindow([null, C.lower8200], { show: 'propermotion' });
    assert.equal(w.lo, 8200);
  });
});

// ---------------------------------------------------------------------------
// The doctrine tests. These encode a scientific-integrity rule, not a
// preference: OCS never collapses a tension record into a single number.
test('tension records are preserved, never collapsed', async (t) => {
  await t.test('an unsatisfiable window is flagged, not silently emptied', () => {
    const w = computeWindow([C.lower8200, C.upper6000], { show: 'propermotion,timing' });
    assert.equal(w.tension, true, 'lo 8200 > hi 6000 must register as tension');
    assert.equal(w.lo, 8200, 'the lower bound must survive');
    assert.equal(w.hi, 6000, 'the upper limit must survive');
  });

  await t.test('both sources survive so the reader can attribute the conflict', () => {
    const w = computeWindow([C.lower8200, C.upper6000], { show: 'propermotion,timing' });
    assert.equal(w.lowSrc.id, 'lo');
    assert.equal(w.hiSrc.id, 'hi');
  });

  await t.test('no reconciled midpoint is ever produced', () => {
    const w = computeWindow([C.lower8200, C.upper6000], { show: 'propermotion,timing' });
    // 7100 is the arithmetic midpoint an averaging implementation would emit.
    assert.ok(!Object.values(w).includes(7100), 'the library must not average conflicting bounds');
    assert.equal(w.lo > w.hi, true, 'the inversion itself must remain visible to the caller');
  });

  await t.test('the real Häberle/Bañares conflict is live in the shipped data', () => {
    const w = computeWindow(SHIPPED, { show: 'propermotion,timing' });
    assert.equal(w.tension, true);
    assert.equal(w.lowSrc.id, 'haberle2024');
    assert.match(w.hiSrc.id, /banares2025|trapum2026/);
    assert.equal(w.lo, 8200, 'Häberle 2024 lower bound');
    assert.equal(w.hi, 6000, 'Bañares 2025 is the tighter upper limit of the two timing constraints');
  });

  await t.test('the verdict string names both sides of a tension', () => {
    const w = computeWindow([C.lower8200, C.upper6000], { show: 'propermotion,timing' });
    const v = buildVerdictString(w);
    assert.match(v, /^tension —/);
    assert.match(v, /Lower Author 2024/);
    assert.match(v, /Upper Author 2025/);
  });
});

// ---------------------------------------------------------------------------
test('lane helpers', async (t) => {
  await t.test('activeLanes returns canonical METHODS order regardless of input order', () => {
    assert.deepEqual(activeLanes('nbody,kinematics,timing'), ['kinematics', 'timing', 'nbody']);
  });

  await t.test('activeConstraints counts only constraints in visible lanes', () => {
    assert.equal(activeConstraints([C.lower8200, C.upper6000, C.noEvidence], 'propermotion').length, 1);
    assert.equal(activeConstraints(SHIPPED, 'kinematics,propermotion,timing,accretion,nbody').length, SHIPPED.length);
  });
});

// ---------------------------------------------------------------------------
test('formatting is deterministic and locale-independent', async (t) => {
  await t.test('fmtEnUS groups thousands without Intl', () => {
    assert.equal(fmtEnUS(8200), '8,200');
    assert.equal(fmtEnUS(1000000), '1,000,000');
    assert.equal(fmtEnUS(999), '999');
    assert.equal(fmtEnUS(-8200), '-8,200');
    assert.equal(fmtEnUS(0), '0');
  });

  await t.test('fmtEnUS handles non-numbers the way the hashed payload expects', () => {
    assert.equal(fmtEnUS(NaN), 'NaN');
    assert.equal(fmtEnUS(Infinity), '∞');
    assert.equal(fmtEnUS(-Infinity), '-∞');
  });

  await t.test('fmtMass switches notation at the documented thresholds', () => {
    assert.equal(fmtMass(709), '709');
    assert.equal(fmtMass(8200), '8,200');
    assert.equal(fmtMass(4e4), '40.0×10³');
    assert.equal(fmtMass(4e6), '4.00×10⁶');
    assert.equal(fmtMass(null), '—');
    assert.equal(fmtMass(NaN), '—');
  });

  await t.test('verdict covers every one-sided and empty case', () => {
    assert.match(buildVerdictString({ tension: false, lo: 8200, hi: 12000 }), /^allowed window: 8,200–12\.0×10³ M☉$/);
    assert.match(buildVerdictString({ tension: false, lo: 8200, hi: null }), /^lower bound only: > 8,200 M☉$/);
    assert.match(buildVerdictString({ tension: false, lo: null, hi: 6000 }), /^upper limit only: < 6,000 M☉$/);
    assert.equal(buildVerdictString({ tension: false, lo: null, hi: null }), 'no constraints active');
  });
});

// ---------------------------------------------------------------------------
test('dataset adapter', async (t) => {
  await t.test('reads OCS_MEASUREMENTS.imbh from an injected scope', () => {
    assert.ok(Array.isArray(SHIPPED));
    assert.ok(SHIPPED.length >= 9, `expected the full compilation, got ${SHIPPED.length}`);
    assert.ok(SHIPPED.some((m) => m.id === 'haberle2024'));
    assert.ok(SHIPPED.some((m) => m.id === 'trapum2026'), 'TRAPUM 2026 must be present');
  });

  await t.test('accepts a bare scope as well as a window-shaped one', () => {
    assert.doesNotThrow(() => constraintsFromMeasurements({ OCS_MEASUREMENTS: { imbh: [] } }));
  });

  await t.test('fails loudly when measurements.js is not loaded', () => {
    assert.throws(() => constraintsFromMeasurements({}), /measurements\.js/);
  });

  await t.test('measurements.js is not mutated by the library', () => {
    const before = JSON.stringify(SHIPPED);
    computeWindow(SHIPPED, { show: 'kinematics,propermotion,timing,accretion,nbody', epsilon: 1e-2, rho: 1e-20 });
    assert.equal(JSON.stringify(SHIPPED), before);
  });
});

// ---------------------------------------------------------------------------
// Regression against the published record.
test('anchored golden — the published artifact must still reproduce', async (t) => {
  const golden = JSON.parse(readFileSync(resolve(REPO, 'tools/data/anchored-evidence.json'), 'utf8'));

  await t.test('replays tools/data/anchored-evidence.json byte-for-byte', () => {
    const { output_payload } = computeStackerPayload(golden.policy_parameters, SHIPPED);
    assert.deepEqual(
      output_payload,
      golden.output_payload,
      'The library no longer reproduces the RFC3161 + OTS anchored artifact ' +
      '(execution_hash ' + golden.execution_hash.slice(0, 12) + '…). ' +
      'This is a published, timestamped record — do not update the fixture to match the code.'
    );
  });

  await t.test('replays the constraint-stacker ChainGraph artifact fixture', () => {
    const fixture = JSON.parse(readFileSync(resolve(REPO, 'scripts/fixtures/constraint-stacker.artifact.json'), 'utf8'));
    const { output_payload } = computeStackerPayload(fixture.policy_parameters, SHIPPED);
    assert.deepEqual(output_payload, fixture.output_payload);
  });

  await t.test('the golden encodes the tension, and it is still there', () => {
    assert.equal(golden.output_payload.tension_detected, true);
    const { output_payload } = computeStackerPayload(golden.policy_parameters, SHIPPED);
    assert.equal(output_payload.tension_detected, true);
    assert.equal(output_payload.tension_direction, 'lower_bound_exceeds_upper_limit');
  });
});

// ---------------------------------------------------------------------------
test('stacker payload contract', async (t) => {
  const pp = (ip) => ({ execution_backend: 'js', input_parameters: ip });

  await t.test('field set is exactly what the hashed payload declares', () => {
    const { output_payload } = computeStackerPayload(pp({ epsilon: 1e-3, rho: 1e-21, show: 'timing' }), SHIPPED);
    assert.deepEqual(Object.keys(output_payload), [
      'allowed_window_M_solar',
      'tension_detected',
      'tension_direction',
      'n_constraints_active',
      'constraint_lanes_active',
      'lower_bound_source',
      'upper_limit_source',
      'epsilon_adaf',
      'rho_inf_kg_m3',
      'verdict',
    ]);
  });

  await t.test('masses are rounded to integers in the payload', () => {
    const { output_payload } = computeStackerPayload(pp({ epsilon: 1e-3, rho: 1e-21, show: 'accretion' }), SHIPPED);
    assert.equal(output_payload.allowed_window_M_solar.upper, 709);
    assert.equal(Number.isInteger(output_payload.allowed_window_M_solar.upper), true);
  });

  await t.test('missing inputs fall back to the documented defaults', () => {
    const { output_payload } = computeStackerPayload({}, SHIPPED);
    assert.equal(output_payload.epsilon_adaf, 1e-3);
    assert.equal(output_payload.rho_inf_kg_m3, 1e-21);
  });

  await t.test('unparseable inputs fall back rather than emitting NaN', () => {
    const { output_payload } = computeStackerPayload(pp({ epsilon: 'abc', rho: undefined, show: 'accretion' }), SHIPPED);
    assert.equal(output_payload.epsilon_adaf, 1e-3);
    assert.equal(output_payload.rho_inf_kg_m3, 1e-21);
    assert.ok(Number.isFinite(output_payload.epsilon_adaf));
  });

  await t.test('null coerces to 0 rather than the default — kernel-parity behaviour', () => {
    // Number(null) === 0, which is finite, so it passes the fallback guard and
    // is taken as a literal zero density. Verified identical in
    // ocs-mcp-worker kernels/constraint-stacker.kernel.mjs, which is
    // §18 groth16-proven and whose output is bound by the anchored golden.
    // The library reproduces this exactly on purpose: parity with the proven
    // kernel is the contract, so this behaviour cannot be "fixed" on one side
    // alone. A zero density yields no limit at all, which computeWindow
    // reports as an unbounded upper side (null) rather than NaN — so the
    // result stays honest even though the input was junk.
    const { output_payload } = computeStackerPayload(pp({ epsilon: 1e-3, rho: null, show: 'accretion' }), SHIPPED);
    assert.equal(output_payload.rho_inf_kg_m3, 0);
    assert.equal(output_payload.allowed_window_M_solar.upper, null);
    assert.equal(output_payload.verdict, 'no constraints active');
  });

  await t.test('no lanes active means an empty, honest payload', () => {
    const { output_payload } = computeStackerPayload(pp({ epsilon: 1e-3, rho: 1e-21, show: '' }), SHIPPED);
    assert.equal(output_payload.n_constraints_active, 0);
    assert.deepEqual(output_payload.constraint_lanes_active, []);
    assert.equal(output_payload.verdict, 'no constraints active');
    assert.equal(output_payload.tension_detected, false);
    assert.equal(output_payload.tension_direction, null);
  });

  await t.test('payload is I-JSON clean, so it can be canonicalized and hashed', () => {
    const { output_payload } = computeStackerPayload(pp({ epsilon: 1e-3, rho: 1e-21, show: 'accretion,propermotion' }), SHIPPED);
    const walk = (v) => {
      if (typeof v === 'number') {
        assert.ok(Number.isFinite(v), `non-finite number ${v} would break RFC 8785 canonicalization`);
      } else if (Array.isArray(v)) v.forEach(walk);
      else if (v && typeof v === 'object') Object.values(v).forEach(walk);
    };
    walk(output_payload);
  });

  await t.test('the payload is deterministic across repeated calls', () => {
    const args = pp({ epsilon: 1e-3, rho: 1e-21, show: 'kinematics,propermotion,timing,accretion,nbody' });
    const a = computeStackerPayload(args, SHIPPED).output_payload;
    const b = computeStackerPayload(args, SHIPPED).output_payload;
    assert.deepEqual(a, b);
  });
});
