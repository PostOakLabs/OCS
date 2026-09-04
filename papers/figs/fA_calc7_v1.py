"""R7-CALC-AB, Paper A (A-CALC-1): enclosed-mass profile, fuel-census reconciliation,
Phase-4 depletion recomputation, spin-up self-consistency (two branches), dense-coding budget.
Deterministic; no randomness. Run plan pre-committed in 0xAlpha/results/R7-CALC-AB.md section 0.1.
Outputs: fA_calc7_profile.json, fA_calc7_dense.json (this directory).
"""
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repo root

# ---------------------------------------------------------------- constants
h = 6.62607015e-34        # J s
hbar = h / (2 * math.pi)
c = 2.99792458e8          # m/s
G = 6.674e-11             # SI (matches board/notes/scripts/r7_adj_1.py)
kB = 1.380649e-23         # J/K
m_p = 1.67262192e-27      # kg
sigma_T = 6.6524587321e-29  # m^2
Msun = 1.98892e30         # kg (matches r7_adj_1.py)
Lsun = 3.828e26           # W
pc = 3.0856775814913673e16  # m
yr = 3.15576e7            # s (Julian)
LN2 = math.log(2)

M_FID = 2e4               # Msun, paper's fiducial hole mass (mth-paper.tex:170)
M_CL = 4e6                # Msun, paper's cluster mass (:389/:403)
D_KPC = 5.49              # kpc, paper's adopted distance (:389/:402)
RC_AMIN = 2.37            # Harris core radius, arcmin
RH_AMIN = 5.00            # Harris half-mass radius, arcmin
CONC = 1.31               # Harris concentration c = log10(rt/rc)
LOG_RHO0_L = 3.15         # Harris log10 central luminosity density, Lsun/pc^3
LOG_TRC = 9.60            # Harris log10 core relaxation time, yr
ETA_REF = 0.1             # paper's reference efficiency (:217)
T_CMB = 2.7               # K, paper's value (:258)
MEAN_STAR = 0.43          # Msun/star, paper's own implied conversion (:217)
MEAN_STAR_BRACKET = (0.35, 0.43, 0.55)
NE_AMBIENT = 0.23         # cm^-3, paper's ambient (:269)
NE_FED_LO = 1e4           # cm^-3 (:269)
NE_FED_HI = 1e8           # cm^-3 (:269)

ARCSEC_RAD = math.pi / (180 * 3600)
PC_PER_AMIN = D_KPC * 1000 * (60 * ARCSEC_RAD)

failures = []


def check(name, ok, detail):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}: {detail}")
    if not ok:
        failures.append(name)


# ---------------------------------------------------------------- gate G-A1
def gate_A1():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "board", "notes", "scripts", "r7_adj_1.py")],
                         capture_output=True, text=True).stdout
    m = re.search(r"delivered mass.*?: ([\d.e+-]+)", out)
    dM_adj = float(m.group(1))
    inv2 = float(re.search(r"M\(<2pc\)=([\d.e+-]+)", out).group(1))
    inv10 = float(re.search(r"M\(<10pc\)=([\d.e+-]+)", out).group(1))
    # R9-A-1 (A-R9-07): this gate used to PASS on the legacy script's own
    # inverted census (1.458e5 / 3.50e6 Msun), which the paper no longer
    # prints -- the King profile of Sec. 4.2 gives 1.068e5 / 1.866e6, i.e.
    # 37% / 88% apart. Certifying the stale set was the failure mode. Only
    # the delivered mass, which both routes share, is gated here; the
    # census gate moved to G-A1b below and reads the profile.
    check("G-A1 delivered Phase-4 mass", abs(dM_adj / 24048.0 - 1) < 2e-3,
          f"dM={dM_adj:.4e} Msun = (2.2024-1) x 2e4")
    print(f"       [SUPERSEDED provenance: legacy adj inversion M(<2pc)={inv2:.3e}, "
          f"M(<10pc)={inv10:.3e}, giving 16.5%/0.69%. The paper prints the "
          f"profile reading instead; see G-A1b.]")
    return {"adj_dM": dM_adj, "inv_M2": inv2, "inv_M10": inv10}


# ---------------------------------------------------------------- gate G-A2
def gate_A2():
    rg = G * M_FID * Msun / c ** 2
    E_grav = h * c / rg
    TH = (hbar * c ** 3) / (8 * math.pi * G * M_FID * Msun * kB)
    LEdd_coeff = 4 * math.pi * G * m_p * c / sigma_T * Msun   # W per Msun of hole mass
    LEdd = LEdd_coeff * M_FID
    t_edd = ETA_REF * c ** 2 * Msun / LEdd / yr
    # R9-A-1 (A-R9-08): anchor was 3e3 (the catalogued BV21 value quoted in
    # Table 1); the King model this paper integrates has rho_c = 4.03e3, and
    # the prose at :231 uses 4e3. Flat-core M(<1pc) at 4e3 lands within 6%
    # of the profile's 1.58e4; at 3e3 it is 20% low.
    flat_M1 = (4 * math.pi / 3) * 4e3
    efolds = math.log(2.2024)
    ok = (abs(E_grav / 6.73e-33 - 1) < 0.01 and abs(TH / 3.1e-12 - 1) < 0.05
          and abs(LEdd / 2.52e35 - 1) < 0.01 and abs(t_edd / 2247 - 1) < 0.02
          and abs(flat_M1 / 1.6755e4 - 1) < 1e-3 and abs(efolds / 0.790 - 1) < 5e-3)
    check("G-A2 paper anchors", ok,
          f"hc/rg={E_grav:.3e} J, T_H={TH:.3e} K, L_Edd coeff={LEdd_coeff:.3e} W, "
          f"t_Edd={t_edd:.0f} yr/Msun, flat-core M(<1pc)={flat_M1:.3e}, ln(2.2024)={efolds:.4f}")
    return dict(rg_m=rg, E_grav=E_grav, T_H=TH, LEdd_coeff=LEdd_coeff, t_edd_per_msun=t_edd)


# ---------------------------------------------------------------- gate G-A3 (Harris row integrity, fetched primaries)
HARRIS = dict(c=1.31, rc_amin=2.37, rh_amin=5.00, log_rho0_L=3.15, log_trc=9.60, log_trh=10.09,
              sigma_p=16.8, sigma_p_err=0.3, mM_V=13.94, EbV=0.12, Vt=3.68, FeH=-1.53, Vr=232.1)
check("G-A3 Harris row", abs(HARRIS["log_trc"] - 9.60) < 1e-9 and abs(HARRIS["c"] - CONC) < 1e-9
      and abs(HARRIS["rc_amin"] - RC_AMIN) < 1e-9,
      f"c={CONC}, r_c={RC_AMIN}', 10^9.60 yr = {10**9.60/1e9:.2f} Gyr core relaxation "
      f"(paper :470 prints '~4-Gyr core relaxation time')")


# ---------------------------------------------------------------- King model
def rho_raw(W):
    if W <= 0:
        return 0.0
    return math.exp(W) * math.erf(math.sqrt(W)) - math.sqrt(4 * W / math.pi) * (1 + 2 * W / 3)


def king_curve(W0, ds=0.005):
    """Lowered-isothermal (King 1962) dimensionless Poisson integration in s = ln x.
    r_0^2 = 9 sigma_K^2/(4 pi G rho_c) with rho_c the model's own central density
    (King's definition), so the source term is -9 rho_hat with rho_hat(W0)=1.
    State: (W, y), y = dW/dlnx. Returns strictly increasing x-grid, W-grid, x_t."""
    norm = rho_raw(W0)
    x0 = 1e-3
    W = W0 - 1.5 * x0 * x0
    y = -3 * x0

    def f(sv, state):
        xx = x0 * math.exp(sv)
        return [state[1], -state[1] - 9 * xx * xx * rho_raw(state[0]) / norm]

    xs, Ws = [x0], [W]
    s = 0.0
    while True:
        k1 = f(s, (W, y))
        k2 = f(s + ds / 2, (W + ds / 2 * k1[0], y + ds / 2 * k1[1]))
        k3 = f(s + ds / 2, (W + ds / 2 * k2[0], y + ds / 2 * k2[1]))
        k4 = f(s + ds, (W + ds * k3[0], y + ds * k3[1]))
        W_n = W + ds / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        y_n = y + ds / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        if W_n <= 0:
            fr = W / (W - W_n)
            s_t = s + ds * min(max(fr, 0.0), 1.0)
            xs.append(x0 * math.exp(s_t))
            Ws.append(0.0)
            break
        s += ds
        W, y = W_n, y_n
        xs.append(x0 * math.exp(s))
        Ws.append(W)
    return xs, Ws, xs[-1]


def shoot_concentration(target=CONC):
    lo, hi = 2.0, 12.0
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        _, _, xt = king_curve(mid, ds=0.01)
        cc = math.log10(xt)
        if cc < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def enclosed_mass_fraction(xs, Ws, norm):
    """cumulative int x^2 rho_hat dx (trapezoid), rho_hat = rho_raw(W)/rho_raw(W0)."""
    cum = [0.0]
    for i in range(1, len(xs)):
        hstep = xs[i] - xs[i - 1]
        g = xs[i] ** 2 * rho_raw(Ws[i]) / norm + xs[i - 1] ** 2 * rho_raw(Ws[i - 1]) / norm
        cum.append(cum[-1] + 0.5 * hstep * g)
    tot = cum[-1]

    def frac(xq):
        import bisect
        i = min(bisect.bisect_left(xs, xq) - 1, len(xs) - 2)
        i = max(i, 0)
        t = (xq - xs[i]) / (xs[i + 1] - xs[i])
        t = min(max(t, 0.0), 1.0)
        return (cum[i] + t * (cum[i + 1] - cum[i])) / tot

    return frac, tot


def interp(xs, ys, xq):
    import bisect
    i = min(bisect.bisect_left(xs, xq) - 1, len(xs) - 2)
    i = max(i, 0)
    t = (xq - xs[i]) / (xs[i + 1] - xs[i])
    t = min(max(t, 0.0), 1.0)
    return ys[i] + t * (ys[i + 1] - ys[i])


# ---------------------------------------------------------------- Bardeen ISCO + spin-up branches
def isco_energy_angular(a):
    """Bardeen-Press-Teukolsky prograde ISCO specific energy (c^2=1) and angular momentum (GM/c=1).

    R9-A-1 (2026-09-03): two errors repaired here. (i) z2 read
    sqrt(3 z1^2 + a^2); BPT (1972) Eq. 2.21 is sqrt(3 a^2 + z1^2).
    (ii) the ISCO radius took the "+" root, which is the RETROGRADE
    orbit; prograde is the "-" root. Together these put eta(0) at
    0.0505 and eta(0.998) at 0.0515, neither of which is the paper's
    own printed 0.0572 / 0.3210 -- see gate G-A4 below, which now
    fails loudly on any regression.
    """
    z1 = 1 + (1 - a * a) ** (1 / 3) * ((1 + a) ** (1 / 3) + (1 - a) ** (1 / 3))
    z2 = math.sqrt(3 * a * a + z1 * z1)
    x = 3 + z2 - math.sqrt(max((3 - z1) * (3 + z1 + 2 * z2), 0.0))
    sx = math.sqrt(x)
    den = x ** 0.75 * math.sqrt(x ** 1.5 - 3 * sx + 2 * a)
    E = (x ** 1.5 - 2 * sx + a) / den
    L = (x * x - 2 * a * sx + a * a) / den
    return E, L


def spinup_track(lnm_end=math.log(2.2024), n=40000):
    """da/dlnm = (l_ISCO - 2a E_ISCO)/E_ISCO on the geodesic track from a=0
    (Bardeen 1970). Returns m-grid, eta-grid (geodesic 1-E_ISCO), a_end.

    R9-A-1 (2026-09-03): the /E_ISCO divisor was missing. dM in
    Bardeen's da/dM is rest mass accreted, but dM_hole = E_ISCO dM_rest,
    so per unit of HOLE mass the spin gain is (l - 2aE)/E. Without it
    the track over-spins and reaches a*=0.998 at m=1.505 instead of the
    2.2024 the paper prints.
    """
    dl = lnm_end / n
    lnm = 0.0
    a = 0.0

    def f(l_, a_):
        E, L = isco_energy_angular(min(max(a_, 0.0), 0.999999))
        return (L - 2 * a_ * E) / E

    ms, etas = [1.0], [1 - isco_energy_angular(0)[0]]
    for i in range(n):
        k1 = f(lnm, a); k2 = f(lnm + dl / 2, a + dl / 2 * k1)
        k3 = f(lnm + dl / 2, a + dl / 2 * k2); k4 = f(lnm + dl, a + dl * k3)
        a += dl / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        a = min(max(a, 0.0), 0.999995)
        lnm += dl
        ms.append(math.exp(lnm))
        etas.append(1 - isco_energy_angular(a)[0])
    return ms, etas, a


def spinup_eta_of_m(ms, etas, eta_plateau=0.30, a_cap=0.998):
    """Strict branch: geodesic-track efficiency until a* reaches the Thorne cap,
    then the capture-corrected equilibrium efficiency 0.30 (the paper's own value, :181)."""
    dl = math.log(ms[1] / ms[0])

    def _dadl(a_):
        E, L = isco_energy_angular(min(max(a_, 0.0), 0.999999))
        return (L - 2 * a_ * E) / E

    out = list(etas)
    a = 0.0
    crossed = False
    for i in range(len(ms)):
        if i > 0:
            k1 = _dadl(a); k2 = _dadl(a + dl / 2 * k1); k3 = _dadl(a + dl / 2 * k2)
            k4 = _dadl(a + dl * k3)
            a = min(max(a + dl / 6 * (k1 + 2 * k2 + 2 * k3 + k4), 0.0), 0.999995)
        if not crossed and a >= a_cap:
            crossed = True
        if crossed:
            out[i] = eta_plateau
    return out


# ---------------------------------------------------------------- gate G-A4 (ISCO + Bardeen track)
def gate_A4():
    """Pin the ISCO solver against values the paper itself prints, and the
    spin-up track against Bardeen (1970). Added by R9-A-1 after the shipped
    solver was found wrong in three compounding ways while every existing
    gate still passed: nothing here touched the ISCO, so nothing caught it.

    Checks: eta(0) = 1 - sqrt(8/9) = 0.05719 (r_ISCO = 6 r_g);
            eta(0.998) = 0.32100 (paper :190, Fig. 1 node);
            r_ISCO(0.998) = 1.2370 r_g;
            m(a* = 0.998) = 2.2024 (paper :267 growth factor);
            m(a* -> 1) -> sqrt(6) = 2.4495 (Bardeen 1970).
    """
    E0, _ = isco_energy_angular(0.0)
    E998, _ = isco_energy_angular(0.998)
    z1 = 1 + (1 - 0.998 ** 2) ** (1 / 3) * ((1.998) ** (1 / 3) + (0.002) ** (1 / 3))
    z2 = math.sqrt(3 * 0.998 ** 2 + z1 * z1)
    r998 = 3 + z2 - math.sqrt((3 - z1) * (3 + z1 + 2 * z2))

    def _m_at(a_target, n=200000, lnm_max=1.5):
        dl, a, lnm = lnm_max / n, 0.0, 0.0
        for _ in range(n):
            def d(x):
                E, L = isco_energy_angular(min(max(x, 0.0), 0.999999))
                return (L - 2 * x * E) / E
            k1 = d(a); k2 = d(a + dl / 2 * k1); k3 = d(a + dl / 2 * k2); k4 = d(a + dl * k3)
            an = a + dl / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            if an >= a_target:
                return math.exp(lnm + dl * (a_target - a) / (an - a))
            a, lnm = an, lnm + dl
        return math.exp(lnm)

    m998 = _m_at(0.998)
    m_ext = _m_at(0.999999)
    ok = (abs((1 - E0) / 0.057191 - 1) < 1e-4 and abs((1 - E998) / 0.321000 - 1) < 1e-4
          and abs(r998 / 1.23697 - 1) < 1e-4 and abs(m998 / 2.2024 - 1) < 1e-3
          and abs(m_ext / math.sqrt(6) - 1) < 0.01)
    check("G-A4 ISCO + Bardeen track", ok,
          f"eta(0)={1-E0:.5f} (0.05719), eta(0.998)={1-E998:.5f} (0.32100), "
          f"r_ISCO(0.998)={r998:.5f} r_g (1.23697), m(0.998)={m998:.5f} (2.2024), "
          f"m(a*->1)={m_ext:.4f} (sqrt6=2.4495)")
    return dict(eta_0=1 - E0, eta_998=1 - E998, r_isco_998=r998,
                m_at_998=m998, m_extremal=m_ext, sqrt6=math.sqrt(6))


# ================================================================= run
print("=" * 72)
gA1 = gate_A1()
gA2 = gate_A2()
gA4 = gate_A4()

print("\n--- King profile build ---")
W0 = shoot_concentration()
xs, Ws, x_t = king_curve(W0, ds=0.005)
norm = rho_raw(W0)
conc_model = math.log10(x_t)
frac, Itot = enclosed_mass_fraction(xs, Ws, norm)

rc_pc = RC_AMIN * PC_PER_AMIN
rt_pc = x_t * rc_pc
m_tot_4pi = 4 * math.pi * Itot                       # dimensionless M_tot/(rho_c r0^3)
rho_c_true = M_CL / (rc_pc ** 3 * m_tot_4pi)         # model central mass density, Msun/pc^3
df_amp = rho_c_true / norm                           # DF coefficient rho1

# half-mass radius: invert enclosed fraction = 1/2
lo, hi = 1e-3, x_t
for _ in range(60):
    mid = 0.5 * (lo + hi)
    if frac(mid) < 0.5:
        lo = mid
    else:
        hi = mid
x_h = 0.5 * (lo + hi)
rh_model_pc = x_h * rc_pc
rh_harris_pc = RH_AMIN * PC_PER_AMIN * (D_KPC / 5.2)     # Harris angular value scaled to paper's distance

MV_sun = 4.83
LV = 10 ** (-0.4 * (-10.26 - MV_sun))                    # Lsun from paper's M_V,t = -10.26
ML_global = M_CL / LV
log_rhol_model = math.log10(rho_c_true / ML_global)

print(f"W0={W0:.4f}  x_t={x_t:.3f}  c_model={conc_model:.4f} (target {CONC})")
print(f"r_c={rc_pc:.3f} pc   r_t={rt_pc:.2f} pc")
print(f"rho_c(model central)={rho_c_true:.4g} Msun/pc^3   DF amplitude rho1={df_amp:.4g}")
print(f"half-mass: model(3D)={rh_model_pc:.2f} pc; as projected (/1.305, Plummer-equivalent) "
      f"={rh_model_pc / 1.305:.2f} pc = {rh_model_pc / 1.305 / PC_PER_AMIN:.2f}' vs Harris {RH_AMIN:.2f}'")
print(f"L_V={LV:.3e} Lsun -> global M/L_V={ML_global:.2f}")
print(f"log rho0,L(model)={log_rhol_model:.2f} vs Harris {LOG_RHO0_L}")

profile_checks = {
    "conc_model": conc_model,
    "rh_model_pc": rh_model_pc, "rh_harris_scaled_pc": rh_harris_pc,
    "rho_c_model": rho_c_true, "rho_c_paper_adopted": 3e3,
    "df_amplitude": df_amp,
    "log_rho0_L_model": log_rhol_model, "log_rho0_L_harris": LOG_RHO0_L,
    "ML_V_global": ML_global,
}

# ---------------------------------------------------------------- census reconciliation
print("\n--- census reconciliation (profile vs printed set) ---")
radii = [1.0, 2.0, 10.0]
prof_mass = {}
prof_stars = {}
for r in radii:
    fr = frac(r / rc_pc)
    M_r = M_CL * fr
    prof_mass[r] = M_r
    prof_stars[r] = M_r / MEAN_STAR
    print(f"M(<{r:g} pc) = {M_r:.4e} Msun  ({M_r/MEAN_STAR:.3e} stars @ {MEAN_STAR})")

t_edd = gA2["t_edd_per_msun"]
fuel_years = {r: prof_mass[r] * t_edd for r in radii}
flat_M1 = (4 * math.pi / 3) * 3e3
print(f"Eddington fuel years per Msun at eta=0.1, M=2e4: {t_edd:.0f} yr")

dM = 24048.0
dep_prof_2 = 100 * dM / prof_mass[2.0]
dep_prof_10 = 100 * dM / prof_mass[10.0]
dep_printed = dict(pct2=24.0, pct10=1.0)
dep_adj = dict(M2=gA1["inv_M2"], M10=gA1["inv_M10"], pct2=100 * dM / gA1["inv_M2"], pct10=100 * dM / gA1["inv_M10"])
print(f"\ndelivered Phase-4 mass dM = {dM:.1f} Msun (= {(2.2024-1)*2e4:.1f})")
print(f"profile reading: {dep_prof_2:.1f}% inside 2 pc, {dep_prof_10:.2f}% inside 10 pc")
print(f"ADJ inversion:   {dep_adj['pct2']:.1f}% inside 2 pc, {dep_adj['pct10']:.2f}% inside 10 pc")
print(f"printed at :470: {dep_printed['pct2']:.0f}% inside 2 pc, ~{dep_printed['pct10']:.0f}% inside 10 pc")

# --- G-A1b: the census gate the paper actually prints (replaces G-A1's stale set)
TAB5_PRINTED = {1.0: 1.6e4, 2.0: 1.1e5, 10.0: 1.9e6}
tab5_dev = {r: prof_mass[r] / TAB5_PRINTED[r] - 1 for r in radii}
check("G-A1b Table 5 vs King profile", max(abs(v) for v in tab5_dev.values()) < 0.05,
      "; ".join(f"{r:g} pc: {prof_mass[r]:.4g} vs printed {TAB5_PRINTED[r]:.2g} "
                f"({100*tab5_dev[r]:+.1f}%)" for r in radii))
check("G-A1b depletion vs :645", abs(dep_prof_2 / 22.5 - 1) < 2e-3 and abs(dep_prof_10 / 1.29 - 1) < 5e-3,
      f"{dep_prof_2:.2f}% inside 2 pc (printed 22.5), {dep_prof_10:.3f}% inside 10 pc (printed 1.29)")

# --- growth-aware Eddington durations for Table 5 (A-R8-01) -------------
# The printed column is fuel mass expressed in Eddington-years at FIXED
# M = 2e4 (linear in M_fuel). Feeding the hole raises L_Edd, so the time to
# actually consume the reservoir is t_S ln(1 + M_fuel/M_i), t_S = eta c^2/(kappa).
t_salpeter = ETA_REF * c ** 2 * Msun / gA2["LEdd_coeff"] / yr
growth_aware = {r: t_salpeter * math.log(1 + prof_mass[r] / M_FID) for r in radii}
endpoint = {r: M_FID + prof_mass[r] for r in radii}
print("\n--- Table 5 duration columns (A-R8-01) ---")
print(f"Salpeter time t_S = eta c^2 M/L_Edd(M) = {t_salpeter:.4e} yr at eta=0.1 (mass-independent)")
for r in radii:
    print(f"  {r:g} pc: fuel-at-fixed-M {fuel_years[r]:.3e} yr | growth-aware "
          f"{growth_aware[r]:.3e} yr | endpoint mass {endpoint[r]:.3e} Msun"
          + ("   <-- OUTSIDE criterion 1's 1e3-1e5 range" if endpoint[r] > 1e5 else ""))

# --- r_infl for the omega Cen row of Table 3 (A-R9-11 / A-R8-09) --------
r_infl_168 = G * 1e4 * Msun / (16.8e3) ** 2 / pc
sigma_for_010 = math.sqrt(G * 1e4 * Msun / (0.10 * pc)) / 1e3
check("G-A5 r_infl at catalogued sigma", abs(r_infl_168 / 0.152 - 1) < 0.02,
      f"GM/sigma^2 at 1e4 Msun, sigma_c=16.8 km/s = {r_infl_168:.4f} pc; "
      f"Table 3 now prints 0.15 (pre-v2.7 drafts printed 0.10, which needs "
      f"sigma = {sigma_for_010:.1f} km/s and does not match the caption's convention)")

stars10_lo = prof_mass[10.0] / 0.55
stars10_hi = prof_mass[10.0] / 0.35
print(f"\nstar counts inside 10 pc: {prof_stars[10.0]:.2e} @0.43 (bracket {stars10_lo:.2e} - {stars10_hi:.2e})")
print("printed ':138/:217': ~1e6 stars")

# ---------------------------------------------------------------- spin-up branches (A-P8)
print("\n--- spin-up self-consistency ---")
Mi, growth = 2e4, 2.2024
Mf = Mi * growth
mean_M = 0.5 * (Mi + Mf)
LEdd = lambda M_: 4 * math.pi * G * m_p * c / sigma_T * M_ * Msun
eta_eff_S1 = ETA_REF
t_S1 = eta_eff_S1 * c ** 2 * ((growth - 1) * Mi * Msun) / LEdd(mean_M) / yr
ms_track, etas_track, a_end = spinup_track()
etas_capped = spinup_eta_of_m(ms_track, etas_track)


def _int_trap(mm, ee, dlog=False):
    """Trapezoid in m, or in ln m when dlog=True."""
    acc = 0.0
    for i in range(1, len(mm)):
        dx = (math.log(mm[i]) - math.log(mm[i - 1])) if dlog else (mm[i] - mm[i - 1])
        acc += 0.5 * (ee[i] + ee[i - 1]) * dx
    return acc


# R9-A-1 (2026-09-03): the duration integral was taken over dm, not dlnm.
# dt = eta c^2 dM_phys / L_Edd(M) and L_Edd is linear in M, so
# t = (c^2 Msun / kappa_Edd) * int eta dlnm exactly -- the prefactor
# c^2 Mi Msun / L_Edd(Mi) is already the growth-aware one; only the
# integration variable was wrong.
int_eta_dlnm = _int_trap(ms_track, etas_capped, dlog=True)
int_eta_geo = _int_trap(ms_track, etas_track, dlog=True)
int_eta_dm_legacy = _int_trap(ms_track, etas_capped)      # retained: reproduces the withdrawn 1.05e8 yr
m_cap = next((ms_track[i] for i, e in enumerate(etas_capped) if e == 0.30), None)
t_S2 = c ** 2 * (int_eta_dlnm * Mi * Msun) / LEdd(Mi) / yr
n_stars_spinup = dM / MEAN_STAR
rate = n_stars_spinup / t_S1
t_S1_growth = ETA_REF * c ** 2 * Mi * Msun / LEdd(Mi) * math.log(growth) / yr
print(f"S1 (reproduction branch, eta=0.1 at mean mass {mean_M:.3e}): t = {t_S1:.3e} yr  (paper prints ~3.5e7)")
print(f"S1g (growth-aware, eta=0.1, t_S ln(Mf/Mi)):                  t = {t_S1_growth:.3e} yr")
print(f"S2 (strict branch, geodesic track, a*=0.998 reached at m={m_cap if m_cap else ms_track[-1]:.5f}): "
      f"int eta dlnm = {int_eta_dlnm:.5f}; t = {t_S2:.4e} yr  ({t_S2/t_S1:.2f}x S1)")
print(f"S2 bracket (pure geodesic, no capture correction, int eta dlnm = {int_eta_geo:.5f}): "
      f"t = {c ** 2 * int_eta_geo * Mi * Msun / LEdd(Mi) / yr:.4e} yr")
print(f"  [withdrawn pre-R9 value, int eta dm = {int_eta_dm_legacy:.3f} -> "
      f"{c ** 2 * int_eta_dm_legacy * Mi * Msun / LEdd(Mi) / yr:.3e} yr; NOT quoted]")
# A-R8-14: the 2.4048e4 Msun is the HOLE mass increment. Delivered rest mass
# is larger by 1/E_ISCO integrated along the track, since dM_hole = E dM_rest.
_dl_tr = math.log(ms_track[1] / ms_track[0])
m_rest_delivered = 0.0
for _i in range(len(ms_track) - 1):
    _a = None
_a_tr = 0.0
for _i in range(len(ms_track) - 1):
    _E, _L = isco_energy_angular(min(max(_a_tr, 0.0), 0.999999))
    m_rest_delivered += Mi * ms_track[_i] * _dl_tr / _E
    _k1 = (_L - 2 * _a_tr * _E) / _E
    def _d(x):
        e_, l_ = isco_energy_angular(min(max(x, 0.0), 0.999999))
        return (l_ - 2 * x * e_) / e_
    _k2 = _d(_a_tr + _dl_tr / 2 * _k1); _k3 = _d(_a_tr + _dl_tr / 2 * _k2)
    _k4 = _d(_a_tr + _dl_tr * _k3)
    _a_tr = min(max(_a_tr + _dl_tr / 6 * (_k1 + 2 * _k2 + 2 * _k3 + _k4), 0.0), 0.999995)
print(f"track end a*={a_end:.4f}")
print(f"delivered rest mass = {m_rest_delivered:.4e} Msun vs hole increment "
      f"{dM:.4e} Msun (ratio {m_rest_delivered/dM:.3f}); "
      f"{m_rest_delivered/MEAN_STAR:.3e} stars at 0.43 Msun")
print(f"star cost: {n_stars_spinup:.3e} @0.43 (printed 1e4-5); rate {rate:.2e}/yr (printed 3e-4 - 3e-3)")

# ---------------------------------------------------------------- Phase-4 tug pricing rescale (A-M3 rider, :476)
print("\n--- :476 delta-v pricing rescale (linear in consumed mass) ---")
v_kvms = 1e5  # 100 km/s
KE_printed = 0.5 * 3e4 * Msun * v_kvms ** 2
EP_printed = 3e4 * Msun * v_kvms * c
dur = 3.5e7 * yr
KE_new = 0.5 * dM * Msun * v_kvms ** 2
EP_new = dM * Msun * v_kvms * c
L_ke_new = KE_new / dur / Lsun
L_ph_new = EP_new / dur / Lsun
ceiling = 7.6e5
ratio_new = L_ph_new / ceiling
print(f"validation at printed 3e4: KE={KE_printed:.3e} J (~3e44 printed), E_ph={EP_printed:.3e} J (~1.8e48), "
      f"L_ph={EP_printed/dur/Lsun:.3e} Lsun (~4.2e6), ratio={EP_printed/dur/Lsun/ceiling:.2f} (~5.6)")
print(f"rescaled at 2.4048e4: KE={KE_new:.3e} J, E_ph={EP_new:.3e} J, L_avg={L_ke_new:.2e} Lsun, "
      f"photon-tug={L_ph_new:.3e} Lsun = {ratio_new:.1f}x ambient ceiling")

# --- A-R9-02: the exclusion verdict depends on a delta-v the paper does not
# use anywhere else. :647 states the per-star impulse is "of order the local
# orbital speed, tens of km/s"; the King profile gives 8.2/15.2/28.3 km/s at
# 1/2/10 pc. Price the bracket at both candidate episode durations.
print("")
print("--- A-R9-02 tug bracket over delta-v and episode duration ---")
def _vcirc(r_pc):
    return math.sqrt(G * prof_mass[r_pc] * Msun / (r_pc * pc)) / 1e3
print("  King-profile circular speeds: " + ", ".join(
    f"{_vcirc(r):.1f} km/s at {r:g} pc" for r in radii))
tug_rows = []
for dv_kms in (20.0, 30.0, 100.0):
    dv = dv_kms * 1e3
    for dur_yr, lbl in ((t_S1, "S1 3.38e7 yr"), (t_S2, "S2 5.31e7 yr")):
        dur = dur_yr * yr
        L_ke = 0.5 * dM * Msun * dv ** 2 / dur / Lsun
        L_ph = dM * Msun * dv * c / dur / Lsun
        verdict = "EXCLUDED" if L_ph / ceiling > 1 else "fits"
        tug_rows.append(dict(dv_kms=dv_kms, duration_label=lbl, duration_yr=dur_yr,
                             L_kinetic_Lsun=L_ke, L_photon_Lsun=L_ph,
                             ratio_to_ceiling=L_ph / ceiling, verdict=verdict))
        print(f"  dv={dv_kms:5.0f} km/s, {lbl}: L_kin={L_ke:8.1f} Lsun, "
              f"L_photon={L_ph:.3e} Lsun = {L_ph/ceiling:5.2f}x ceiling -> {verdict}")
# The 7.6e5 Lsun ceiling is Paper E's ambient BONDI accretion power, not a
# JWST limit (A-R8-04); and it is in any case the wrong comparator for tug
# heat, which the paper itself says is reradiated at stellar temperature by
# the star being moved. The robust bound is the cluster's own integrated
# light: a diffuse excess of this size would show up in ordinary photometry.
print("  against the cluster's integrated luminosity "
      f"(L_V = {LV:.3e} Lsun from M_V,t = -10.26):")
lightfrac_rows = []
for dv_kms in (_vcirc(1.0), 20.0, _vcirc(10.0), 100.0):
    L_ph = dM * Msun * (dv_kms * 1e3) * c / (t_S2 * yr) / Lsun
    L_ke = 0.5 * dM * Msun * (dv_kms * 1e3) ** 2 / (t_S2 * yr) / Lsun
    lightfrac_rows.append(dict(dv_kms=dv_kms, photon_frac_of_LV=L_ph / LV,
                               kinetic_frac_of_LV=L_ke / LV))
    print(f"    dv={dv_kms:5.1f} km/s: photon tug = {100*L_ph/LV:6.1f}% of cluster light; "
          f"gravitational assist (kinetic only) = {100*L_ke/LV:.2e}%")
check("G-A7 photon tug excluded on integrated light",
      min(r["photon_frac_of_LV"] for r in lightfrac_rows) > 0.10
      and max(r["kinetic_frac_of_LV"] for r in lightfrac_rows) < 1e-3,
      "photon tug costs 10-100 per cent of the cluster's total luminosity at every "
      "delta-v in the orbital-speed bracket, while the kinetic (gravitational-assist) "
      "channel costs under 0.1 per cent: the exclusion holds, on a comparator that "
      "does not depend on the contested ambient-fuel ceiling")

dv_break = ceiling * Lsun * (t_S2 * yr) / (dM * Msun * c) / 1e3
print(f"  photon-tug exclusion threshold at the S2 duration: delta-v > {dv_break:.0f} km/s "
      f"(at S1: {ceiling*Lsun*(t_S1*yr)/(dM*Msun*c)/1e3:.0f} km/s)")
print(f"  -> against the ambient-fuel ceiling alone, the paper's own orbital-speed scale "
      f"({_vcirc(1.0):.0f}-{_vcirc(10.0):.0f} km/s) does NOT exclude the photon tug; "
      f"the exclusion rests on the integrated-light bound above.")

# ---------------------------------------------------------------- A-R9-04/05: headline ratios
print("")
print("--- A-R9-04/05: headline efficiency ratios, one denominator convention ---")
X_H = 0.7
Y_FUSION_RAW = 0.0071                      # H -> He rest-mass release
Y_FUSION_COMPLETE = Y_FUSION_RAW * X_H     # complete fusion of a star's H
Y_DYSON = Y_FUSION_RAW * X_H * 0.1         # unassisted MS star burns ~10% of its mass
ETA_SCHW, ETA_THORNE, ETA_EXTREMAL = 0.0572, 0.30, 0.4226
ratio_rows = []
for dlabel, dval in (("raw H fusion (0.0071)", Y_FUSION_RAW),
                     ("complete fusion / star lifting", Y_FUSION_COMPLETE),
                     ("Dyson, no star lifting", Y_DYSON)):
    row = dict(denominator=dlabel, yield_=dval,
               schwarzschild=ETA_SCHW / dval, thorne=ETA_THORNE / dval,
               formal_extremal=ETA_EXTREMAL / dval)
    ratio_rows.append(row)
    print(f"  vs {dlabel:32s} (y={dval:.3g}): a*=0 {row['schwarzschild']:6.1f}x | "
          f"Thorne {row['thorne']:6.1f}x | formal extremal {row['formal_extremal']:6.1f}x")
print(f"  spin-up payoff eta(0.998)/eta(0) = {ETA_THORNE/ETA_SCHW:.2f}x "
      f"(formal extremal {ETA_EXTREMAL/ETA_SCHW:.2f}x)")
print("  NOTE (A-R9-04): the Dyson yield now carries X_H, matching the stellar-yield")
print("  line; the hydrogen-only convention (7.1e-4) gives "
      f"{ETA_SCHW/(Y_FUSION_RAW*0.1):.0f}-{ETA_THORNE/(Y_FUSION_RAW*0.1):.0f}x instead.")
bits_schw = 1.5e77 * M_FID ** 2
check("G-A8 storage pair", abs(bits_schw / 6.0e85 - 1) < 0.02,
      f"1.5e77 M^2 at {M_FID:.0g} Msun = {bits_schw:.3g} bits (Schwarzschild); "
      f"x0.53 at a*=0.998 = {0.53*bits_schw:.3g} bits. Abstract and body now print "
      f"this pair; the pre-v2.7 abstract's '~1e86' was {1e86/bits_schw:.2f}x the "
      f"Schwarzschild value and {1e86/(0.53*bits_schw):.1f}x the Kerr one.")

# ---------------------------------------------------------------- dense-coding budget (A-n4/A-P7)
print("\n--- dense-coding delivery budget ---")
eps_CMB = kB * T_CMB * LN2
rg = gA2["rg_m"]
E_grav = g2 = h * c / rg
floors = [("F0 vacuum hc/rg", E_grav),
          ("F1 ambient n_e=0.23", h * 8.98e3 * math.sqrt(NE_AMBIENT)),
          ("F2 fed n_e=1e4", h * 8.98e3 * math.sqrt(NE_FED_LO)),
          ("F3 fed n_e=1e8", h * 8.98e3 * math.sqrt(NE_FED_HI))]
C_lambda = 2 * math.pi * h / (hbar * LN2)
dense_rows = []
L_scalefree = []
for name, E in floors:
    nu = E / h
    lam = c / nu
    g1bit = eps_CMB / E
    b6 = 1e6 * E / eps_CMB
    b9 = 1e9 * E / eps_CMB
    Nlam6, Nlam9 = b6 / C_lambda, b9 / C_lambda
    L6, L9 = Nlam6 * lam, Nlam9 * lam
    Gmax1l = eps_CMB * C_lambda / E
    Lsf6 = 1e6 * h * c / (eps_CMB * C_lambda)
    Lsf9 = 1e9 * h * c / (eps_CMB * C_lambda)
    L_scalefree += [(L6, Lsf6), (L9, Lsf9)]
    dense_rows.append(dict(floor=name, nu_Hz=nu, E_J=E, lam_m=lam, gain_single_bit=g1bit,
                           b_req_1e6=b6, b_req_1e9=b9, C_lambda=C_lambda,
                           Nlambda_req_1e6=Nlam6, Nlambda_req_1e9=Nlam9,
                           packet_len_req_1e6_m=L6, packet_len_req_1e9_m=L9,
                           Gmax_onelambda=Gmax1l))
    print(f"{name}: nu={nu:.3e} Hz, E={E:.3e} J, lam={lam:.3e} m")
    print(f"   single-bit gain={g1bit:.3e}; b*(1e6)={b6:.3g}, b*(1e9)={b9:.3g} bits/carrier")
    print(f"   required packet: {Nlam6:.4g} lam ({L6:.4g} m) for 1e6; {Nlam9:.4g} lam ({L9:.4g} m) for 1e9")
    print(f"   max gain on one-wavelength packet: {Gmax1l:.3e}")
sf_dev = max(abs(a / b - 1) for a, b in L_scalefree)
check("dense-coding scale-free length", sf_dev < 1e-10,
      f"packet length independent of carrier floor: L(G*)=G*hc/(eps_CMB*C_lambda); max dev {sf_dev:.1e}")
L6_sf = 1e6 * h * c / (eps_CMB * C_lambda)
L9_sf = 1e9 * h * c / (eps_CMB * C_lambda)
print(f"C_lambda = 2pi h/(hbar ln2) = {C_lambda:.2f} bits per wavelength of coherent packet")
print(f"scale-free requirement: L(1e6)={L6_sf:.4g} m, L(1e9)={L9_sf:.4g} m")

mm_pellet = 1e-3
v_pellet = 1e5
R_pellet = 0.01
E_pellet = mm_pellet * c ** 2 + 0.5 * mm_pellet * v_pellet ** 2
I_pellet = 2 * math.pi * E_pellet * R_pellet / (hbar * c * LN2)
KE_pellet = 0.5 * mm_pellet * v_pellet ** 2
gain_pellet = eps_CMB * I_pellet / KE_pellet
print("")
print("matter fallback: 1 g pellet at 100 km/s, 1 cm: Bekenstein capacity "
      f"{I_pellet:.3e} bits (rest/kinetic energy ratio {mm_pellet*c**2/KE_pellet:.2e})")

# A-R8-02 / Bob A-F2: the capacity counts the pellet REST energy in its
# numerator, so charging only kinetic energy in the denominator is not a
# like-for-like accounting. Three chargings, all reported.
pellet_charges = [
    ("kinetic only (rest mass credited to the fuel account)", KE_pellet),
    ("accretion opportunity cost, eta = 0.30", 0.30 * mm_pellet * c ** 2 + KE_pellet),
    ("full rest energy (symmetric with the capacity numerator)", E_pellet),
]
pellet_rows = []
for label, cost in pellet_charges:
    gsel = eps_CMB * I_pellet / cost
    pellet_rows.append(dict(charging=label, cost_J=cost,
                            cost_per_bit_J=cost / I_pellet, realized_gain=gsel))
    print(f"   {label}: {cost/I_pellet:.3e} J/bit -> gain {gsel:.3g}")
print("   -> the 1e9 upper end rests on the kinetic-only charging; the")
print("      defensible matter-channel figure is the 74-250 band.")

# ---------------------------------------------------------------- A-R8-03: priced delivery budget
print("")
print("--- A-R8-03: delivery loss budget, fixed L, reported G ---")
# The scale-free length L(G) above is the length at which the packet SATURATES
# the Bekenstein bound: b_req/N_lambda = C_lambda exactly, at every carrier
# floor. There is no "modest fraction of capacity" anywhere in the range; what
# is modest is the length. Coding at a fraction f of capacity, or suffering
# delivery losses of the same size, multiplies the required length by 1/f.
def G_saturated(L_m):
    """Ideal (lossless, capacity-saturating) gain for coherence length L."""
    return L_m * C_lambda * eps_CMB / (h * c)


LOSS_SCENARIOS = [
    ("optimistic", dict(f_ecc=0.90, f_sink=0.90, f_reint=0.90, f_z=0.99)),
    ("conservative", dict(f_ecc=0.50, f_sink=0.30, f_reint=0.30, f_z=0.99)),
]
r_g_working = 1e2 * gA2["rg_m"]
budget_rows = []
for name, fl in LOSS_SCENARIOS:
    prod = fl["f_ecc"] * fl["f_sink"] * fl["f_reint"] * fl["f_z"]
    row = dict(scenario=name, factors=fl, throughput=prod,
               L_req_realized_1e6_m=(1e6 * h * c / (C_lambda * eps_CMB)) / prod,
               L_req_realized_1e9_m=(1e9 * h * c / (C_lambda * eps_CMB)) / prod,
               G_realized_at_L_100km=G_saturated(1e5) * prod)
    budget_rows.append(row)
    print(f"  {name:12s}: code rate {fl['f_ecc']}, capture {fl['f_sink']}, "
          f"swarm transmission {fl['f_reint']}, lapse {fl['f_z']} -> throughput {prod:.4f}")
    print(f"                coherence length for a realized 1e6: {row['L_req_realized_1e6_m']:.3g} m; "
          f"for a realized 1e9: {row['L_req_realized_1e9_m']:.3g} m")
    print(f"                G realized at a fixed L = 100 km: {row['G_realized_at_L_100km']:.3g}")
Lmax_req = max(r["L_req_realized_1e9_m"] for r in budget_rows)
check("G-A6 delivery budget inside the working boundary", Lmax_req < r_g_working,
      f"worst-case required coherence length {Lmax_req:.3g} m is "
      f"{r_g_working/Lmax_req:.0f}x smaller than the 1e2 r_g working boundary "
      f"({r_g_working:.3g} m); the 1e6-1e9 range survives priced losses")

json.dump(dict(
    meta=dict(wu="R7-CALC-AB", part="Paper A", date="2026-08-23",
              anchors=dict(harris=HARRIS, d_kpc=D_KPC, M_cl=M_CL, rc_amin=RC_AMIN, rh_amin=RH_AMIN)),
    king=dict(W0=W0, x_t=x_t, concentration=conc_model, r_c_pc=rc_pc, r_t_pc=rt_pc,
              rho_c=rho_c_true, df_amplitude=df_amp, m_tot_4pi=m_tot_4pi,
              half_mass=dict(model_pc=rh_model_pc, harris_scaled_pc=rh_harris_pc)),
    profile_checks=profile_checks,
    enclosed={str(r): dict(Msun=prof_mass[r], stars_at_043=prof_stars[r], eddington_yr=fuel_years[r],
                           density=None) for r in radii},
    curve=dict(r_pc=[round(rc_pc * x, 6) for x in xs[::40]],
               M_enc=[M_CL * frac(x) for x in xs[::40]]),
    depletion=dict(delivered=dM, profile_pct=dict(pc2=dep_prof_2, pc10=dep_prof_10),
                   printed_pct=dep_printed, adj_inversion=dep_adj,
                   star_counts_10pc=dict(at_043=prof_stars[10.0], lo_055=stars10_lo, hi_035=stars10_hi,
                                         printed="~1e6")),
    fuel=dict(t_edd_per_msun=t_edd, reservoir_years_1pc=fuel_years[1.0], reservoir_years_10pc=fuel_years[10.0]),
    spinup=dict(S1_reproduction_yr=t_S1, S1_growth_aware_yr=t_S1_growth,
                S2_strict_yr=t_S2, S2_int_eta_dlnm=int_eta_dlnm,
                S2_int_eta_geodesic=int_eta_geo, S2_m_at_cap=m_cap,
                S2_over_S1=t_S2 / t_S1,
                S1_mean_mass=mean_M,
                S2_a_end=a_end, growth=2.2024, efolds_ln=math.log(2.2024),
                stars=n_stars_spinup, rate_per_yr=rate,
                delivered_rest_mass_msun=m_rest_delivered,
                rest_over_hole_increment=m_rest_delivered / dM),
    tug_bracket=tug_rows,
    tug_vs_cluster_light=dict(L_V_Lsun=LV, rows=lightfrac_rows),
    headline_ratios=dict(rows=ratio_rows, eta=dict(schwarzschild=ETA_SCHW,
                                                   thorne=ETA_THORNE, formal_extremal=ETA_EXTREMAL),
                         spinup_payoff=ETA_THORNE / ETA_SCHW),
    storage_bits=dict(schwarzschild=bits_schw, kerr_998=0.53 * bits_schw),
    tug_exclusion_threshold_kms=dict(at_S1=ceiling*Lsun*(t_S1*yr)/(dM*Msun*c)/1e3,
                                     at_S2=dv_break),
    king_circular_speeds_kms={str(r): _vcirc(r) for r in radii},
    tug_rescale=dict(KE_printed_3e4=KE_printed, KE_at_2p4048e4=KE_new, Eph_at_2p4048e4=EP_new,
                     Lavg_Lsun=L_ke_new, Lphot_Lsun=L_ph_new, ratio_ceiling=ratio_new,
                     ceiling_Lsun=ceiling),
    gates=dict(G_A2=gA2, G_A4=gA4),
), open(os.path.join(HERE, "fA_calc7_profile.json"), "w"), indent=1)

json.dump(dict(
    meta=dict(wu="R7-CALC-AB", part="dense-coding budget", date="2026-08-23",
              eps_CMB_J_per_bit=eps_CMB, T_CMB=T_CMB, M_fid_msun=M_FID,
              capacity_law="I <= 2 pi E R /(hbar c ln2) [Bekenstein1981]; reference packet R=lambda=c/nu"),
    C_lambda_bits=C_lambda,
    floors=dense_rows,
    scale_free_length=dict(L_1e6_m=L6_sf, L_1e9_m=L9_sf, max_dev=sf_dev),
    matter_fallback=dict(bits=I_pellet, cost_J_per_bit=KE_pellet / I_pellet, realized_gain=gain_pellet,
                         chargings=pellet_rows),
    capacity_note=("the scale-free L(G) is the length at which the packet saturates the "
                   "Bekenstein bound; coding at a fraction f of capacity, or suffering "
                   "delivery losses of the same size, multiplies it by 1/f"),
    loss_budget=dict(rows=budget_rows, working_boundary_m=r_g_working),
), open(os.path.join(HERE, "fA_calc7_dense.json"), "w"), indent=1)

print("\n" + "=" * 72)
if failures:
    print("FAILURES:", failures)
    sys.exit(1)
print("all Paper A gates and computations complete")
