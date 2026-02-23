# =====================================================
# MODULE: stability.py
# Longitudinal & lateral stability for tailless BWB
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg


def longitudinal_stability(mac: float, W_kg: dict) -> dict:
    """
    Longitudinal static stability for tailless BWB.

    For a tailless aircraft, stability requires:
      1. Pitching moment Cm0 < 0 (or = 0) at zero lift
      2. dCm/dCL < 0  (restoring moment with AoA)
      3. Static margin SM = (NP - CG) / MAC > 0  (NP ahead of CG → unstable)
         For BWB: SM = 5–15% MAC is target
    """
    NP_frac = cfg.NP_FRACTION_MAC
    CG_frac = cfg.CG_FRACTION_MAC

    SM_frac = NP_frac - CG_frac
    SM_pct  = SM_frac * 100.0

    NP_m = NP_frac * mac
    CG_m = CG_frac * mac

    # Component CG breakdown
    W_e  = W_kg.get("W_empty_kg", 0)
    W_f  = W_kg.get("W_fuel_kg",  0)
    W_p  = W_kg.get("W_payload_kg", 0)

    cg_e = cfg.CG_FRACTION_MAC         # structural
    cg_f = 0.28                         # fuel in centre body
    cg_p = 0.25                         # payload

    W_total = W_e + W_f + W_p
    CG_actual = (W_e*cg_e + W_f*cg_f + W_p*cg_p) / W_total if W_total > 0 else CG_frac

    SM_actual = NP_frac - CG_actual

    # Fuel-burned CG shift
    # As fuel burns: CG_frac shifts from fuel CG toward structural CG
    CG_empty = (W_e*cg_e + W_p*cg_p) / (W_e + W_p) if (W_e+W_p) > 0 else cg_e
    CG_shift  = abs(CG_actual - CG_empty) * mac   # [m]

    stable = SM_actual > 0.05  # require > 5% margin

    return {
        "NP_frac":       NP_frac,
        "CG_frac":       CG_actual,
        "CG_m_from_LE":  CG_actual * mac,
        "NP_m_from_LE":  NP_m,
        "SM_frac":       SM_actual,
        "SM_pct":        SM_actual * 100.0,
        "SM_target_min": 5.0,
        "SM_target_max": 15.0,
        "stable":        stable,
        "CG_shift_fuel_m":CG_shift,
    }


def lateral_stability(b: float, mac: float) -> dict:
    """
    Lateral (roll) stability estimates for BWB.
    Dihedral effect, sweep contribution.
    """
    sweep_qc_rad = math.radians(25.0)   # typical BWB quarter-chord sweep
    AR = cfg.ASPECT_RATIO

    # Lateral stability derivative Cl_beta (roll due to sideslip)
    # Dihedral effect: Cl_beta_dihedral ~ -0.0001 × AR × dihedral (per deg)
    Gamma_deg   = 0.0    # zero geometric dihedral (BWB uses sweep)
    Cl_b_dihed  = -0.0001 * AR * Gamma_deg

    # Sweep contribution to Cl_beta (Raymer Eq. 16.35 simplified)
    Cl_b_sweep  = -0.0005 * math.degrees(sweep_qc_rad) * AR / (AR + 4)

    Cl_beta_total = Cl_b_dihed + Cl_b_sweep

    # Directional stability Cn_beta (yaw stability)
    # For BWB without vertical tail: Cn_beta ≈ 0 → need winglets or elevons
    Cn_beta = 0.001 * AR * (1.0 / math.cos(sweep_qc_rad))  # rough estimate with winglets

    return {
        "sweep_qc_deg":   math.degrees(sweep_qc_rad),
        "dihedral_deg":   Gamma_deg,
        "Cl_beta_dihedral": Cl_b_dihed,
        "Cl_beta_sweep":    Cl_b_sweep,
        "Cl_beta_total":    Cl_beta_total,
        "Cn_beta":          Cn_beta,
        "roll_stable":      Cl_beta_total < 0,    # should be negative
        "yaw_stable":       Cn_beta > 0,           # should be positive
    }


def control_surface_sizing(mac: float, b: float, S: float) -> dict:
    """
    Elevon sizing for BWB tailless control.
    Elevons provide both pitch and roll control.
    Based on Raymer guidelines for tailless aircraft.
    """
    # Elevon span: typically 30–40% of half-span on outer panel
    b_elev   = 0.35 * (b / 2)        # elevon span (each side)

    # Elevon chord: 20–30% of local chord
    c_e_frac = 0.25
    c_e_root = mac * cfg.CHORD_RATIO_TIP * c_e_frac   # at tip section
    c_e_mac  = mac * c_e_frac

    S_elevon = b_elev * c_e_mac      # elevon area (one side)
    S_e_frac = (2 * S_elevon) / S    # both sides / ref area

    return {
        "b_elevon_m":     b_elev,
        "c_elevon_m":     c_e_mac,
        "S_elevon_m2":    S_elevon,
        "S_elevon_frac":  S_e_frac,
        "b_elevon_span_pct": (b_elev / (b/2)) * 100,
        "c_elevon_chord_pct": c_e_frac * 100,
        "deflection_max_deg": 25.0,   # ±25° typical
    }


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    from geometry import wing_geometry
    from weights  import weight_breakdown

    wb   = weight_breakdown()
    geom = wing_geometry()

    lon  = longitudinal_stability(geom["mac"], wb)
    lat  = lateral_stability(geom["b"], geom["mac"])
    cs   = control_surface_sizing(geom["mac"], geom["b"], geom["S"])

    print("\n=== LONGITUDINAL STABILITY ===")
    sm = lon['SM_pct']
    flag = "✓" if lon['stable'] else "⚠ INSUFFICIENT MARGIN"
    print(f"  NP at          : {lon['NP_frac']*100:.1f}% MAC  ({lon['NP_m_from_LE']:.4f} m from LE)")
    print(f"  CG at          : {lon['CG_frac']*100:.1f}% MAC  ({lon['CG_m_from_LE']:.4f} m from LE)")
    print(f"  Static margin  : {sm:.1f}% MAC  {flag}")
    print(f"  Target SM      : {lon['SM_target_min']:.0f}–{lon['SM_target_max']:.0f}% MAC")
    print(f"  CG shift (fuel): {lon['CG_shift_fuel_m']*100:.1f} cm")

    print("\n=== LATERAL STABILITY ===")
    print(f"  Sweep QC       : {lat['sweep_qc_deg']:.1f}°")
    print(f"  Cl_beta total  : {lat['Cl_beta_total']:.5f}  {'✓ stable' if lat['roll_stable'] else '⚠'}")
    print(f"  Cn_beta        : {lat['Cn_beta']:.5f}  {'✓ stable' if lat['yaw_stable'] else '⚠ Needs winglets'}")

    print("\n=== ELEVON SIZING ===")
    print(f"  Elevon span    : {cs['b_elevon_m']:.3f} m  ({cs['b_elevon_span_pct']:.0f}% half-span)")
    print(f"  Elevon chord   : {cs['c_elevon_m']:.3f} m  ({cs['c_elevon_chord_pct']:.0f}% local chord)")
    print(f"  Elevon area    : {cs['S_elevon_m2']:.4f} m² each side")
    print(f"  S_e / S_ref    : {cs['S_elevon_frac']*100:.1f}%")
    print(f"  Max deflection : ±{cs['deflection_max_deg']:.0f}°")
