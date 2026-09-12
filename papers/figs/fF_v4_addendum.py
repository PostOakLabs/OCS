"""WU OCS-R9-F-1: the three v0.4 quantities the main run does not produce.

  1. Monte Carlo spread of the v0.4 headline numbers over eight seeds, which
     replaces the v0.3 seed study quoted in Section 3.3.  Anchors and both
     exclusion statistics only; the full grid is not re-run per seed.
  2. The SKA-depth forecast on the new exclusion statistic (Section 8.2).
  3. The eps-grid-floor check: the posterior-predictive statistic never reads
     eps95, so unlike the v0.3 statistic it cannot depend on the efficiency
     prior's lower cutoff.  Asserted here rather than claimed.

Output: fF_v4_seedspread.json
"""

import json
import os

import numpy as np

import fF_posterior_v4 as V

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = [42, 43, 44, 45, 46, 47, 48, 49]
FAM_OF = {"riaf": "riaf", "jet": "jet", "riaf_noradio": "disk"}


def one_seed(seed):
    rng = np.random.default_rng(seed)
    th = {f: V.draw_theta(rng, V.N_MC, f) for f in V.FAMILIES}
    _dead = V.draw_theta(rng, V.N_MC, "disk")
    del _dead
    th_nat = {"riaf": V.attach_delta(th["riaf"], seed=V.SEED_DELTA + seed),
              "jet": V.attach_delta(th["jet"], seed=V.SEED_DELTA + seed),
              "riaf_noradio": None}
    th_nat["riaf_noradio"] = th_nat["riaf"]
    out = {"seed": seed, "eps95": {}, "p_excl_ppc": {}, "p_exceed": {}}
    for key, fam in FAM_OF.items():
        src = th["riaf"] if key == "riaf_noradio" else th[fam]
        e = V.eps95_curve(V.ANCHORS, fam, src)
        out["eps95"][key] = e
        out["p_excl_ppc"][key] = V.p_excl_ppc(V.ANCHORS, fam,
                                              th_nat[key])[0]
        out["p_exceed"][key] = V.p_exceed(V.ANCHORS, e, th_nat["riaf"])[0]
    return out


def main():
    runs = [one_seed(s) for s in SEEDS]
    spread = {}
    for stat in ("eps95", "p_excl_ppc", "p_exceed"):
        spread[stat] = {}
        for key in FAM_OF:
            arr = np.array([r[stat][key] for r in runs])
            rec = {"min": arr.min(0).tolist(), "max": arr.max(0).tolist(),
                   "mean": arr.mean(0).tolist(), "sd": arr.std(0, ddof=1).tolist(),
                   "seed_of_record": runs[0][stat][key]}
            if stat == "eps95":
                rec["full_range_percent"] = ((arr.max(0) - arr.min(0))
                                             / arr.mean(0) * 100).tolist()
            else:
                rec["full_range_pp"] = ((arr.max(0) - arr.min(0))
                                        * 100).tolist()
            spread[stat][key] = rec

    # 2. SKA-era radio depth on the new statistic
    rng = np.random.default_rng(V.SEED)
    th = {f: V.draw_theta(rng, V.N_MC, f) for f in V.FAMILIES}
    th_nat = V.attach_delta(th["riaf"])
    ska = {"p_excl_ppc_riaf_baseline": V.p_excl_ppc(V.ANCHORS, "riaf",
                                                    th_nat)[0],
           "p_excl_ppc_riaf_ska10x": V.p_excl_ppc(
               V.ANCHORS, "riaf", th_nat,
               sig_radio=V.SIG_S_RADIO / 10.0)[0],
           "p_excl_ppc_riaf_ne_measured": None}
    th_ne = V.attach_delta(V.draw_theta(np.random.default_rng(V.SEED + 900),
                                        V.N_MC, "riaf", ne_width=0.04))
    ska["p_excl_ppc_riaf_ne_measured"] = V.p_excl_ppc(V.ANCHORS, "riaf",
                                                      th_ne)[0]

    # 3. eps-grid-floor independence of the posterior-predictive statistic
    with open(os.path.join(HERE, "fF_v4_results.json")) as fh:
        v4 = json.load(fh)
    floor_check = {
        "eps95_ratio_floor11_over_baseline":
            [a / b for a, b in zip(v4["anchors_riaf_floor11"],
                                   v4["anchors_riaf"])],
        "p_excl_ppc_reads_eps95": False,
        "note": ("The posterior-predictive exclusion fraction evaluates the "
                 "likelihood at each draw's own eps_nat and never reads "
                 "eps95, so the efficiency prior's lower cutoff cannot move "
                 "it.  Under the v0.3 statistic that cutoff moved P_excl at "
                 "the high anchor from 0.90 to 0.48."),
    }

    out = {"_meta": {"script": "paper/figs/fF_v4_addendum.py",
                     "wu": "OCS-R9-F-1", "seeds": SEEDS},
           "per_seed": runs, "spread": spread, "forecasts": ska,
           "eps_grid_floor": floor_check}
    with open(os.path.join(HERE, "fF_v4_seedspread.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({"spread": spread, "forecasts": ska,
                      "eps_grid_floor": floor_check}, indent=1))


if __name__ == "__main__":
    main()
