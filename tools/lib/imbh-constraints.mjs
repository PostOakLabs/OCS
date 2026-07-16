/*
  imbh-constraints — ES module facade
  The Omega Centauri Society — omegacentauri.me
  Code: MIT License. Library version: 1.0.0

  The importable surface of the library. All logic lives in
  ./imbh-constraints.core.js — this file only re-exports it under named
  bindings. There is exactly one authored copy of the math.

  The split exists because the two consumers have incompatible loading
  rules, not because the code differs:

    - Browser pages must run from file:// (site architecture rule 3).
      ES module scripts are fetched under CORS and file:// pages have an
      opaque origin, so `<script type="module">` cannot import anything
      there. Pages therefore load the core with a plain
      `<script src="lib/imbh-constraints.core.js">` and read the global,
      exactly as they already do for data/measurements.js.

    - Node (tests, the ocs-mcp-worker parity gate, and any downstream
      reuse) wants real named imports:

        import { computeWindow, validateConstraintSet } from './lib/imbh-constraints.mjs';

  Importing the core for side effects populates globalThis.IMBHConstraints;
  everything below is a binding onto that one object.

  No build step, no dependencies, works in Node 18+, Cloudflare Workers and
  any browser.
*/

import './imbh-constraints.core.js';

const lib = globalThis.IMBHConstraints;

if (!lib) {
  throw new Error(
    'imbh-constraints: core failed to register globalThis.IMBHConstraints. ' +
    'Expected ./imbh-constraints.core.js to load as a classic script.'
  );
}

export const VERSION = lib.VERSION;
export const SCHEMA_VERSION = lib.SCHEMA_VERSION;
export const LIMIT_TYPES = lib.LIMIT_TYPES;
export const METHODS = lib.METHODS;
export const CONSTANTS = lib.CONSTANTS;
export const JWST_DEFAULTS = lib.JWST_DEFAULTS;

export const validateConstraint = lib.validateConstraint;
export const validateConstraintSet = lib.validateConstraintSet;
export const jwstUpperLimitMsun = lib.jwstUpperLimitMsun;
export const mSigmaPrediction = lib.mSigmaPrediction;
export const computeWindow = lib.computeWindow;
export const activeConstraints = lib.activeConstraints;
export const activeLanes = lib.activeLanes;
export const normalizeShow = lib.normalizeShow;
export const fmtEnUS = lib.fmtEnUS;
export const fmtMass = lib.fmtMass;
export const buildVerdictString = lib.buildVerdictString;
export const computeStackerPayload = lib.computeStackerPayload;
export const constraintsFromMeasurements = lib.constraintsFromMeasurements;

export default lib;
