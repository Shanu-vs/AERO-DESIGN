import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

# ==========================================================
# PATH SETUP
# ==========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

import config as cfg

# ==========================================================
# LOAD ATMOSPHERE MODEL
# ==========================================================
atm = pd.read_csv(os.path.join(PROJECT_ROOT, cfg.ATMOSPHERE_CSV))

def find_col(keys):
    for c in atm.columns:
        for k in keys:
            if k.lower() in c.lower():
                return c
    raise KeyError(f"Missing column for {keys}")

ALT = find_col(["altitude", "height"])
RHO = find_col(["density", "rho"])
A   = find_col(["sound", "speed"])

h = cfg.CRUISE_ALTITUDE * 0.3048
rho = np.interp(h, atm[ALT], atm[RHO])
a   = np.interp(h, atm[ALT], atm[A])

# ==========================================================
# PARAMETERS
# ==========================================================
g = cfg.G
W = cfg.MTOW * g

CL_max = cfg.CL_MAX
CD0 = cfg.CD0
AR = cfg.ASPECT_RATIO
e = cfg.OSWALD_EFF

Vs = cfg.STALL_SPEED
Vc = 1.5 * Vs
V_to = 1.2 * Vs

STO = cfg.STO                     # m 
ROC = cfg.ROC                     # m/s 
n = 2.5

k = 1 / (np.pi * e * AR)

WS = np.linspace(50, 700, 600)

# ==========================================================
# CONSTRAINTS
# ==========================================================
# Stall
WS_stall = 0.5 * rho * Vs**2 * CL_max

# Cruise
q = 0.5 * rho * Vc**2
TW_cruise = (q * CD0) / WS + (k * WS) / q

# Climb
TW_climb = TW_cruise + ROC / Vc

# Sustained turn
q_sl = 0.5 * cfg.RHO_SL * Vc**2
TW_turn = (q_sl * CD0) / WS + (k * n**2 * WS) / q_sl

# Jet take-off (horizontal line)
TW_takeoff = (V_to**2) / (2 * g * STO)

# ==========================================================
# PLOTTING
# ==========================================================
fig, ax = plt.subplots(figsize=(9, 6))

ax.plot(WS, TW_takeoff * np.ones_like(WS), label="Take-off (Jet)", color="magenta")
ax.plot(WS, TW_climb, label="Climb", color="red")
ax.plot(WS, TW_turn, label="Sustained Turn", color="blue")
ax.plot(WS, TW_cruise, label="Cruise", color="green")

ax.axvline(WS_stall, linestyle="--", color="black", label="Stall")

ax.set_xlabel("Wing Loading W/S (N/m²)")
ax.set_ylabel("Thrust-to-Weight Ratio T/W")
ax.set_title("UAV Constraint Analysis (Interactive Selection)")
ax.set_ylim(0, 1.2)
ax.grid(True)
ax.legend()

# ==========================================================
# INTERACTIVE POINT SELECTION
# ==========================================================
marker, = ax.plot([], [], "ko", markersize=8)

def on_click(event):
    if event.inaxes != ax:
        return

    WS_sel = event.xdata
    TW_sel = event.ydata

    marker.set_data([WS_sel], [TW_sel])
    fig.canvas.draw()

    S = W / WS_sel
    T_required = TW_sel * W

    output = f'''"""
USER-SELECTED DESIGN POINT
"""

WING_LOADING = {WS_sel:.2f}        # N/m^2
THRUST_TO_WEIGHT = {TW_sel:.3f}

WING_AREA = {S:.3f}                # m^2
AIRCRAFT_WEIGHT = {W:.2f}          # N
REQUIRED_THRUST = {T_required:.2f} # N

ALTITUDE = {h:.1f}                 # m
DENSITY = {rho:.4f}                # kg/m^3
'''

    with open(os.path.join(CURRENT_DIR, "selected_design_point.py"), "w") as f:
        f.write(output)

    print("\n✅ Design point selected and stored")
    print(f"W/S = {WS_sel:.2f} N/m²")
    print(f"T/W = {TW_sel:.3f}")

fig.canvas.mpl_connect("button_press_event", on_click)

plt.show()
