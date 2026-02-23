# =====================================================
# MODULE: weights.py
# Weight estimation and breakdown for BWB UAV
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg


def empty_weight_regression(mtow_kg: float) -> float:
    """
    Raymer statistical regression for jet UAV:
    W_empty = A × MTOW^B    [kg]
    """
    return cfg.RAYMER_A * (mtow_kg ** cfg.RAYMER_B)


def weight_breakdown(mtow_kg: float = cfg.MTOW,
                     fuel_kg: float  = cfg.FUEL_WEIGHT) -> dict:
    """
    Full weight breakdown [kg and N].
    Returns dict with all weight components.
    """
    W_empty   = empty_weight_regression(mtow_kg)
    W_fuel    = fuel_kg
    W_payload = mtow_kg - W_empty - W_fuel

    if W_payload < 0:
        raise ValueError(
            f"Negative payload ({W_payload:.2f} kg). "
            f"Check MTOW, fuel, or regression coefficients."
        )

    return {
        "MTOW_kg":      mtow_kg,
        "W_empty_kg":   W_empty,
        "W_fuel_kg":    W_fuel,
        "W_payload_kg": W_payload,
        "MTOW_N":       mtow_kg  * cfg.G,
        "W_empty_N":    W_empty  * cfg.G,
        "W_fuel_N":     W_fuel   * cfg.G,
        "W_payload_N":  W_payload * cfg.G,
        "empty_frac":   W_empty  / mtow_kg,
        "fuel_frac":    W_fuel   / mtow_kg,
        "payload_frac": W_payload / mtow_kg,
    }


def mission_weights(wb: dict) -> dict:
    """
    Compute weight at each mission segment start/end [N].
    Segment fractions from config.
    """
    W0 = wb["MTOW_N"]
    W1 = W0 * cfg.SEG_WARMUP_TAKEOFF      # after warmup/takeoff
    W2 = W1 * cfg.SEG_CLIMB               # after climb
    W3 = W2                                # cruise start (fuel burned via Breguet)
    W4 = wb["MTOW_N"] - wb["W_fuel_N"]    # after full fuel burn (Breguet end)
    W5 = W4 * cfg.SEG_DESCENT             # after descent
    W6 = W5 * cfg.SEG_LANDING             # after landing

    return {
        "W0_takeoff":    W0,
        "W1_after_to":   W1,
        "W2_top_climb":  W2,
        "W3_cruise_start": W3,
        "W4_cruise_end": W4,
        "W5_descent":    W5,
        "W6_landing":    W6,
        "W_avg_cruise_N": 0.5 * (W2 + W4),
    }


def centre_of_gravity(wb: dict, mac: float) -> dict:
    """
    CG estimation for BWB.
    Uses Raymer fraction estimates for each component.
    Returns CG as % MAC from leading edge.
    """
    # Component CG fractions of MAC (typical BWB estimates)
    cg_empty   = cfg.CG_FRACTION_MAC        # structural + avionics
    cg_fuel    = 0.28                        # fuel in centre body
    cg_payload = 0.25                        # payload forward of CG

    W_e = wb["W_empty_kg"]
    W_f = wb["W_fuel_kg"]
    W_p = wb["W_payload_kg"]
    W_total = W_e + W_f + W_p

    cg_frac = (W_e*cg_empty + W_f*cg_fuel + W_p*cg_payload) / W_total

    return {
        "CG_frac_MAC":  cg_frac,
        "CG_m_from_LE": cg_frac * mac,
        "NP_frac_MAC":  cfg.NP_FRACTION_MAC,
        "NP_m_from_LE": cfg.NP_FRACTION_MAC * mac,
        "static_margin_frac": cfg.NP_FRACTION_MAC - cg_frac,
        "static_margin_pct":  (cfg.NP_FRACTION_MAC - cg_frac) * 100,
    }


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    from geometry import wing_geometry
    geom = wing_geometry()
    wb   = weight_breakdown()
    mw   = mission_weights(wb)
    cg   = centre_of_gravity(wb, geom["mac"])

    print("\n=== WEIGHT BREAKDOWN ===")
    print(f"  MTOW      : {wb['MTOW_kg']:.2f} kg  ({wb['MTOW_N']:.1f} N)")
    print(f"  W_empty   : {wb['W_empty_kg']:.2f} kg  ({wb['empty_frac']*100:.1f}%)")
    print(f"  W_fuel    : {wb['W_fuel_kg']:.2f} kg  ({wb['fuel_frac']*100:.1f}%)")
    print(f"  W_payload : {wb['W_payload_kg']:.2f} kg  ({wb['payload_frac']*100:.1f}%)")

    print("\n=== MISSION WEIGHTS (N) ===")
    for k, v in mw.items():
        print(f"  {k:25s}: {v:.2f} N  ({v/cfg.G:.2f} kg)")

    print("\n=== CENTRE OF GRAVITY ===")
    print(f"  CG at     : {cg['CG_frac_MAC']*100:.1f}% MAC  ({cg['CG_m_from_LE']:.4f} m from LE)")
    print(f"  NP at     : {cg['NP_frac_MAC']*100:.1f}% MAC  ({cg['NP_m_from_LE']:.4f} m from LE)")
    sm = cg['static_margin_pct']
    flag = "✓" if 5 <= sm <= 15 else "⚠ CHECK"
    print(f"  Stat. margin: {sm:.1f}% MAC  {flag}  (BWB target: 5–15%)")
