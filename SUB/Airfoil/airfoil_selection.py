# =====================================================
# AIRFOIL SELECTION MODULE – FINAL
# =====================================================

# -----------------------
# FIX PROJECT IMPORT PATH
# -----------------------
import sys
import os
import math

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# -----------------------
# STANDARD IMPORTS
# -----------------------
import numpy as np
import pandas as pd

# -----------------------
# LOAD CONFIG
# -----------------------
import config as cfg


# =====================================================
# ATMOSPHERE HANDLER (MATCHES YOUR CSV)
# =====================================================

def load_atmosphere(csv_path):
    return pd.read_csv(csv_path)


def interpolate_density(atm, altitude_m):
    return np.interp(
        altitude_m,
        atm["Altitude_m"],
        atm["Density_kg_m3"]
    )


def interpolate_speed_of_sound(atm, altitude_m):
    return np.interp(
        altitude_m,
        atm["Altitude_m"],
        atm["Speed_of_Sound_m_s"]
    )


# =====================================================
# AIRFOIL SELECTION FORMULAS (FROM SLIDES)
# =====================================================

def average_cruise_weight(Wi, Wf):
    return 0.5 * (Wi + Wf)


def ideal_cruise_lift_coefficient(W_avg, rho, V, S):
    return (2 * W_avg) / (rho * V**2 * S)
 

def wing_cruise_lift_coefficient(C_lc):
    return C_lc / 0.95


def airfoil_ideal_lift_coefficient(C_lw):
    return C_lw / 0.9


def aircraft_max_lift_coefficient(W_to, rho_sl, V_stall, S):
    return (2 * W_to) / (rho_sl * V_stall**2 * S)


def wing_max_lift_coefficient(C_Lmax):
    return C_Lmax / 0.95


def airfoil_gross_max_lift_coefficient(C_Lmax_w):
    return C_Lmax_w / 0.9


def airfoil_net_max_lift_coefficient(c_lmax_gross, delta_cl_hld=0.0):
    return c_lmax_gross - delta_cl_hld


# =====================================================
# REYNOLDS NUMBER
# =====================================================

def reynolds_number(rho, V, S, AR):
    b = math.sqrt(AR * S)    # wing span
    c = S / b               # mean aerodynamic chord
    mu = 1.789e-5           # air viscosity (kg/m·s)
    Re = (rho * V * c) / mu
    return Re, c


# =====================================================
# MAIN SOLVER
# =====================================================

def run_airfoil_selection():

    # -----------------------
    # LOAD ATMOSPHERE
    # -----------------------
    atm = load_atmosphere(cfg.ATMOSPHERE_CSV)

    h_cruise_m = cfg.CRUISE_ALTITUDE * 0.3048
    rho_cruise = interpolate_density(atm, h_cruise_m)

    # -----------------------
    # WEIGHTS (N)
    # -----------------------
    W_to = cfg.MTOW * cfg.G
    W_fuel = cfg.FUEL_WEIGHT * cfg.G

    Wi = W_to
    Wf = W_to - W_fuel

    # -----------------------
    # STEP 1 – AVERAGE WEIGHT
    # -----------------------
    W_avg = average_cruise_weight(Wi, Wf)

    # -----------------------
    # STEP 2 – CRUISE CL
    # -----------------------
    C_lc = ideal_cruise_lift_coefficient(
        W_avg,
        rho_cruise,
        cfg.CRUISE_SPEED,
        cfg.WING_AREA
    )

    # -----------------------
    # STEP 3 – WING CL
    # -----------------------
    C_lw = wing_cruise_lift_coefficient(C_lc)

    # -----------------------
    # STEP 4 – AIRFOIL CL
    # -----------------------
    c_li = airfoil_ideal_lift_coefficient(C_lw)

    # -----------------------
    # STEP 5 – AIRCRAFT CLmax
    # -----------------------
    C_Lmax = aircraft_max_lift_coefficient(
        W_to,
        cfg.RHO_SL,
        cfg.STALL_SPEED,
        cfg.WING_AREA
    )

    # -----------------------
    # STEP 6 – WING CLmax
    # -----------------------
    C_Lmax_w = wing_max_lift_coefficient(C_Lmax)

    # -----------------------
    # STEP 7 – AIRFOIL GROSS CLmax
    # -----------------------
    c_lmax_gross = airfoil_gross_max_lift_coefficient(C_Lmax_w)

    # -----------------------
    # STEP 10 – AIRFOIL NET CLmax (CLEAN)
    # -----------------------
    c_lmax_net = airfoil_net_max_lift_coefficient(c_lmax_gross)

    # -----------------------
    # REYNOLDS NUMBER
    # -----------------------
    Re, mac = reynolds_number(
        rho_cruise,
        cfg.CRUISE_SPEED,
        cfg.WING_AREA,
        cfg.ASPECT_RATIO
    )

    # -----------------------
    # OUTPUT
    # -----------------------
    results = {
        "Cruise altitude (m)": h_cruise_m,
        "Cruise density (kg/m^3)": rho_cruise,
        "Mean aerodynamic chord (m)": mac,
        "Reynolds number (cruise)": Re,
        "Average cruise weight (N)": W_avg,
        "C_lc (ideal aircraft)": C_lc,
        "C_lw (wing)": C_lw,
        "c_li (airfoil ideal)": c_li,
        "C_Lmax (aircraft)": C_Lmax,
        "C_Lmax_w (wing)": C_Lmax_w,
        "c_lmax_gross (airfoil)": c_lmax_gross,
        "c_lmax_net (airfoil clean)": c_lmax_net,
    }

    return results


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    results = run_airfoil_selection()

    print("\n====== GENERAL AIRFOIL SELECTION PARAMETERS ======\n")
    for k, v in results.items():
        print(f"{k:40s}: {v:.4f}")
