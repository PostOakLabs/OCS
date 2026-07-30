"""Fig 1: survival time of swarm structures vs orbital radius (flyby Monte Carlo).

Semi-analytic Monte Carlo (Appendix A of the paper):
per radius bin, encounter statistics (impact parameter with gravitational focusing,
speed drawn as a Rayleigh of scale sigma shifted upward by 0.3 sigma, mass function)
are sampled directly; per history, the diffusion channel (random-walk eccentricity
growth to orbit-crossing, e ~ 0.5) uses the sampled kick-variance with CLT scatter.
Lifetime capped at 12 Gyr.

Referee-M1 update (2026-07-23): the perturber mass function carries a
mass-segregated heavy-remnant extension (1.4 Msun NSs at 2 per cent number
fraction; BHs at 0.1 / 1 / 3 per cent).  The MC is run for the stars-only
baseline and all three BH fractions; the figure shows the baseline and the
fiducial (1 per cent) case with the bracketing fractions as thin lines.

Referee-5 update (2026-07-30), three changes:
  * the radius grid now starts at the Schwarzschild ISCO (6 r_g) rather than at
    5 r_g, where circular orbits do not exist and v_orb = 0.44 c;
  * the perturber BH mass is 31 Msun (Gonzalez Prieto et al. 2025) not 10 Msun;
  * an adiabatically-corrected curve is produced alongside the impulsive one.
    The impulsive curves remain the quoted conservative floor; the corrected
    curve is the physical estimate and shows that unbound cluster stars are
    decoupled from every orbit in the envelope.
Each configuration is now independently seeded, so results do not depend on the
order in which configurations are run.

Outputs fig1_envelope.pdf + fig1_results.json (numbers quoted in the text).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import (GM, RG, AU, YR, MSUN, V_REL, SIGMA, N_STAR, M_BH, R_INFL,
                    MF_MASSES, MF_WEIGHTS, remnant_mf, F_BH_GRID, F_BH_FID,
                    M_BH_PERT, M_BH_PERT_OLD, adiabatic_factor, v_orb, STYLE,
                    GAMMA_STAR, GAMMA_NS, GAMMA_BH, M_DARK_FID, M_DARK_LO, M_DARK_HI,
                    M_BH_PERT_LO, N_STAR_CLUSTER, SEG_ENHANCE, P_KOZAI_INCL,
                    f_bh_global, f_bh_central, species_table, N_enclosed,
                    sigma_loc, P_orb, F_NS)

SEED = 20260717
plt.rcParams.update(STYLE)

N_ENC_SAMPLE = 200_000     # encounter draws per radius bin (statistics)
N_HIST = 20_000            # histories per radius bin
E_CROSS = 0.5              # eccentricity threshold for swarm orbit-crossing
T_CAP = 1.2e10 * YR
B_MAX_FACTOR = 30.0        # kicks beyond 30a contribute <1e-3 of variance

A_MIN = 6.0 * RG           # Schwarzschild ISCO: no circular orbits inside
a_grid = np.logspace(np.log10(A_MIN / AU), np.log10(4e3), 40) * AU

def sample_encounters(rng, a, n, masses, weights):
    """Draw (b, m, v) for n encounters within b_max = 30a, focused distribution."""
    b_max = B_MAX_FACTOR * a
    # speed: Rayleigh of scale sigma (mean 1.2533 sigma) shifted up by 0.3 sigma
    v = rng.rayleigh(scale=SIGMA, size=n) + 0.3 * SIGMA
    # cumulative rate within b: Q(b) = v^2 b^2 + 2GM b  (up to constants)
    u = rng.random(n)
    v2 = v ** 2
    Qmax = v2 * b_max**2 + 2 * GM * b_max
    # invert quadratic v2 b^2 + 2GM b - u Qmax = 0
    b = (-2 * GM + np.sqrt(4 * GM**2 + 4 * v2 * u * Qmax)) / (2 * v2)
    m = rng.choice(masses, p=weights, size=n)
    return b, m, v

def total_rate(a):
    """Gamma(<30a) with focusing at the mean relative velocity."""
    b_max = B_MAX_FACTOR * a
    return N_STAR * np.pi * b_max**2 * V_REL * (1 + 2 * GM / (b_max * V_REL**2))

def run_mc(masses, weights, adiabatic=False, seed=SEED):
    """Run the full radius grid for one mass function; return per-bin results.

    adiabatic=False reproduces the conservative impulsive estimate quoted in the
    text.  adiabatic=True applies the Gnedin & Ostriker (1999) correction
    A(x) = (1 + x^2)^{-5/2} per encounter, with x = (b/a)(v_orb/v), which is the
    physical estimate for encounters whose duration exceeds the orbital period.
    """
    rng = np.random.default_rng(seed)
    out = {"a_AU": [], "t_med": [], "t_lo": [], "t_hi": [],
           "p_dis": [], "kick_var": [], "rate_per_yr": [], "x_ad_pen": []}
    for a in a_grid:
        b, m, v = sample_encounters(rng, a, N_ENC_SAMPLE, masses, weights)
        lam = total_rate(a)                                  # encounters / s
        # impulsive tidal kick, saturated for penetrating passages (b <= a).
        geom = np.minimum(1.0, (a / b) ** 2)
        delta = 2 * (m / M_BH) * geom * (v_orb(a) / v)
        d2 = delta ** 2
        # adiabatic parameter x = omega_orb * tau_enc = (b/a)(v_orb/v)
        x_ad = (b / a) * (v_orb(a) / v)
        if adiabatic:
            d2 = d2 * adiabatic_factor(x_ad)
        mu, sd = np.mean(d2), np.std(d2)
        p_dis = np.mean(b < a)                               # penetrating fraction (diagnostic)

        # diffusion channel: encounters needed for sum(delta^2) = E_CROSS^2
        if mu > 0:
            # encounters needed to random-walk to e = E_CROSS, with CLT scatter on the
            # kick-variance sum and Poisson scatter on the arrival times
            n_star = E_CROSS**2 / mu
            n_draw = np.maximum(rng.normal(n_star, (sd / mu) * np.sqrt(max(n_star, 1.0)), size=N_HIST), 1.0)
            t_diff = n_draw / lam * (1 + rng.normal(0, 1 / np.sqrt(n_draw), N_HIST))
            t_diff = np.maximum(t_diff, 0)
        else:
            t_diff = np.full(N_HIST, np.inf)

        t = np.minimum(t_diff, T_CAP)
        out["a_AU"].append(a / AU)
        out["t_med"].append(float(np.median(t) / YR))
        out["t_lo"].append(float(np.percentile(t, 16) / YR))
        out["t_hi"].append(float(np.percentile(t, 84) / YR))
        out["p_dis"].append(float(p_dis))
        out["kick_var"].append(float(mu))
        out["rate_per_yr"].append(float(lam * YR))
        out["x_ad_pen"].append(float(v_orb(a) / V_REL))      # x at b = a, v = v_rel
    return out

SQRT2 = np.sqrt(2.0)
B_MAX_BOUND = 3.0          # bound-channel b_max = 3a, set by the kernel (D1.2.4)
R_P_FID = 4.0e3 * AU       # radius at which N_BH(<r) = 1, D1.3.1
T_1E8 = 1.0e8 * YR

def bound_shell_counts(a, f_bh, m_bh_msun):
    """Expected shell count lambda_s(a) = N_s(<sqrt2 a) - N_s(<a/sqrt2) per species (D1.2.3)."""
    species = species_table(f_bh, m_bh_msun=m_bh_msun)
    lam = {}
    for name, m_kg, gamma_s, f_s in species:
        lam[name] = float(N_enclosed(SQRT2 * a, gamma_s, f_s) - N_enclosed(a / SQRT2, gamma_s, f_s))
    return lam, species

def run_mc_bound(f_bh, m_bh_msun, apply_kernel=True, seed=SEED, n_enc=N_ENC_SAMPLE, n_hist=N_HIST):
    """Bound-member diffusion channel (D1.1-D1.2): Poisson-granular perturber
    counts per history, impulsive kernel with the adiabatic correction applied
    (unless apply_kernel=False, the D1.2.4 diagnostic-only comparison run)."""
    rng = np.random.default_rng(seed)
    species = species_table(f_bh, m_bh_msun=m_bh_msun)
    out = {"a_AU": [], "t_med": [], "t_lo": [], "t_hi": [], "p_bh_present": [],
           "f_cap": [], "p_surv_1e8": []}
    for a in a_grid:
        b_max = B_MAX_BOUND * a
        V_shell = (4 * np.pi / 3) * (2 * SQRT2 - 2 ** -1.5) * a ** 3
        vc = v_orb(a)
        lam_s, gam_tot, mu_s, mean_v_s = {}, {}, {}, {}
        for name, m_kg, gamma_s, f_s in species:
            lam_s[name] = float(N_enclosed(SQRT2 * a, gamma_s, f_s) - N_enclosed(a / SQRT2, gamma_s, f_s))
            s_rel = np.sqrt(2 * GM / ((1.0 + gamma_s) * a))       # D1.2.1
            mean_v_s[name] = np.sqrt(8.0 / np.pi) * s_rel          # Maxwellian mean
            v = s_rel * np.sqrt(rng.chisquare(3, size=n_enc))      # Maxwell(s_rel) draws
            u = rng.random(n_enc)
            b = b_max * np.sqrt(u)                                  # uniform in b^2
            geom = np.minimum(1.0, (a / b) ** 2)
            delta = 2 * (m_kg / M_BH) * geom * (vc / v)
            d2 = delta ** 2
            if apply_kernel:
                x = (b / a) * (vc / v)
                d2 = d2 * adiabatic_factor(x)
            mu_s[name] = float(np.mean(d2))

        p_bh_present = 1.0 - np.exp(-lam_s["bh"])

        Gam_tot = np.zeros(n_hist)
        weighted_mu = np.zeros(n_hist)
        for name, m_kg, gamma_s, f_s in species:
            n_draw = rng.poisson(lam_s[name], size=n_hist)
            Gam_s = (n_draw / V_shell) * np.pi * b_max ** 2 * mean_v_s[name]
            Gam_tot += Gam_s
            weighted_mu += Gam_s * mu_s[name]

        active = Gam_tot > 0
        mu_eff = np.full(n_hist, np.nan)
        mu_eff[active] = weighted_mu[active] / Gam_tot[active]

        n_star = np.where(active, E_CROSS ** 2 / np.where(mu_eff > 0, mu_eff, np.nan), np.inf)
        n_star = np.maximum(n_star, 1.0)
        n_draw_walk = np.where(active,
                                np.maximum(rng.normal(n_star, np.sqrt(np.maximum(n_star, 1.0)), size=n_hist), 1.0),
                                np.inf)
        t_diff = np.where(active, n_draw_walk / np.where(active, Gam_tot, 1.0), np.inf)
        t_diff = np.where(active, t_diff * (1 + rng.normal(0, 1 / np.sqrt(np.maximum(n_draw_walk, 1.0)), n_hist)), t_diff)
        t_diff = np.maximum(t_diff, 0)

        t = np.minimum(t_diff, T_CAP)
        out["a_AU"].append(a / AU)
        out["t_med"].append(float(np.median(t) / YR))
        out["t_lo"].append(float(np.percentile(t, 16) / YR))
        out["t_hi"].append(float(np.percentile(t, 84) / YR))
        out["p_bh_present"].append(float(p_bh_present))
        out["f_cap"].append(float(np.mean(t >= T_CAP)))
        out["p_surv_1e8"].append(float(np.mean(t >= T_1E8)))
    return out

def run_secular(f_bh, m_bh_msun, r_p=R_P_FID, seed=SEED, n_hist=N_HIST):
    """Kozai-Lidov secular clock from the outermost bound heavy remnant (D1.3).
    Returns per-bin t_sec, t_gr, t_mass (median over the M_enc draw), and
    kozai_active_frac, over the full a_grid (the 4e2-4e3 AU plotting window is
    applied by the caller)."""
    rng = np.random.default_rng(seed)
    species = species_table(f_bh, m_bh_msun=m_bh_msun)
    light_species = [s for s in species if s[0] != "bh"]
    m_pert_kg = m_bh_msun * MSUN
    out = {"a_AU": [], "t_sec_yr": [], "t_gr_yr": [], "t_mass_yr": [], "kozai_active_frac": []}
    for a in a_grid:
        Porb = P_orb(a)
        t_sec = (M_BH / m_pert_kg) * (r_p / a) ** 3 * Porb
        t_gr = (a / (3 * RG)) * Porb

        M_enc = np.zeros(n_hist)
        for name, m_kg, gamma_s, f_s in light_species:
            lam = float(N_enclosed(a, gamma_s, f_s))
            M_enc += rng.poisson(lam, size=n_hist) * m_kg
        t_mass = np.where(M_enc > 0, (M_BH / np.where(M_enc > 0, M_enc, 1.0)) * Porb, np.inf)

        gr_ok = t_sec < t_gr
        active_frac = gr_ok * float(np.mean(t_sec < t_mass)) * P_KOZAI_INCL

        out["a_AU"].append(a / AU)
        out["t_sec_yr"].append(float(t_sec / YR))
        out["t_gr_yr"].append(float(t_gr / YR))
        out["t_mass_yr"].append(float(np.median(t_mass) / YR) if np.isfinite(np.median(t_mass)) else float("inf"))
        out["kozai_active_frac"].append(float(active_frac))
    return out

def interp_t(res, a_q):
    a_AU, t_med = np.array(res["a_AU"]), np.array(res["t_med"])
    return float(10 ** np.interp(np.log10(a_q), np.log10(a_AU), np.log10(t_med)))

# --- run all configurations (unbound/impulsive channel, panel a) ---
# Each configuration gets its own seed offset so the curves are independent of
# the order in which they are run.
configs = {"stars_only": (MF_MASSES, MF_WEIGHTS, False)}
for f_bh in F_BH_GRID:
    m, w = remnant_mf(f_bh)
    configs[f"fbh_{f_bh:g}"] = (m, w, False)
# pre-R5 perturber mass, retained so the 10 -> 31 Msun step is auditable
m10, w10 = remnant_mf(F_BH_FID, m_bh=M_BH_PERT_OLD)
configs[f"fbh_{F_BH_FID:g}_m10"] = (m10, w10, False)
# physical (adiabatically corrected) run at the fiducial mass function
mf, wf = remnant_mf(F_BH_FID)
configs[f"fbh_{F_BH_FID:g}_adiabatic"] = (mf, wf, True)

all_res = {name: run_mc(m, w, adiabatic=ad, seed=SEED + 17 * i)
           for i, (name, (m, w, ad)) in enumerate(configs.items())}
base = all_res["stars_only"]
fid = all_res[f"fbh_{F_BH_FID:g}"]
adia = all_res[f"fbh_{F_BH_FID:g}_adiabatic"]

# --- D1: bound-cusp channel (panel b) -----------------------------------
# Joint anchoring of f_BH and m_BH (D1.5): the perturber population is set by
# the extended-dark-mass / mean-remnant-mass pair rather than a stipulated
# number fraction.
F_BH_BOUND_FID = f_bh_central(M_DARK_FID, M_BH_PERT)
F_BH_BOUND_LO = f_bh_central(M_DARK_LO, M_BH_PERT_LO)
F_BH_BOUND_HI = f_bh_central(M_DARK_HI, M_BH_PERT)

bound_configs = {
    "bound_fid": (F_BH_BOUND_FID, M_BH_PERT, True),
    "bound_lo": (F_BH_BOUND_LO, M_BH_PERT_LO, True),
    "bound_hi": (F_BH_BOUND_HI, M_BH_PERT, True),
    "bound_fid_nokernel": (F_BH_BOUND_FID, M_BH_PERT, False),  # D1.2.4 diagnostic only
}
bound_res = {name: run_mc_bound(f_bh, m_bh, apply_kernel=ker, seed=SEED + 251 * i)
             for i, (name, (f_bh, m_bh, ker)) in enumerate(bound_configs.items())}
bound_fid = bound_res["bound_fid"]

secular = run_secular(F_BH_BOUND_FID, M_BH_PERT, seed=SEED + 999)
sec_a = np.array(secular["a_AU"])
sec_window = (sec_a >= 4.0e2) & (sec_a <= 4.0e3)

# --- figure: two panels, unbound channel (a) and bound channel (b) -----
fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.4, 4.2), sharey=True)

a_AU = np.array(fid["a_AU"])
axA.fill_between(a_AU, np.array(fid["t_lo"]), np.array(fid["t_hi"]),
                  alpha=0.25, color="#3b4d8f", lw=0)
axA.loglog(a_AU, np.array(fid["t_med"]), color="#3b4d8f", lw=2,
           label=r"impulsive floor, remnant MF ($f_{\rm BH}=1\%$, $31\,M_\odot$)")
axA.loglog(np.array(base["a_AU"]), np.array(base["t_med"]), color="#7a8ac2",
           lw=1.6, ls="--", label="stars + WDs only")
for f_bh, ls in [(0.001, ":"), (0.03, "-.")]:
    r = all_res[f"fbh_{f_bh:g}"]
    axA.loglog(np.array(r["a_AU"]), np.array(r["t_med"]), color="0.45", lw=1, ls=ls,
               label=rf"$f_{{\rm BH}}={100*f_bh:g}\%$")
axA.loglog(np.array(adia["a_AU"]), np.array(adia["t_med"]), color="#1f7a4d", lw=2,
           label=r"adiabatically corrected (physical), $f_{\rm BH}=1\%$")

# panel (b): bound-member diffusion + secular cadence
b_AU = np.array(bound_fid["a_AU"])
axB.fill_between(b_AU, np.array(bound_fid["t_lo"]), np.array(bound_fid["t_hi"]),
                  alpha=0.22, color="#9c3b3b", lw=0)
axB.loglog(b_AU, np.array(bound_fid["t_med"]), color="#9c3b3b", lw=2,
           label="bound-member diffusion, median")
axB.loglog(b_AU, np.array(bound_fid["t_lo"]), color="#c46a3f", lw=1.4, ls="--",
           label="bound-member diffusion, 16th pct")
sec_line, = axB.loglog(sec_a[sec_window], np.array(secular["t_sec_yr"])[sec_window],
                        color="#c2185b", lw=1.6, ls="-.")
if sec_window.any():
    a_edge = sec_a[sec_window][0]
    axB.annotate("station-keeping cadence (not a survival limit)",
                 xy=(a_edge * 1.05, secular["t_sec_yr"][np.argmax(sec_window)]),
                 fontsize=6.6, color="#8e1245", rotation=25, va="bottom")
    axB.axvline(a_edge, color="#c2185b", ls=":", lw=0.9)
    axB.text(a_edge * 0.92, 2.0e2, r"GR-quenched inward of $\sim4\times10^{2}$ AU",
             rotation=90, fontsize=6.4, va="bottom", ha="right", color="#8e1245")

for x, lab in [(6 * RG / AU, r"$r_{\rm ISCO}$"),
               (100 * RG / AU, r"$10^2\,r_{\rm g}$"),
               (0.1 * R_INFL / AU, r"$0.1\,r_{\rm infl}$")]:
    for ax in (axA, axB):
        ax.axvline(x, color="0.4", ls=":", lw=1)
        ax.text(x / 1.35, 1.6e2, lab, rotation=90, fontsize=7.5, va="bottom", ha="right",
                color="0.25")

for ax in (axA, axB):
    ax.axhline(1e6, color="#b98a2e", ls="--", lw=1)
    ax.axhline(1.2e10, color="0.6", ls="-", lw=0.8)
    ax.set_xlabel("structure semi-major axis  $a$  [AU]")
    ax.set_xlim(0.8 * A_MIN / AU, 5.5e3)
    ax.set_ylim(1e2, 5e10)
axA.text(2.2e-3, 1.3e6, "passive-safety criterion ($10^6$ yr)", fontsize=7.5, color="#7a5a1d")
axA.text(2.2e-3, 1.5e10, "cluster age cap", fontsize=7.5, color="0.4")
axA.set_ylabel("survival time against flybys  [yr]")
axA.set_title("(a) unbound cluster field", fontsize=9)
axB.set_title("(b) bound cusp members", fontsize=9)

hA, lA = axA.get_legend_handles_labels()
axA.legend(hA, lA, loc="lower left", fontsize=6.6, ncol=1, framealpha=0.92,
           title="survival", title_fontsize=6.8)

# panel (b): two legend blocks with headers so survival and maintenance-cadence
# curves cannot be grouped by accident (D1.3.4 point 4).
hB, lB = axB.get_legend_handles_labels()
leg_surv = axB.legend(hB, lB, loc="lower left", fontsize=6.6, ncol=1, framealpha=0.92,
                       title="survival", title_fontsize=6.8)
axB.add_artist(leg_surv)
axB.legend([sec_line], ["Kozai-Lidov cadence"], loc="upper right", fontsize=6.6,
           ncol=1, framealpha=0.92, title="maintenance cadence", title_fontsize=6.8)

fig.tight_layout()
fig.savefig("fig1_envelope.pdf"); fig.savefig("fig1_envelope.png", dpi=110)

# numbers for the text: fiducial-case bins in the main arrays, full per-bin arrays
# for every configuration (R5-V9: the JSON previously stored only the fiducial).
results = dict(fid)
summary, per_config = {}, {}
for name, res in all_res.items():
    summary[name] = {
        "t_at_10AU_yr": interp_t(res, 10),
        "t_at_100AU_yr": interp_t(res, 100),
        "t_at_1000AU_yr": interp_t(res, 1000),
        "t_min_envelope_yr": float(np.min(res["t_med"])),
    }
    per_config[name] = res
for name, res in bound_res.items():
    summary[name] = {
        "t_at_10AU_yr": interp_t(res, 10),
        "t_at_100AU_yr": interp_t(res, 100),
        "t_at_1000AU_yr": interp_t(res, 1000),
        "t_min_envelope_yr": float(np.min(res["t_med"])),
        "p_bh_present_edge": res["p_bh_present"][-1],
        "f_cap_edge": res["f_cap"][-1],
        "p_surv_1e8_edge": res["p_surv_1e8"][-1],
    }
    per_config[name] = res
results["summary"] = summary
results["per_config"] = per_config
results["secular"] = secular
results["joint_anchoring"] = {
    "M_dark_fid_Msun": M_DARK_FID, "M_dark_lo_Msun": M_DARK_LO, "M_dark_hi_Msun": M_DARK_HI,
    "m_BH_pert_fid_Msun": M_BH_PERT, "m_BH_pert_lo_Msun": M_BH_PERT_LO,
    "seg_enhance": SEG_ENHANCE,
    "f_bh_bound_fid": F_BH_BOUND_FID, "f_bh_bound_lo": F_BH_BOUND_LO, "f_bh_bound_hi": F_BH_BOUND_HI,
    "variance_relative": {
        "bound_fid": 1.0,
        "bound_lo": (M_DARK_LO * M_BH_PERT_LO) / (M_DARK_FID * M_BH_PERT),
        "bound_hi": (M_DARK_HI * M_BH_PERT) / (M_DARK_FID * M_BH_PERT),
    },
}
results["config_note"] = (
    "main arrays = fiducial remnant MF (f_BH=1%, f_NS=2%, m_BH=31 Msun, impulsive); "
    "per_config gives full per-bin arrays for every configuration, including the "
    "pre-R5 10 Msun comparison (_m10), the adiabatically-corrected unbound run "
    "(_adiabatic, Gnedin & Ostriker 1999 kernel), and the bound-cusp channel "
    "(bound_fid/bound_lo/bound_hi, kernel applied; bound_fid_nokernel is a "
    "diagnostic-only comparison, D1.2.4). 'secular' is the Kozai-Lidov "
    "station-keeping cadence, D1.3, valid only over its GR/mass-quenched window. "
    "Grid starts at the 6 r_g ISCO.")
with open("fig1_results.json", "w") as f:
    json.dump(results, f, indent=1)
print(json.dumps(summary, indent=1))

# seed-to-seed spread on the min-of-bins statistic, for the Appendix A claim
spread = {}
for f_bh in F_BH_GRID:
    m, w = remnant_mf(f_bh)
    mins = [float(np.min(run_mc(m, w, seed=SEED + 1000 * k)["t_med"])) for k in range(5)]
    spread[f"fbh_{f_bh:g}"] = {"min_yr": mins,
                               "lo": min(mins), "hi": max(mins),
                               "frac_spread": (max(mins) - min(mins)) / np.mean(mins)}
print("seed-to-seed spread on envelope minima:")
print(json.dumps(spread, indent=1))
print("adiabatic parameter x at b=a (first, mid, last bin):",
      [f"{v:.3g}" for v in (fid["x_ad_pen"][0], fid["x_ad_pen"][20], fid["x_ad_pen"][-1])])

# D1.1.2 consistency check
n_bh_infl = float(N_enclosed(R_INFL, GAMMA_BH, F_BH_BOUND_FID))
n_bh_cluster = M_DARK_FID / M_BH_PERT
print(f"D1.1.2 check: N_BH(<r_infl)={n_bh_infl:.3g} of cluster-wide N_BH={n_bh_cluster:.3g} "
      f"-> {100*n_bh_infl/n_bh_cluster:.3g}% of black holes inside r_infl")

# D1.2.6 order-of-magnitude checks at the envelope edge (a = 4e3 AU, last bin)
edge = bound_fid
print("D1.2.6 checks at envelope edge (4e3 AU):",
      {"t_med_yr": edge["t_med"][-1], "t_lo_yr": edge["t_lo"][-1],
       "p_bh_present": edge["p_bh_present"][-1], "f_cap": edge["f_cap"][-1]})

# D1.4.2 bimodality quote and D1.5.1 bracket table
print(f"D1.4.2: p_bh_present at edge = {bound_fid['p_bh_present'][-1]:.3g}, "
      f"16th pct floor = {bound_fid['t_lo'][-1]:.3g} yr")
print("D1.5.1 variance bracket:", results["joint_anchoring"]["variance_relative"])
