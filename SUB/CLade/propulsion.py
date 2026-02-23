# =====================================================
# MODULE: propulsion.py
# Thrust, TSFC, Breguet, mission fuel analysis
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg


def tsfc_si(tsfc_per_hr: float = cfg.TSFC) -> float:
    """Convert TSFC from 1/hr to SI units (1/s)."""
    return tsfc_per_hr / 3600.0


def thrust_required(W_N: float, LD: float) -> float:
    """Cruise thrust required T = W / (L/D)  [N]"""
    return W_N / LD


def thrust_margin(T_available: float, T_required: float) -> float:
    return T_available / T_required


def power_required(T_req: float, V: float) -> float:
    """Shaft power  P = T × V  [W]"""
    return T_req * V


# -------------------------------------------------------
# BREGUET EQUATIONS
# -------------------------------------------------------

def breguet_range(V: float, LD: float, W_i: float, W_f: float,
                  tsfc_hr: float = cfg.TSFC) -> float:
    """
    Breguet range equation [m].
    R = (V / c) × (L/D) × ln(Wi/Wf)
    c in 1/s, V in m/s
    """
    c = tsfc_si(tsfc_hr)
    return (V / c) * LD * math.log(W_i / W_f)


def breguet_endurance(LD: float, W_i: float, W_f: float,
                      tsfc_hr: float = cfg.TSFC) -> float:
    """
    Breguet endurance equation [s].
    E = (L/D) / c × ln(Wi/Wf)
    """
    c = tsfc_si(tsfc_hr)
    return (LD / c) * math.log(W_i / W_f)


def cruise_weight_fraction(V: float, t_s: float, LD: float,
                           tsfc_hr: float = cfg.TSFC) -> float:
    """
    Weight fraction Wf/Wi for a cruise segment of duration t_s [s].
    Wf/Wi = exp(-V × t × c / LD)
    """
    c = tsfc_si(tsfc_hr)
    return math.exp(-V * t_s * c / LD)


def loiter_weight_fraction(t_s: float, LD: float,
                           tsfc_hr: float = cfg.TSFC) -> float:
    """
    Weight fraction for loiter (endurance) segment.
    Wf/Wi = exp(-c × t / LD)
    """
    c = tsfc_si(tsfc_hr)
    return math.exp(-c * t_s / LD)


# -------------------------------------------------------
# MISSION FUEL ANALYSIS
# -------------------------------------------------------

def mission_fuel_analysis(W_to: float, LD_cruise: float, LD_loiter: float,
                           V_cruise: float = cfg.CRUISE_SPEED) -> dict:
    """
    Full mission fuel budget.

    Mission profile:
    ─────────────────────────────────────────────────────────
    Seg 0: Warmup + Takeoff  (fraction = SEG_WARMUP_TAKEOFF)
    Seg 1: Climb             (fraction = SEG_CLIMB)
    Seg 2: Cruise            (Breguet, 40 min transit)
    Seg 3: Loiter            (Breguet endurance, 5 min)
    Seg 4: Descent           (fraction = SEG_DESCENT)
    Seg 5: Landing           (fraction = SEG_LANDING)
    ─────────────────────────────────────────────────────────
    Note: Total mission = 45 min. The split cruise/loiter reflects
    that the UAV transits at high speed then loiters at optimal L/D.
    """
    # Segment fractions (non-Breguet)
    f_wto  = cfg.SEG_WARMUP_TAKEOFF
    f_cl   = cfg.SEG_CLIMB
    f_de   = cfg.SEG_DESCENT
    f_la   = cfg.SEG_LANDING

    # Time split: 40 min cruise + 5 min loiter
    t_cruise = (cfg.MISSION_TIME - cfg.LOITER_TIME)
    t_loiter = cfg.LOITER_TIME

    # Breguet weight fractions
    f_cruise = cruise_weight_fraction(V_cruise, t_cruise, LD_cruise)
    f_loiter = loiter_weight_fraction(t_loiter, LD_loiter)

    # Combined fraction
    W_ratio_total = f_wto * f_cl * f_cruise * f_loiter * f_de * f_la

    # Fuel fraction (without reserve)
    fuel_frac_used = 1.0 - W_ratio_total

    # With reserve
    fuel_frac_total = fuel_frac_used / (1.0 - cfg.RESERVE_FRACTION)

    # Actual fuel weights
    W_fuel_used_N  = W_to * fuel_frac_used
    W_fuel_total_N = W_to * fuel_frac_total
    W_fuel_config  = cfg.FUEL_WEIGHT * cfg.G

    # Per-segment breakdown
    segs = {
        "Warmup/Takeoff": f_wto,
        "Climb":          f_cl,
        "Cruise":         f_cruise,
        "Loiter":         f_loiter,
        "Descent":        f_de,
        "Landing":        f_la,
    }

    return {
        "segment_fractions":  segs,
        "W_ratio_total":      W_ratio_total,
        "fuel_frac_mission":  fuel_frac_used,
        "fuel_frac_with_res": fuel_frac_total,
        "W_fuel_needed_N":    W_fuel_total_N,
        "W_fuel_needed_kg":   W_fuel_total_N / cfg.G,
        "W_fuel_config_kg":   W_fuel_config  / cfg.G,
        "fuel_margin_kg":     cfg.FUEL_WEIGHT - W_fuel_total_N / cfg.G,
        "t_cruise_min":       t_cruise / 60,
        "t_loiter_min":       t_loiter / 60,
        "sufficient_fuel":    cfg.FUEL_WEIGHT >= W_fuel_total_N / cfg.G,
    }


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    from weights import weight_breakdown, mission_weights
    from aerodynamics import cruise_aero, optimal_cl

    wb  = weight_breakdown()
    mw  = mission_weights(wb)
    cr  = cruise_aero(mw["W_avg_cruise_N"])
    opt = optimal_cl()

    LD_cruise = cr["LD"]
    LD_loiter = opt["LD_max"]         # fly at V_md for best endurance

    T_req = thrust_required(mw["W_avg_cruise_N"], LD_cruise)
    P_req = power_required(T_req, cfg.CRUISE_SPEED)
    R_max = breguet_range(cfg.CRUISE_SPEED, LD_cruise, wb["MTOW_N"],
                          wb["MTOW_N"] - wb["W_fuel_N"])
    E_max = breguet_endurance(LD_loiter, wb["MTOW_N"],
                              wb["MTOW_N"] - wb["W_fuel_N"])

    mfa = mission_fuel_analysis(wb["MTOW_N"], LD_cruise, LD_loiter)

    print("\n=== PROPULSION ===")
    print(f"  Thrust required (cruise) : {T_req:.1f} N")
    print(f"  Max thrust               : {cfg.MAX_THRUST:.1f} N")
    print(f"  Thrust margin            : {thrust_margin(cfg.MAX_THRUST, T_req):.2f}×")
    print(f"  Power required           : {P_req/1000:.2f} kW")
    print(f"  TSFC                     : {cfg.TSFC:.3f} /hr  ({tsfc_si():.6f} /s)")

    print(f"\n=== BREGUET PERFORMANCE ===")
    print(f"  Max range  (at V_cr, full fuel) : {R_max/1000:.1f} km")
    print(f"  Max endur  (at V_md, full fuel) : {E_max/60:.1f} min")

    print(f"\n=== MISSION FUEL BUDGET ===")
    print(f"  Cruise {mfa['t_cruise_min']:.0f} min | Loiter {mfa['t_loiter_min']:.0f} min")
    print(f"  Segment weight fractions:")
    for seg, f in mfa["segment_fractions"].items():
        fuel_pct = (1 - f) * 100
        print(f"    {seg:20s}: Wf/Wi = {f:.4f}  ({fuel_pct:.2f}% burned)")
    print(f"  Total Wf/Wi              : {mfa['W_ratio_total']:.4f}")
    print(f"  Fuel needed (+ reserve)  : {mfa['W_fuel_needed_kg']:.2f} kg")
    print(f"  Fuel available           : {mfa['W_fuel_config_kg']:.2f} kg")
    print(f"  Fuel margin              : {mfa['fuel_margin_kg']:+.2f} kg")
    flag = "✓" if mfa["sufficient_fuel"] else "⚠ INSUFFICIENT FUEL"
    print(f"  Status                   : {flag}")
