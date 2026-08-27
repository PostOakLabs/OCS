"""
Paper F, WU OCS-R7-CALC-F-1, addendum: the like-for-like reconstruction test.

fF_calcF1_v1.py's Part C compares the paper's Gaussian-at-zero likelihood
against a survival ('censored') likelihood on all six legs.  That comparison
is informative but NOT like-for-like, and the difference matters enough to
separate here:

  * The RADIO leg is a MEASUREMENT.  Mahida et al. image the field and report
    a central flux density consistent with zero at 1.1 uJy rms.  "0 +/- sigma"
    is the datum, and a Gaussian on it is the correct likelihood, not a
    reconstruction of anything.  Replacing it with P(observed < 5 sigma)
    discards the measured value and must loosen the limit; that loosening is
    the value of the measurement, not a bias in the paper's convention.
  * The X-RAY and INFRARED legs are LIMITS.  Haggard et al. publish a 95 per
    cent aprates bound and Chen et al. publish per-filter completeness-based
    limits.  Neither publishes a central value.  These are the legs where the
    paper reconstructs a Gaussian from a published bound, and these are the
    legs where the referee's faithfulness question actually applies.

This script therefore runs the ladder:

  gauss_all      the paper's convention (published)
  surv_all       survival on all legs        (the naive comparison)
  hybrid         survival on the X-ray and IR legs, Gaussian on the measured
                 radio leg                   (the like-for-like test)
  surv_radio     survival on radio only, Gaussian elsewhere (isolates how
                 much of surv_all's motion is the discarded measurement)

Output: fF_calcF1_hybrid.json
Run:    python3 fF_calcF1_v1b.py
"""

import json
import os

import numpy as np
from scipy.special import log_ndtr

import fF_posterior_v3 as P
import fF_calcF1_v1 as C

HERE = os.path.dirname(os.path.abspath(__file__))


def log_like_mixed(eps, M, th, family, surv_xray=False, surv_ir=False,
                   surv_radio=False):
    """Per-leg choice of Gaussian-at-zero vs survival reconstruction.

    Both forms use the SAME sigma on each leg, so the only thing that changes
    is the shape of the term, which is exactly the referee's question.
    """
    ir_set = P.IR_SETS[P.IR_COMPLETENESS_PRIMARY]
    use_radio = P.FAMILIES[family][4]
    fX, LIR, S = C._pred(eps, M, th)

    if surv_xray:
        ll = log_ndtr((P.FX_LIM - fX) / P.SIG_FX)
    else:
        ll = -0.5 * (fX / P.SIG_FX) ** 2

    for f in ir_set:
        if surv_ir:
            ll = ll + log_ndtr((f["L_lim"] - LIR) / f["sigma"])
        else:
            ll = ll + -0.5 * (LIR / f["sigma"]) ** 2

    if use_radio:
        if surv_radio:
            ll = ll + log_ndtr((5.0 * P.SIG_S_RADIO - S) / P.SIG_S_RADIO)
        else:
            ll = ll + -0.5 * (S / P.SIG_S_RADIO) ** 2
    return ll


LADDER = {
    "gauss_all": dict(),
    "surv_all": dict(surv_xray=True, surv_ir=True, surv_radio=True),
    "hybrid_limits_only": dict(surv_xray=True, surv_ir=True),
    "surv_radio_only": dict(surv_radio=True),
    "surv_xray_only": dict(surv_xray=True),
    "surv_ir_only": dict(surv_ir=True),
}


def main():
    v3 = C.load_json("fF_v3_results.json")
    th = C.baseline_draws()
    C.assert_reproduction(th, v3)
    print("reproduction gate passed", flush=True)

    out = {"anchors_Msun": (P.ANCHORS / P.Msun).tolist(), "ladder": {}}
    base = None
    for tag, kw in LADDER.items():
        row = {}
        for fam in ("riaf", "jet", "disk"):
            row[fam] = C.eps95_from(log_like_mixed, P.ANCHORS, fam, th[fam],
                                    P.EPS_GRID, **kw)
        # radio-free column: riaf draws, disk (no-radio) likelihood
        row["riaf_noradio"] = C.eps95_from(log_like_mixed, P.ANCHORS, "disk",
                                           th["riaf"], P.EPS_GRID, **kw)
        row["P_excl"] = {f: P.excl_fraction(P.ANCHORS, row[f], th["riaf"])
                         for f in ("riaf", "jet", "riaf_noradio")}
        if tag == "gauss_all":
            base = row
            # gauss_all must reproduce the published anchors exactly
            for f in ("riaf", "jet", "disk"):
                for a, b in zip(row[f], v3["anchors_" + f]):
                    assert abs(a / b - 1.0) < 1e-9, (f, a, b)
            for a, b in zip(row["riaf_noradio"], v3["anchors_riaf_noradio"]):
                assert abs(a / b - 1.0) < 1e-9, (a, b)
            print("  gauss_all reproduces every published anchor", flush=True)
        row["ratio_to_gauss_all"] = {
            f: [a / b for a, b in zip(row[f], base[f])]
            for f in ("riaf", "jet", "disk", "riaf_noradio")}
        out["ladder"][tag] = row
        print("  %-20s riaf eps95 x %s | P_excl %s" % (
            tag,
            ["%.2f" % r for r in row["ratio_to_gauss_all"]["riaf"]],
            ["%.3f" % x for x in row["P_excl"]["riaf"]]), flush=True)

    out["note"] = (
        "The radio leg is a measured central flux density, not a published "
        "limit; a survival form there discards the measurement, so "
        "surv_all overstates the reconstruction question. "
        "hybrid_limits_only is the like-for-like test: it changes the "
        "reconstruction ONLY on the two legs the paper actually reconstructs "
        "from a published bound.")
    with open(os.path.join(HERE, "fF_calcF1_hybrid.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("written", flush=True)


if __name__ == "__main__":
    main()
