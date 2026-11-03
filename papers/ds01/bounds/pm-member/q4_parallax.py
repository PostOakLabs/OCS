"""Q4: DS-01's parallax against the single distance SSOT.

Row 5 of the DS-01 rigor campaign. Compares the zero-point corrected catalogue
parallax and the raw DR3 parallax with the cluster value carried as 0.182 mas
(5.49 kpc, oMEGACat VI), checks that value against the cluster members, and
reports the distance sensitivity named in the brief.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PLX_SSOT = 0.182
D_ALTS = [5.18, 5.43, 5.49]


def main():
    v = C.vb21()
    i = int(np.where(v["source_id"] == C.TARGET_ID)[0][0])
    memb = v["memberprob"] >= 0.9
    core = memb & (v["r_arcmin"] <= 10.0)

    # cluster parallax from members, two estimators
    w = 1.0 / v["plxe"][core] ** 2
    plx_w = float(np.sum(w * v["plx"][core]) / np.sum(w))
    plx_med = float(np.median(v["plx"][core]))
    # bootstrap on the weighted mean
    rng = np.random.default_rng(C.SEED)
    idx = np.where(core)[0]
    bs = np.empty(500)
    for k in range(500):
        p = rng.choice(idx, size=idx.size, replace=True)
        ww = 1.0 / v["plxe"][p] ** 2
        bs[k] = np.sum(ww * v["plx"][p]) / np.sum(ww)

    plx_ds = float(v["plx"][i])
    e_ds = float(v["plxe"][i])
    plx_raw = -0.04387
    e_raw = 0.31679

    def report(plx, err, label):
        off = plx - PLX_SSOT
        return {"basis": label, "parallax": plx, "error": err,
                "offset_mas": float(off), "offset_sigma": float(off / err),
                "zp_correction_applied": float(plx - plx_raw) if label != "raw" else 0.0,
                "upper_limit_1sigma_mas": float(plx + err),
                "distance_lower_limit_kpc_1sigma": (float(1.0 / (plx + err))
                                                    if plx + err > 0 else None)}

    rows = [report(plx_ds, e_ds, "catalogue_zp_corrected"),
            report(plx_raw, e_raw, "raw_dr3")]

    sens = []
    for d in D_ALTS:
        p = 1.0 / (d * 1000.0) * 1000.0  # mas
        sens.append({"distance_kpc": d, "parallax_mas": float(p),
                     "offset_vs_ds01_mas": float(plx_ds - p),
                     "offset_sigma": float((plx_ds - p) / e_ds),
                     "transverse_velocity_factor": float(D_ALTS[-1] / d),
                     "distance_squared_factor": float((d / D_ALTS[-1]) ** 2)})

    out = {
        "ssot": {"parallax_mas": PLX_SSOT, "distance_kpc": 1.0 / PLX_SSOT * 1000.0 / 1000.0,
                 "source": "oMEGACat VI, carried as 0.182 mas"},
        "cluster_members_inside_10arcmin": {
            "n": int(core.sum()),
            "plx_weighted_mean": plx_w,
            "plx_weighted_mean_bootstrap_sd": float(np.std(bs, ddof=1)),
            "plx_median": plx_med,
            "plx_p16": float(np.percentile(v["plx"][core], 16)),
            "plx_p84": float(np.percentile(v["plx"][core], 84)),
            "offset_vs_ssot_mas": float(plx_w - PLX_SSOT),
        },
        "rows": rows,
        "sensitivity": sens,
    }
    path = C.write_json("q4_parallax.json", out)
    print("wrote", path)
    for r in rows:
        print(f"{r['basis']:26s} plx={r['parallax']:+.4f}+-{r['error']:.4f} "
              f"off={r['offset_mas']:+.4f} ({r['offset_sigma']:+.2f} sigma)")
    print("cluster members:", round(plx_w, 4), "+-",
          round(float(np.std(bs, ddof=1)), 4), "n=", int(core.sum()))


if __name__ == "__main__":
    main()
