# =====================================================
# MODULE: geometry.py
# Wing and planform geometry for BWB UAV
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg


def wing_geometry(S: float = cfg.WING_AREA,
                  AR: float = cfg.ASPECT_RATIO) -> dict:
    """
    Compute all primary wing geometry parameters.
    BWB planform approximated as trapezoidal with taper ratio ~0.2.
    """
    b   = math.sqrt(AR * S)         # span [m]
    mac = S / b                     # mean aerodynamic chord [m]

    # Section chord estimates (BWB taper approximation)
    c_root = mac * cfg.CHORD_RATIO_ROOT
    c_mid  = mac * cfg.CHORD_RATIO_MID
    c_tip  = mac * cfg.CHORD_RATIO_TIP

    # Taper ratio (tip/root)
    taper = c_tip / c_root

    # Span stations [m from centreline]
    y_root_end = (cfg.SPAN_ROOT_END) * (b / 2)
    y_mid_end  = (cfg.SPAN_MID_END)  * (b / 2)
    y_tip      = b / 2

    # Leading edge sweep (from MAC and planform — simplified for BWB)
    # Assuming leading edge sweep derived from trapezoidal approximation
    # LE sweep = atan((c_root - c_tip) / (2 * b/2)) — for unswept MAC line
    sweep_LE_rad = math.atan((c_root - c_tip) / b)
    sweep_LE_deg = math.degrees(sweep_LE_rad)

    # Quarter-chord sweep (Raymer Eq.)
    sweep_QC_deg = sweep_LE_deg - math.degrees(math.atan(
        0.25 * (c_root - c_tip) / (b / 2)
    ))

    # Dihedral (typical for BWB winglet approach — use 0 for base)
    dihedral_deg = 0.0

    # Wetted area estimate (both surfaces, BWB integration)
    S_wet = 2.0 * S * 1.07   # ~7% increase for thickness

    return {
        "S":             S,
        "AR":            AR,
        "b":             b,
        "mac":           mac,
        "c_root":        c_root,
        "c_mid":         c_mid,
        "c_tip":         c_tip,
        "taper":         taper,
        "y_root_end":    y_root_end,
        "y_mid_end":     y_mid_end,
        "y_tip":         y_tip,
        "sweep_LE_deg":  sweep_LE_deg,
        "sweep_QC_deg":  sweep_QC_deg,
        "dihedral_deg":  dihedral_deg,
        "S_wet":         S_wet,
        "twist_root":    cfg.TWIST_ROOT_DEG,
        "twist_mid":     cfg.TWIST_MID_DEG,
        "twist_tip":     cfg.TWIST_TIP_DEG,
    }


def reynolds_sections(geom: dict,
                      rho: float  = cfg.RHO_CRUISE,
                      V: float    = cfg.CRUISE_SPEED,
                      mu: float   = cfg.MU_CRUISE) -> dict:
    """
    Reynolds number at root, mid, and tip chord stations.
    """
    def Re(c):
        return rho * V * c / mu

    return {
        "Re_root": Re(geom["c_root"]),
        "Re_mid":  Re(geom["c_mid"]),
        "Re_tip":  Re(geom["c_tip"]),
        "Re_mac":  Re(geom["mac"]),
    }


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    g = wing_geometry()
    r = reynolds_sections(g)

    print("\n=== WING GEOMETRY ===")
    print(f"  Reference area S : {g['S']:.4f} m²")
    print(f"  Aspect ratio AR  : {g['AR']:.2f}")
    print(f"  Span b           : {g['b']:.4f} m")
    print(f"  MAC              : {g['mac']:.4f} m")
    print(f"  Root chord       : {g['c_root']:.4f} m  (0–{cfg.SPAN_ROOT_END*100:.0f}% span)")
    print(f"  Mid  chord       : {g['c_mid']:.4f} m  ({cfg.SPAN_ROOT_END*100:.0f}–{cfg.SPAN_MID_END*100:.0f}% span)")
    print(f"  Tip  chord       : {g['c_tip']:.4f} m  ({cfg.SPAN_MID_END*100:.0f}–100% span)")
    print(f"  Taper ratio      : {g['taper']:.3f}")
    print(f"  LE sweep         : {g['sweep_LE_deg']:.2f}°")
    print(f"  QC sweep         : {g['sweep_QC_deg']:.2f}°")
    print(f"  Wetted area      : {g['S_wet']:.4f} m²")
    print(f"  Twist Root/Mid/Tip: {g['twist_root']:+.1f}° / {g['twist_mid']:+.1f}° / {g['twist_tip']:+.1f}°")

    print("\n=== REYNOLDS NUMBERS ===")
    print(f"  Re root : {r['Re_root']:.4e}  (chord {g['c_root']:.3f} m)")
    print(f"  Re mid  : {r['Re_mid']:.4e}  (chord {g['c_mid']:.3f} m)")
    print(f"  Re tip  : {r['Re_tip']:.4e}  (chord {g['c_tip']:.3f} m)")
    print(f"  Re MAC  : {r['Re_mac']:.4e}  (chord {g['mac']:.3f} m)")
