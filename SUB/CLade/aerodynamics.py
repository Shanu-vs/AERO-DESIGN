# =====================================================
# MODULE: aerodynamics.py
# Drag polar, lift coefficients, L/D, stall analysis
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg


def induced_drag_factor(AR: float = cfg.ASPECT_RATIO,
                        e: float  = cfg.OSWALD_EFF) -> float:
    """k = 1 / (π × AR × e)"""
    return 1.0 / (math.pi * AR * e)


def drag_polar(CL: float, k: float, CD0: float = cfg.CD0) -> float:
    """CD = CD0 + k × CL²"""
    return CD0 + k * CL**2


def lift_coefficient(W_N: float, rho: float, V: float,
                     S: float = cfg.WING_AREA) -> float:
    """CL = 2W / (rho × V² × S)"""
    return (2.0 * W_N) / (rho * V**2 * S)


def ld_ratio(CL: float, CD: float) -> float:
    return CL / CD if CD > 1e-9 else 0.0


def optimal_cl(CD0: float = cfg.CD0,
               AR: float  = cfg.ASPECT_RATIO,
               e: float   = cfg.OSWALD_EFF) -> dict:
    """
    CL for minimum drag (maximum L/D).
    CL_md = sqrt(CD0 / k)
    """
    k      = induced_drag_factor(AR, e)
    CL_md  = math.sqrt(CD0 / k)
    CD_md  = 2.0 * CD0                   # at CL_md, induced = parasite
    LD_max = CL_md / CD_md
    return {"k": k, "CL_md": CL_md, "CD_md": CD_md, "LD_max": LD_max}


def clmax_from_stall(W_N: float      = None,
                     rho_sl: float   = cfg.RHO_SL,
                     V_stall: float  = cfg.STALL_SPEED,
                     S: float        = cfg.WING_AREA) -> float:
    """
    CL_max derived from stall speed (ground truth).
    Overrides the config CL_MAX which may be inconsistent.
    """
    if W_N is None:
        W_N = cfg.MTOW * cfg.G
    return (2.0 * W_N) / (rho_sl * V_stall**2 * S)


def cruise_aero(W_N: float, rho: float = cfg.RHO_CRUISE,
                V: float   = cfg.CRUISE_SPEED,
                S: float   = cfg.WING_AREA) -> dict:
    """
    Full aerodynamic state at cruise condition.
    """
    k   = induced_drag_factor()
    CL  = lift_coefficient(W_N, rho, V, S)
    CD  = drag_polar(CL, k)
    LD  = ld_ratio(CL, CD)
    D   = 0.5 * rho * V**2 * S * CD   # drag [N]
    L   = 0.5 * rho * V**2 * S * CL   # lift [N]
    q   = 0.5 * rho * V**2             # dynamic pressure [Pa]

    return {
        "CL":   CL,
        "CD":   CD,
        "CD0":  cfg.CD0,
        "CDi":  k * CL**2,
        "k":    k,
        "LD":   LD,
        "L_N":  L,
        "D_N":  D,
        "q_Pa": q,
    }


def cl_chain_airfoil(W_N: float, W_fuel_N: float,
                     rho: float  = cfg.RHO_CRUISE,
                     V: float    = cfg.CRUISE_SPEED,
                     S: float    = cfg.WING_AREA) -> dict:
    """
    Lift coefficient chain from aircraft to airfoil section.
    Follows Raymer / Gudmundsson methodology:
      C_lc  = aircraft cruise CL at average weight
      C_lw  = wing CL (÷ 0.95 fuselage correction)
      c_li  = airfoil section ideal CL (÷ 0.90 span/sweep)

    CLmax chain:
      C_Lmax     = from stall speed
      C_Lmax_w   = ÷ 0.95
      c_lmax_net = ÷ 0.90  (clean, no HLD)
    """
    W_avg = 0.5 * (W_N + (W_N - W_fuel_N))
    C_lc  = (2.0 * W_avg) / (rho * V**2 * S)   # aircraft avg-weight CL
    C_lw  = C_lc  / 0.95
    c_li  = C_lw  / 0.90

    CL_max      = clmax_from_stall(W_N)
    C_Lmax_w    = CL_max / 0.95
    c_lmax_net  = C_Lmax_w / 0.90

    return {
        "C_lc":       C_lc,
        "C_lw":       C_lw,
        "c_li":       c_li,
        "CL_max":     CL_max,
        "C_Lmax_w":   C_Lmax_w,
        "c_lmax_net": c_lmax_net,
    }


def stall_check(config_clmax: float = cfg.CL_MAX,
                config_vstall: float = cfg.STALL_SPEED,
                W_N: float = None) -> dict:
    """
    Cross-check config CL_MAX vs STALL_SPEED.
    Returns physical values and flags any inconsistency.
    """
    if W_N is None:
        W_N = cfg.MTOW * cfg.G
    S   = cfg.WING_AREA

    CL_max_physical     = clmax_from_stall(W_N)
    V_stall_from_clmax  = math.sqrt(2.0 * W_N / (cfg.RHO_SL * config_clmax * S))
    consistent          = abs(CL_max_physical - config_clmax) < 0.05

    return {
        "CL_max_physical":    CL_max_physical,
        "CL_max_config":      config_clmax,
        "V_stall_config":     config_vstall,
        "V_stall_from_clmax": V_stall_from_clmax,
        "consistent":         consistent,
    }


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    from weights import weight_breakdown, mission_weights

    wb  = weight_breakdown()
    mw  = mission_weights(wb)
    opt = optimal_cl()
    cr  = cruise_aero(mw["W_avg_cruise_N"])
    clf = cl_chain_airfoil(wb["MTOW_N"], wb["W_fuel_N"])
    sc  = stall_check()

    print("\n=== AERODYNAMICS ===")
    print(f"  Induced drag factor k : {opt['k']:.5f}")
    print(f"  CL_md (best L/D)      : {opt['CL_md']:.4f}")
    print(f"  L/D max               : {opt['LD_max']:.2f}")
    print(f"  V for L/D max         : {math.sqrt(2*wb['MTOW_N']/(cfg.RHO_CRUISE*opt['CL_md']*cfg.WING_AREA)):.2f} m/s")

    print(f"\n  --- Cruise ({cfg.CRUISE_SPEED} m/s) ---")
    print(f"  CL  : {cr['CL']:.4f}")
    print(f"  CD  : {cr['CD']:.4f}  (CD0={cr['CD0']:.4f}  CDi={cr['CDi']:.4f})")
    print(f"  L/D : {cr['LD']:.2f}")
    print(f"  Drag: {cr['D_N']:.1f} N")
    print(f"  q   : {cr['q_Pa']:.1f} Pa")

    print(f"\n  --- Airfoil CL Chain ---")
    print(f"  C_lc (aircraft avg wt): {clf['C_lc']:.4f}")
    print(f"  C_lw (wing)           : {clf['C_lw']:.4f}")
    print(f"  c_li (airfoil target) : {clf['c_li']:.4f}")
    print(f"  CL_max (from Vstall)  : {clf['CL_max']:.4f}")
    print(f"  c_lmax_net (airfoil)  : {clf['c_lmax_net']:.4f}")

    print(f"\n  --- Config Consistency ---")
    cs = sc['consistent']
    print(f"  CL_max physical  : {sc['CL_max_physical']:.4f}  (from V_stall={cfg.STALL_SPEED} m/s)")
    print(f"  CL_max config    : {sc['CL_max_config']:.4f}  {'✓' if cs else '⚠ MISMATCH — use physical value'}")
    if not cs:
        print(f"  Fix config: CL_MAX = {sc['CL_max_physical']:.4f}  OR  STALL_SPEED = {sc['V_stall_from_clmax']:.2f} m/s")
