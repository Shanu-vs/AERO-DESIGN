# =====================================================
# BWB UAV — MASTER DESIGN REPORT
# =====================================================
# Entry point. Run this file to get the complete
# design analysis across all modules.
#
# Usage:
#   python main.py
#   python main.py --save        (save report to results/)
#   python main.py --csv         (also export CSV summary)
# =====================================================

import sys
import os
import math
import argparse
import datetime

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

import config          as cfg
from atmosphere        import from_ft
from geometry          import wing_geometry, reynolds_sections
from weights           import weight_breakdown, mission_weights, centre_of_gravity
from aerodynamics      import (cruise_aero, optimal_cl, cl_chain_airfoil,
                               clmax_from_stall, stall_check, induced_drag_factor)
from propulsion        import (thrust_required, thrust_margin, power_required,
                               breguet_range, breguet_endurance,
                               mission_fuel_analysis, tsfc_si)
from performance       import (takeoff_ground_roll, climb_performance,
                               service_ceiling, load_factors, glide_performance)
from stability         import (longitudinal_stability, lateral_stability,
                               control_surface_sizing)
from airfoil_selection import run_airfoil_selection


# =====================================================
# SEPARATOR HELPERS
# =====================================================
W = 68   # print width

def header(title: str):
    print("\n" + "=" * W)
    print(f"  {title}")
    print("=" * W)

def subheader(title: str):
    print(f"\n  ── {title} ──")

def row(label: str, value, unit: str = ""):
    val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
    print(f"  {label:38s}: {val_str} {unit}".rstrip())

def flag(ok: bool) -> str:
    return "✓" if ok else "⚠"


# =====================================================
# MAIN REPORT
# =====================================================
def generate_report(save: bool = False, csv_out: bool = False) -> dict:

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    # ─────────────────────────────────────────────────
    p("=" * W)
    p(f"  BWB UAV — COMPLETE DESIGN REPORT")
    p(f"  Generated: {ts}")
    p("=" * W)

    # ─────────────────────────────────────────────────
    # 1. ATMOSPHERE
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  1. ATMOSPHERE")
    p("─" * W)

    atm_sl = from_ft(0)
    atm_cr = from_ft(cfg.CRUISE_ALTITUDE)
    atm_mx = from_ft(6000)

    p(f"  {'Altitude':12s} | {'ρ (kg/m³)':10s} | {'T (K)':8s} | {'a (m/s)':9s} | {'μ (Pa·s)':12s}")
    p(f"  {'-'*12} | {'-'*10} | {'-'*8} | {'-'*9} | {'-'*12}")
    for label, atm in [("SL (0 ft)", atm_sl),
                        (f"Cruise ({cfg.CRUISE_ALTITUDE} ft)", atm_cr),
                        ("Max (6000 ft)", atm_mx)]:
        p(f"  {label:12s} | {atm['rho']:10.5f} | {atm['T_K']:8.2f} | {atm['a']:9.3f} | {atm['mu']:12.3e}")

    # ─────────────────────────────────────────────────
    # 2. GEOMETRY
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  2. WING GEOMETRY")
    p("─" * W)

    geom = wing_geometry()
    re   = reynolds_sections(geom, rho=atm_cr["rho"], mu=atm_cr["mu"])

    p(f"  Reference area S       : {geom['S']:.4f} m²")
    p(f"  Aspect ratio AR        : {geom['AR']:.2f}")
    p(f"  Wingspan b             : {geom['b']:.4f} m")
    p(f"  MAC                    : {geom['mac']:.4f} m")
    p(f"  Root chord             : {geom['c_root']:.4f} m  (0–{cfg.SPAN_ROOT_END*100:.0f}% span)")
    p(f"  Mid  chord             : {geom['c_mid']:.4f} m  ({cfg.SPAN_ROOT_END*100:.0f}–{cfg.SPAN_MID_END*100:.0f}% span)")
    p(f"  Tip  chord             : {geom['c_tip']:.4f} m  ({cfg.SPAN_MID_END*100:.0f}–100% span)")
    p(f"  Taper ratio            : {geom['taper']:.3f}")
    p(f"  LE sweep               : {geom['sweep_LE_deg']:.2f}°")
    p(f"  QC sweep               : {geom['sweep_QC_deg']:.2f}°")
    p(f"  Wetted area            : {geom['S_wet']:.4f} m²")
    p(f"  Twist Root / Mid / Tip : {geom['twist_root']:+.1f}° / {geom['twist_mid']:+.1f}° / {geom['twist_tip']:+.1f}°")
    p(f"\n  Reynolds numbers (cruise V = {cfg.CRUISE_SPEED} m/s):")
    p(f"    Root section : {re['Re_root']:.4e}  (chord {geom['c_root']:.3f} m)")
    p(f"    Mid  section : {re['Re_mid']:.4e}  (chord {geom['c_mid']:.3f} m)")
    p(f"    Tip  section : {re['Re_tip']:.4e}  (chord {geom['c_tip']:.3f} m)")

    # ─────────────────────────────────────────────────
    # 3. WEIGHTS
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  3. WEIGHT BREAKDOWN")
    p("─" * W)

    wb  = weight_breakdown()
    mw  = mission_weights(wb)
    cg  = centre_of_gravity(wb, geom["mac"])

    p(f"  MTOW           : {wb['MTOW_kg']:.2f} kg  ({wb['MTOW_N']:.1f} N)")
    p(f"  Empty weight   : {wb['W_empty_kg']:.2f} kg  ({wb['empty_frac']*100:.1f}%)  [Raymer regression]")
    p(f"  Fuel weight    : {wb['W_fuel_kg']:.2f} kg  ({wb['fuel_frac']*100:.1f}%)")
    p(f"  Payload        : {wb['W_payload_kg']:.2f} kg  ({wb['payload_frac']*100:.1f}%)")
    p(f"  Wing loading   : {wb['MTOW_N']/geom['S']:.2f} N/m²  =  {cfg.MTOW/geom['S']:.2f} kg/m²")

    p(f"\n  Mission weight stations:")
    p(f"    W0 (takeoff)          : {mw['W0_takeoff']/cfg.G:.2f} kg")
    p(f"    W2 (top of climb)     : {mw['W2_top_climb']/cfg.G:.2f} kg")
    p(f"    W4 (end of cruise)    : {mw['W4_cruise_end']/cfg.G:.2f} kg")
    p(f"    W6 (landing)          : {mw['W6_landing']/cfg.G:.2f} kg")
    p(f"    W_avg cruise          : {mw['W_avg_cruise_N']/cfg.G:.2f} kg")

    sm_f = flag(cg['static_margin_pct'] >= 5 and cg['static_margin_pct'] <= 15)
    p(f"\n  Centre of Gravity:")
    p(f"    CG location    : {cg['CG_frac_MAC']*100:.1f}% MAC  ({cg['CG_m_from_LE']:.4f} m from LE)")
    p(f"    NP location    : {cg['NP_frac_MAC']*100:.1f}% MAC  ({cg['NP_m_from_LE']:.4f} m from LE)")
    p(f"    Static margin  : {cg['static_margin_pct']:.1f}% MAC  {sm_f}  (target: 5–15%)")

    # ─────────────────────────────────────────────────
    # 4. AERODYNAMICS
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  4. AERODYNAMICS")
    p("─" * W)

    W_to  = wb["MTOW_N"]
    opt   = optimal_cl()
    cr    = cruise_aero(mw["W_avg_cruise_N"], rho=atm_cr["rho"])
    clf   = cl_chain_airfoil(W_to, wb["W_fuel_N"], rho=atm_cr["rho"])
    sc_   = stall_check()
    CLmax = clmax_from_stall(W_to)

    V_md  = math.sqrt(2.0 * mw["W_avg_cruise_N"] / (atm_cr["rho"] * opt["CL_md"] * geom["S"]))

    p(f"  Induced drag factor k  : {opt['k']:.5f}")
    p(f"  L/D max (theoretical)  : {opt['LD_max']:.2f}  at V = {V_md:.1f} m/s,  CL = {opt['CL_md']:.4f}")

    p(f"\n  Cruise condition (V = {cfg.CRUISE_SPEED} m/s, alt = {cfg.CRUISE_ALTITUDE} ft):")
    p(f"    CL                   : {cr['CL']:.4f}")
    p(f"    CD (total)           : {cr['CD']:.4f}  (CD0={cr['CD0']:.4f}  CDi={cr['CDi']:.4f})")
    p(f"    L/D                  : {cr['LD']:.2f}  (≠ L/D_max: cruise is faster than V_md)")
    p(f"    Lift                 : {cr['L_N']:.1f} N")
    p(f"    Drag                 : {cr['D_N']:.1f} N")
    p(f"    Dynamic pressure     : {cr['q_Pa']:.1f} Pa")

    p(f"\n  Airfoil CL chain (Raymer/Gudmundsson):")
    p(f"    C_lc (aircraft avg)  : {clf['C_lc']:.4f}  ← use for NeuralFoil matching")
    p(f"    C_lw (wing)          : {clf['C_lw']:.4f}  [÷ 0.95 fuselage correction]")
    p(f"    c_li (airfoil)       : {clf['c_li']:.4f}  [÷ 0.90 span/sweep correction]")

    clmax_flag = flag(sc_["consistent"])
    p(f"\n  CLmax / Stall check:")
    p(f"    CL_max (from Vstall) : {CLmax:.4f}  {clmax_flag}")
    p(f"    CL_MAX (config)      : {cfg.CL_MAX:.4f}")
    if not sc_["consistent"]:
        p(f"    ⚠ Fix config: CL_MAX = {sc_['CL_max_physical']:.4f}  OR  STALL_SPEED = {sc_['V_stall_from_clmax']:.2f} m/s")
    p(f"    c_lmax_net (airfoil) : {clf['c_lmax_net']:.4f}")

    # ─────────────────────────────────────────────────
    # 5. PROPULSION
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  5. PROPULSION & RANGE")
    p("─" * W)

    T_req = thrust_required(mw["W_avg_cruise_N"], cr["LD"])
    P_req = power_required(T_req, cfg.CRUISE_SPEED)
    TM    = thrust_margin(cfg.MAX_THRUST, T_req)
    R_max = breguet_range(cfg.CRUISE_SPEED, cr["LD"], W_to, W_to - wb["W_fuel_N"])
    E_max = breguet_endurance(opt["LD_max"], W_to, W_to - wb["W_fuel_N"])

    mfa   = mission_fuel_analysis(W_to, cr["LD"], opt["LD_max"])

    tm_flag = flag(TM >= 1.3)
    p(f"  Engine:")
    p(f"    Max thrust           : {cfg.MAX_THRUST:.1f} N")
    p(f"    TSFC                 : {cfg.TSFC:.3f} /hr  ({tsfc_si():.6f} /s)")
    p(f"    Thrust req (cruise)  : {T_req:.1f} N")
    p(f"    Thrust margin        : {TM:.2f}×  {tm_flag}  (target ≥ 1.3)")
    p(f"    Power req (cruise)   : {P_req/1000:.2f} kW")

    p(f"\n  Breguet performance (full fuel):")
    p(f"    Max range  (at Vcr)  : {R_max/1000:.1f} km")
    p(f"    Max endur  (at Vmd)  : {E_max/60:.1f} min")

    p(f"\n  Mission fuel budget  (cruise {mfa['t_cruise_min']:.0f} min + loiter {mfa['t_loiter_min']:.0f} min):")
    for seg, f_ in mfa["segment_fractions"].items():
        p(f"    {seg:20s}: Wf/Wi = {f_:.4f}  ({(1-f_)*100:.2f}% burned)")
    fuel_flag = flag(mfa["sufficient_fuel"])
    p(f"    Total Wf/Wi          : {mfa['W_ratio_total']:.4f}")
    p(f"    Fuel needed (+5% res): {mfa['W_fuel_needed_kg']:.2f} kg")
    p(f"    Fuel available       : {mfa['W_fuel_config_kg']:.2f} kg")
    p(f"    Fuel margin          : {mfa['fuel_margin_kg']:+.2f} kg  {fuel_flag}")

    # ─────────────────────────────────────────────────
    # 6. PERFORMANCE
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  6. FLIGHT PERFORMANCE")
    p("─" * W)

    to_  = takeoff_ground_roll(W_to, CLmax)
    cl_  = climb_performance(W_to, cr["LD"])
    sc_p = service_ceiling(W_to, opt["LD_max"], opt["CL_md"])
    lf_  = load_factors(CLmax)
    gl_  = glide_performance(opt["LD_max"])

    p(f"  Takeoff:")
    p(f"    V_stall              : {to_['V_stall']:.2f} m/s")
    p(f"    V_TO (1.2 Vs)        : {to_['V_TO']:.2f} m/s  ({to_['V_TO']*1.944:.1f} kts)")
    p(f"    STO ground roll      : {to_['STO_detailed']:.1f} m  (Raymer: {to_['STO_raymer']:.1f} m)")
    p(f"    Air distance (35 ft) : {to_['S_airborne']:.1f} m")
    p(f"    STO total (FAR)      : {to_['STO_total']:.1f} m  (config: {cfg.STO:.1f} m)")

    p(f"\n  Climb:")
    p(f"    Rate of climb        : {cl_['RC_m_s']:.2f} m/s  ({cl_['RC_fpm']:.0f} fpm)")
    p(f"    Climb angle          : {cl_['gamma_deg']:.2f}°")
    p(f"    T/W ratio            : {cl_['T_W']:.3f}")
    p(f"    Time to cruise alt   : {cl_['time_to_alt_min']:.1f} min")

    p(f"\n  Service ceiling:")
    p(f"    Ceiling (RC=0.5 m/s) : {sc_p['ceiling_ft']:.0f} ft  ({sc_p['ceiling_m']:.0f} m)")
    p(f"    V_md at ceiling      : {sc_p['V_md_ceiling']:.2f} m/s")

    p(f"\n  Load factors (V-n diagram):")
    p(f"    Wing loading W/S     : {lf_['WS_N_m2']:.1f} N/m²")
    p(f"    n design (+)         : {lf_['n_design']:.2f}")
    p(f"    n design (-)         : {lf_['n_design_neg']:.2f}")
    p(f"    V_A (manoeuvre)      : {lf_['V_A_m_s']:.2f} m/s  ({lf_['V_A_kts']:.1f} kts)")

    p(f"\n  Glide (engine-out):")
    p(f"    Best glide ratio     : {gl_['glide_ratio']:.1f}")
    p(f"    Best glide speed     : {gl_['V_best_glide']:.2f} m/s")
    p(f"    Sink rate            : {gl_['sink_rate_m_s']:.2f} m/s  ({gl_['sink_fpm']:.0f} fpm)")

    # ─────────────────────────────────────────────────
    # 7. STABILITY
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  7. STABILITY & CONTROL")
    p("─" * W)

    lon = longitudinal_stability(geom["mac"], wb)
    lat = lateral_stability(geom["b"], geom["mac"])
    cs  = control_surface_sizing(geom["mac"], geom["b"], geom["S"])

    sm_flag = flag(lon["stable"])
    p(f"  Longitudinal:")
    p(f"    NP location          : {lon['NP_frac']*100:.1f}% MAC  ({lon['NP_m_from_LE']:.4f} m)")
    p(f"    CG location          : {lon['CG_frac']*100:.1f}% MAC  ({lon['CG_m_from_LE']:.4f} m)")
    p(f"    Static margin        : {lon['SM_pct']:.1f}% MAC  {sm_flag}  (target: {lon['SM_target_min']:.0f}–{lon['SM_target_max']:.0f}%)")
    p(f"    CG shift (fuel burn) : {lon['CG_shift_fuel_m']*100:.1f} cm")

    rl_f = flag(lat["roll_stable"]); ya_f = flag(lat["yaw_stable"])
    p(f"\n  Lateral / Directional:")
    p(f"    Cl_beta (roll)       : {lat['Cl_beta_total']:.5f}  {rl_f}  (should be < 0)")
    p(f"    Cn_beta (yaw)        : {lat['Cn_beta']:.5f}  {ya_f}  (should be > 0, winglets needed)")
    p(f"    Sweep QC             : {lat['sweep_qc_deg']:.1f}°")

    p(f"\n  Elevon sizing:")
    p(f"    Span (each side)     : {cs['b_elevon_m']:.3f} m  ({cs['b_elevon_span_pct']:.0f}% half-span)")
    p(f"    Chord                : {cs['c_elevon_m']:.3f} m  ({cs['c_elevon_chord_pct']:.0f}% local chord)")
    p(f"    Area (each side)     : {cs['S_elevon_m2']:.4f} m²")
    p(f"    S_e / S_ref          : {cs['S_elevon_frac']*100:.1f}%")
    p(f"    Max deflection       : ±{cs['deflection_max_deg']:.0f}°")

    # ─────────────────────────────────────────────────
    # 8. AIRFOIL SELECTION PARAMETERS
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  8. AIRFOIL SELECTION PARAMETERS")
    p("─" * W)

    _, _, afs = run_airfoil_selection(verbose=False)

    p(f"  Design CL chain (input to airfoil_selector.py):")
    p(f"    CL_CRUISE (aircraft) : {afs['CL_CRUISE']:.4f}")
    p(f"    c_li (section target): {afs['c_li']:.4f}")
    p(f"    c_lmax_net           : {afs['c_lmax_net']:.4f}")
    p(f"\n  Reynolds numbers per section:")
    p(f"    Re root              : {afs['Re_root']:.4e}  (chord {geom['c_root']:.3f} m)")
    p(f"    Re mid               : {afs['Re_mid']:.4e}  (chord {geom['c_mid']:.3f} m)")
    p(f"    Re tip               : {afs['Re_tip']:.4e}  (chord {geom['c_tip']:.3f} m)")
    p(f"\n  Run airfoil_selector.py to evaluate .dat files from SUB/Airfoil/Data/")

    # ─────────────────────────────────────────────────
    # 9. DESIGN SUMMARY / HEALTH CHECK
    # ─────────────────────────────────────────────────
    p("\n" + "─" * W)
    p("  9. DESIGN HEALTH CHECK")
    p("─" * W)

    checks = [
        ("Weight closure",      abs(wb["W_empty_kg"]+wb["W_fuel_kg"]+wb["W_payload_kg"] - cfg.MTOW) < 0.01, ""),
        ("Payload > 0",         wb["W_payload_kg"] > 0,                f"{wb['W_payload_kg']:.2f} kg"),
        ("Thrust margin ≥ 1.3", TM >= 1.3,                             f"{TM:.2f}×"),
        ("Static margin 5–15%", 5 <= lon["SM_pct"] <= 15,              f"{lon['SM_pct']:.1f}%"),
        ("Fuel sufficient",     mfa["sufficient_fuel"],                 f"margin {mfa['fuel_margin_kg']:+.2f} kg"),
        ("CL_MAX consistent",   sc_["consistent"],                      f"CL_max={CLmax:.4f}"),
        ("Roll stable (Cl_β<0)",lat["roll_stable"],                    f"Cl_β={lat['Cl_beta_total']:.4f}"),
        ("Yaw stable (Cn_β>0)", lat["yaw_stable"],                     f"Cn_β={lat['Cn_beta']:.4f}"),
        ("Service ceil ≥ 6000 ft",sc_p["ceiling_ft"] >= 6000,          f"{sc_p['ceiling_ft']:.0f} ft"),
        ("ROC > 2 m/s",         cl_["RC_m_s"] > 2.0,                   f"{cl_['RC_m_s']:.2f} m/s"),
    ]

    all_pass = True
    for label, ok, detail in checks:
        sym = "  ✓" if ok else "  ⚠"
        if not ok:
            all_pass = False
        extra = f"  [{detail}]" if detail else ""
        p(f"  {sym}  {label:35s}{extra}")

    p()
    if all_pass:
        p("  ✓ All checks PASSED — design is internally consistent.")
    else:
        p("  ⚠ Some checks FAILED — review flagged items above.")

    p("\n" + "=" * W)
    p(f"  END OF REPORT — {ts}")
    p("=" * W)

    # ─────────────────────────────────────────────────
    # SAVE
    # ─────────────────────────────────────────────────
    if save:
        os.makedirs(cfg.RESULTS_DIR, exist_ok=True)
        fname = os.path.join(cfg.RESULTS_DIR,
                             f"design_report_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt")
        with open(fname, "w") as fh:
            fh.write("\n".join(lines))
        print(f"\n  Report saved → {fname}")

    if csv_out:
        import csv
        fname_csv = os.path.join(cfg.RESULTS_DIR,
                                 f"design_summary_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv")
        summary = [
            ["Parameter", "Value", "Unit"],
            ["MTOW",              cfg.MTOW,                     "kg"],
            ["W_empty",           wb["W_empty_kg"],              "kg"],
            ["W_fuel",            wb["W_fuel_kg"],               "kg"],
            ["W_payload",         wb["W_payload_kg"],            "kg"],
            ["Wingspan",          geom["b"],                     "m"],
            ["MAC",               geom["mac"],                   "m"],
            ["Wing loading",      wb["MTOW_N"]/geom["S"],        "N/m2"],
            ["CL cruise",         cr["CL"],                      "-"],
            ["CD cruise",         cr["CD"],                      "-"],
            ["L/D cruise",        cr["LD"],                      "-"],
            ["L/D max",           opt["LD_max"],                 "-"],
            ["Thrust req",        T_req,                         "N"],
            ["Thrust margin",     TM,                            "x"],
            ["Breguet range",     R_max/1000,                    "km"],
            ["Breguet endurance", E_max/60,                      "min"],
            ["STO",               to_["STO_total"],              "m"],
            ["ROC",               cl_["RC_m_s"],                 "m/s"],
            ["Service ceiling",   sc_p["ceiling_ft"],            "ft"],
            ["Static margin",     lon["SM_pct"],                 "% MAC"],
            ["Fuel needed",       mfa["W_fuel_needed_kg"],       "kg"],
        ]
        with open(fname_csv, "w", newline="") as fh:
            csv.writer(fh).writerows(summary)
        print(f"  CSV saved → {fname_csv}")

    return {
        "geometry":    geom,
        "weights":     wb,
        "aero":        cr,
        "propulsion":  mfa,
        "performance": {"to": to_, "climb": cl_, "ceiling": sc_p},
        "stability":   {"lon": lon, "lat": lat},
        "airfoil":     afs,
    }


# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BWB UAV Design Report")
    parser.add_argument("--save", action="store_true", help="Save report to results/")
    parser.add_argument("--csv",  action="store_true", help="Export CSV summary")
    args = parser.parse_args()

    generate_report(save=args.save, csv_out=args.csv)
