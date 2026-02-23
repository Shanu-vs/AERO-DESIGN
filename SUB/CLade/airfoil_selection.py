# =====================================================
# MODULE: airfoil_selection.py
# Computes all airfoil selection parameters.
# Does NOT run NeuralFoil — that is airfoil_selector.py
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg
from atmosphere import from_ft


def run_airfoil_selection(verbose: bool = True) -> tuple:
    """
    Compute airfoil design parameters from first principles.

    Returns:
        results : dict  — all intermediate values
        chords  : dict  — wing geometry (span, mac, root/mid/tip chords)
        export  : dict  — values to pass directly to airfoil_selector.py
    """

    # --------------------------------------------------
    # ATMOSPHERE at cruise altitude
    # --------------------------------------------------
    atm        = from_ft(cfg.CRUISE_ALTITUDE)
    rho_cruise = atm["rho"]
    mu_cruise  = atm["mu"]

    # --------------------------------------------------
    # WEIGHTS
    # --------------------------------------------------
    W_to   = cfg.MTOW        * cfg.G
    W_fuel = cfg.FUEL_WEIGHT * cfg.G
    Wi     = W_to
    Wf     = W_to - W_fuel
    W_avg  = 0.5 * (Wi + Wf)

    # --------------------------------------------------
    # CONFIG CONSISTENCY CHECK
    # --------------------------------------------------
    CL_max_physical    = (2.0 * W_to) / (cfg.RHO_SL * cfg.STALL_SPEED**2 * cfg.WING_AREA)
    V_stall_from_clmax = math.sqrt((2.0 * W_to) / (cfg.RHO_SL * cfg.CL_MAX * cfg.WING_AREA))
    consistent = abs(CL_max_physical - cfg.CL_MAX) < 0.05

    if verbose:
        print("\n[CONFIG CONSISTENCY CHECK]")
        print(f"  STALL_SPEED = {cfg.STALL_SPEED:.2f} m/s  → CL_max = {CL_max_physical:.4f}")
        print(f"  CL_MAX      = {cfg.CL_MAX:.4f}       → V_stall = {V_stall_from_clmax:.2f} m/s")
        if not consistent:
            print(f"  ⚠ MISMATCH — using V_stall = {cfg.STALL_SPEED:.2f} m/s as ground truth")
            print(f"  => Update config: CL_MAX = {CL_max_physical:.4f}  OR  STALL_SPEED = {V_stall_from_clmax:.2f} m/s")
        else:
            print("  ✓ Consistent")

    # --------------------------------------------------
    # CRUISE CL CHAIN (Raymer / Gudmundsson)
    # --------------------------------------------------
    C_lc        = (2.0 * W_avg) / (rho_cruise * cfg.CRUISE_SPEED**2 * cfg.WING_AREA)
    C_lw        = C_lc  / 0.95      # fuselage lift carryover
    c_li        = C_lw  / 0.90      # finite span / sweep correction

    # --------------------------------------------------
    # CLmax CHAIN (from physical stall speed)
    # --------------------------------------------------
    C_Lmax      = CL_max_physical
    C_Lmax_w    = C_Lmax / 0.95
    c_lmax_gross= C_Lmax_w / 0.90
    c_lmax_net  = c_lmax_gross       # clean, no HLD (delta_cl = 0)

    # --------------------------------------------------
    # WING GEOMETRY
    # --------------------------------------------------
    b    = math.sqrt(cfg.ASPECT_RATIO * cfg.WING_AREA)
    mac  = cfg.WING_AREA / b
    c_root = mac * cfg.CHORD_RATIO_ROOT
    c_mid  = mac * cfg.CHORD_RATIO_MID
    c_tip  = mac * cfg.CHORD_RATIO_TIP

    chords = {
        "span":   b,
        "mac":    mac,
        "c_root": c_root,
        "c_mid":  c_mid,
        "c_tip":  c_tip,
    }

    # --------------------------------------------------
    # REYNOLDS NUMBERS PER SECTION
    # --------------------------------------------------
    def Re(c):
        return rho_cruise * cfg.CRUISE_SPEED * c / mu_cruise

    Re_mac  = Re(mac)
    Re_root = Re(c_root)
    Re_mid  = Re(c_mid)
    Re_tip  = Re(c_tip)

    # --------------------------------------------------
    # RESULTS DICT
    # --------------------------------------------------
    results = {
        "Cruise altitude (m)":          cfg.CRUISE_ALTITUDE * 0.3048,
        "Cruise density (kg/m³)":       rho_cruise,
        "Dynamic viscosity (Pa·s)":     mu_cruise,
        "Wingspan (m)":                 b,
        "MAC (m)":                      mac,
        "Root chord (m)":               c_root,
        "Mid  chord (m)":               c_mid,
        "Tip  chord (m)":               c_tip,
        "W_to (N)":                     W_to,
        "W_fuel (N)":                   W_fuel,
        "W_avg cruise (N)":             W_avg,
        "C_lc  — aircraft cruise CL":   C_lc,
        "C_lw  — wing cruise CL":       C_lw,
        "c_li  — airfoil ideal CL":     c_li,
        "CL_max (from stall speed)":    C_Lmax,
        "C_Lmax_w (wing)":              C_Lmax_w,
        "c_lmax_net (airfoil, clean)":  c_lmax_net,
        "Re — MAC":                     Re_mac,
        "Re — root":                    Re_root,
        "Re — mid":                     Re_mid,
        "Re — tip":                     Re_tip,
        "CL_MAX config":                cfg.CL_MAX,
        "CL_MAX physical":              CL_max_physical,
        "Config consistent":            consistent,
    }

    export = {
        "CL_CRUISE":  C_lc,
        "c_li":       c_li,
        "c_lmax_net": c_lmax_net,
        "Re_root":    Re_root,
        "Re_mid":     Re_mid,
        "Re_tip":     Re_tip,
        "rho_cruise": rho_cruise,
        "mu_cruise":  mu_cruise,
    }

    return results, chords, export


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    results, chords, export = run_airfoil_selection(verbose=True)

    print("\n====== AIRFOIL SELECTION PARAMETERS ======\n")
    for k, v in results.items():
        if isinstance(v, bool):
            print(f"  {k:40s}: {'Yes' if v else 'No'}")
        else:
            print(f"  {k:40s}: {v:.4f}")

    print("\n====== EXPORT TO airfoil_selector.py ======\n")
    for k, v in export.items():
        print(f"  {k:20s}: {v:.4e}" if isinstance(v, float) and v > 100
              else f"  {k:20s}: {v:.4f}")
