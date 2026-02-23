# =====================================================
# MODULE: performance.py
# Takeoff, climb, service ceiling, landing
# =====================================================

import math
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config as cfg
from atmosphere import from_ft, isa_properties


def takeoff_ground_roll(W_N: float, CL_max: float,
                        T: float    = cfg.MAX_THRUST,
                        rho: float  = cfg.RHO_SL,
                        S: float    = cfg.WING_AREA,
                        mu_roll: float = 0.04) -> dict:
    """
    Takeoff ground roll — Raymer simplified method.
    STO = 1.21 × W² / (g × rho × S × CL_max × T_avg)
    V_TO = 1.2 × V_stall
    """
    V_stall = cfg.STALL_SPEED
    V_TO    = 1.2 * V_stall
    V_avg   = 0.7 * V_TO              # average speed during ground roll

    # Raymer ground roll
    STO = (1.21 * W_N**2) / (cfg.G * rho * S * CL_max * T)

    # More detailed method (balanced)
    # Account for rolling friction
    CL_TO = 2.0 * W_N / (rho * V_TO**2 * S)
    CD_TO = cfg.CD0 + (1.0 / (math.pi * cfg.ASPECT_RATIO * cfg.OSWALD_EFF)) * CL_TO**2
    D_avg = 0.5 * rho * V_avg**2 * S * CD_TO
    F_avg = T - D_avg - mu_roll * (W_N - 0.5 * rho * V_avg**2 * S * CL_TO)
    STO_detailed = W_N * V_TO**2 / (2.0 * cfg.G * F_avg)

    # Obstacle clearance (35 ft / 10.7 m)
    theta = math.asin((T - W_N/15) / W_N) if T > W_N/15 else 0.01  # climb angle
    R_cl  = V_TO**2 / (cfg.G * 0.2)                                  # rotation radius
    h_obs = 10.7                                                       # m (35 ft)
    s_air = math.sqrt(R_cl**2 - (R_cl - h_obs)**2) if R_cl > h_obs else 30.0

    return {
        "V_stall":       V_stall,
        "V_TO":          V_TO,
        "CL_TO":         CL_TO,
        "STO_raymer":    STO,
        "STO_detailed":  STO_detailed,
        "STO_config":    cfg.STO,
        "S_airborne":    s_air,
        "STO_total":     STO_detailed + s_air,
    }


def climb_performance(W_N: float, LD: float,
                      T: float   = cfg.MAX_THRUST,
                      V: float   = cfg.CRUISE_SPEED) -> dict:
    """
    Rate of climb and climb angle at given speed.
    RC = (T×V - D×V) / W = V×(T/W - 1/LD)
    """
    RC   = V * (T / W_N - 1.0 / LD)
    sin_gamma = T / W_N - 1.0 / LD
    sin_gamma = max(min(sin_gamma, 1.0), -1.0)
    gamma_deg = math.degrees(math.asin(sin_gamma))
    time_to_alt = (cfg.CRUISE_ALTITUDE * 0.3048) / RC if RC > 0 else float("inf")

    return {
        "RC_m_s":         RC,
        "RC_fpm":         RC * 196.85,
        "gamma_deg":      gamma_deg,
        "T_W":            T / W_N,
        "time_to_alt_s":  time_to_alt,
        "time_to_alt_min":time_to_alt / 60.0,
    }


def service_ceiling(W_N: float, LD_max: float, CL_md: float,
                    T: float = cfg.MAX_THRUST,
                    S: float = cfg.WING_AREA,
                    RC_ceil: float = 0.5) -> dict:
    """
    Service ceiling: altitude where RC = RC_ceil (default 0.5 m/s).
    Iterates on density using ISA model.
    """
    rho = cfg.RHO_CRUISE
    ceiling_found = False

    for _ in range(10000):
        if rho < 0.05:
            break
        V_md  = math.sqrt(2.0 * W_N / (rho * CL_md * S))
        RC    = V_md * (T / W_N - 1.0 / LD_max)
        if RC <= RC_ceil:
            ceiling_found = True
            break
        rho -= 0.0005

    # Recover altitude from density (ISA inverse)
    rho = max(rho, 0.3)
    sigma = rho / 1.225
    h_m  = (1.0 - sigma**(1.0/4.2559)) / 2.2558e-5
    h_ft = h_m / 0.3048

    return {
        "ceiling_m":    h_m,
        "ceiling_ft":   h_ft,
        "rho_ceiling":  rho,
        "V_md_ceiling": math.sqrt(2.0 * W_N / (rho * CL_md * S)),
        "RC_at_ceiling": RC_ceil,
        "found":        ceiling_found,
    }


def load_factors(CL_max: float, V: float = cfg.CRUISE_SPEED,
                 V_max: float = cfg.MAX_SPEED) -> dict:
    """
    V-n diagram key points.
    n_max = CL_max × q / (W/S)
    """
    WS   = cfg.MTOW * cfg.G / cfg.WING_AREA  # wing loading [N/m²]
    q_cr = 0.5 * cfg.RHO_CRUISE * V**2
    q_max= 0.5 * cfg.RHO_CRUISE * V_max**2

    n_stall_cr  = CL_max * q_cr  / WS
    n_stall_max = CL_max * q_max / WS

    # FAR 23 UAV: typically n_max = 3.5–4.0
    n_design     = min(n_stall_max, 4.0)   # positive limit
    n_design_neg = -0.4 * n_design          # negative limit (typical)

    return {
        "WS_N_m2":       WS,
        "n_cruise":      n_stall_cr,
        "n_max_speed":   n_stall_max,
        "n_design":      n_design,
        "n_design_neg":  n_design_neg,
        "V_A_m_s":       math.sqrt(2.0 * n_design * WS / (cfg.RHO_CRUISE * CL_max)),
        "V_A_kts":       math.sqrt(2.0 * n_design * WS / (cfg.RHO_CRUISE * CL_max)) * 1.944,
    }


def glide_performance(LD_max: float) -> dict:
    """Best glide ratio and sink rate at best glide speed."""
    W_N  = cfg.MTOW * cfg.G
    k    = 1.0 / (math.pi * cfg.ASPECT_RATIO * cfg.OSWALD_EFF)
    CL_md= math.sqrt(cfg.CD0 / k)
    V_bg = math.sqrt(2.0 * W_N / (cfg.RHO_SL * CL_md * cfg.WING_AREA))
    sink = V_bg / LD_max   # sink rate [m/s]

    return {
        "glide_ratio":  LD_max,
        "V_best_glide": V_bg,
        "sink_rate_m_s":sink,
        "sink_fpm":     sink * 196.85,
    }


# -------------------------------------------------------
# STANDALONE
# -------------------------------------------------------
if __name__ == "__main__":
    from weights import weight_breakdown
    from aerodynamics import cruise_aero, optimal_cl, clmax_from_stall

    wb   = weight_breakdown()
    W_N  = wb["MTOW_N"]
    cr   = cruise_aero(W_N)
    opt  = optimal_cl()
    CLmax= clmax_from_stall(W_N)

    to   = takeoff_ground_roll(W_N, CLmax)
    cl   = climb_performance(W_N, cr["LD"])
    sc   = service_ceiling(W_N, opt["LD_max"], opt["CL_md"])
    lf   = load_factors(CLmax)
    gl   = glide_performance(opt["LD_max"])

    print("\n=== TAKEOFF ===")
    print(f"  V_stall         : {to['V_stall']:.2f} m/s")
    print(f"  V_TO (1.2 Vs)   : {to['V_TO']:.2f} m/s")
    print(f"  STO (Raymer)    : {to['STO_raymer']:.1f} m")
    print(f"  STO (detailed)  : {to['STO_detailed']:.1f} m")
    print(f"  STO (config)    : {to['STO_config']:.1f} m")
    print(f"  Air dist (35ft) : {to['S_airborne']:.1f} m")
    print(f"  Total (FAR)     : {to['STO_total']:.1f} m")

    print("\n=== CLIMB ===")
    print(f"  Rate of climb   : {cl['RC_m_s']:.2f} m/s  ({cl['RC_fpm']:.0f} fpm)")
    print(f"  Climb angle     : {cl['gamma_deg']:.2f}°")
    print(f"  T/W ratio       : {cl['T_W']:.3f}")
    print(f"  Time to {cfg.CRUISE_ALTITUDE} ft  : {cl['time_to_alt_min']:.1f} min")

    print("\n=== SERVICE CEILING ===")
    print(f"  Ceiling         : {sc['ceiling_ft']:.0f} ft  ({sc['ceiling_m']:.0f} m)")
    print(f"  V_md at ceiling : {sc['V_md_ceiling']:.2f} m/s")

    print("\n=== LOAD FACTORS ===")
    print(f"  Wing loading    : {lf['WS_N_m2']:.1f} N/m²")
    print(f"  n at cruise     : {lf['n_cruise']:.2f}")
    print(f"  n design (+)    : {lf['n_design']:.2f}")
    print(f"  n design (-)    : {lf['n_design_neg']:.2f}")
    print(f"  V_A (manoeuvre) : {lf['V_A_m_s']:.2f} m/s  ({lf['V_A_kts']:.1f} kts)")

    print("\n=== GLIDE ===")
    print(f"  Glide ratio     : {gl['glide_ratio']:.1f}")
    print(f"  Best glide speed: {gl['V_best_glide']:.2f} m/s")
    print(f"  Sink rate       : {gl['sink_rate_m_s']:.2f} m/s  ({gl['sink_fpm']:.0f} fpm)")
