# =====================================================
# MODULE: atmosphere.py
# ISA standard atmosphere — no CSV dependency.
# Falls back to CSV if path provided.
# =====================================================

import math
import numpy as np


# -------------------------------------------------------
# ISA STANDARD ATMOSPHERE (analytical)
# -------------------------------------------------------

def isa_properties(altitude_m: float) -> dict:
    """
    Return ISA standard atmosphere properties at given altitude (m).
    Valid up to ~20 000 m (troposphere + lower stratosphere).
    """
    T0   = 288.15    # K    sea level temperature
    P0   = 101325.0  # Pa   sea level pressure
    rho0 = 1.225     # kg/m³ sea level density
    L    = 0.0065    # K/m  lapse rate (troposphere)
    g    = 9.80665
    R    = 287.05    # J/(kg·K)
    h_tp = 11000.0   # m    tropopause

    if altitude_m <= h_tp:
        T   = T0 - L * altitude_m
        P   = P0 * (T / T0) ** (g / (L * R))
    else:
        # Isothermal stratosphere
        T_tp = T0 - L * h_tp
        P_tp = P0 * (T_tp / T0) ** (g / (L * R))
        T    = T_tp
        P    = P_tp * math.exp(-g * (altitude_m - h_tp) / (R * T_tp))

    rho = P / (R * T)
    a   = math.sqrt(1.4 * R * T)          # speed of sound
    mu  = 1.458e-6 * T**1.5 / (T + 110.4) # Sutherland viscosity

    return {
        "altitude_m":  altitude_m,
        "altitude_ft": altitude_m / 0.3048,
        "T_K":         T,
        "P_Pa":        P,
        "rho":         rho,
        "a":           a,
        "mu":          mu,
        "nu":          mu / rho,           # kinematic viscosity
    }


def from_ft(altitude_ft: float) -> dict:
    return isa_properties(altitude_ft * 0.3048)


def density_ratio(altitude_m: float) -> float:
    return isa_properties(altitude_m)["rho"] / 1.225


# -------------------------------------------------------
# CSV FALLBACK (optional — matches your existing CSV)
# -------------------------------------------------------

def from_csv(csv_path: str, altitude_m: float) -> dict:
    """
    Load from atmosphere CSV if available.
    Expected columns: Altitude_m, Temperature_K, Pressure_Pa,
                      Density_kg_m3, Speed_of_Sound_m_s
    """
    try:
        import pandas as pd
        atm = pd.read_csv(csv_path)
        props = {}
        col_map = {
            "T_K":  "Temperature_K",
            "P_Pa": "Pressure_Pa",
            "rho":  "Density_kg_m3",
            "a":    "Speed_of_Sound_m_s",
        }
        for key, col in col_map.items():
            if col in atm.columns:
                props[key] = float(np.interp(altitude_m, atm["Altitude_m"], atm[col]))
        # Compute mu from T
        T = props.get("T_K", 288.15)
        props["mu"]         = 1.458e-6 * T**1.5 / (T + 110.4)
        props["altitude_m"] = altitude_m
        props["altitude_ft"]= altitude_m / 0.3048
        props["nu"]         = props["mu"] / props["rho"]
        return props
    except Exception:
        # Fall back to ISA
        return isa_properties(altitude_m)


# -------------------------------------------------------
# STANDALONE TEST
# -------------------------------------------------------
if __name__ == "__main__":
    print(f"{'Alt (ft)':>10s} | {'Temp (K)':>9s} | {'Density':>10s} | {'Sound (m/s)':>11s} | {'mu (Pa·s)':>12s}")
    print("-" * 65)
    for ft in [0, 1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000, 15000, 20000]:
        p = from_ft(ft)
        print(f"{ft:>10.0f} | {p['T_K']:>9.2f} | {p['rho']:>10.5f} | {p['a']:>11.3f} | {p['mu']:>12.3e}")
