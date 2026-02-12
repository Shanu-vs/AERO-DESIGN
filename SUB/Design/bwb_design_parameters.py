import math
import sys
import os

# ----------------------------------------------------------
# Allow script to import config.py from root directory
# ----------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(ROOT_DIR)

import config as cfg


print("====================================")
print("   BWB AIRCRAFT DESIGN CALCULATOR")
print("====================================")

# ==========================================================
# READ VALUES FROM CONFIG
# ==========================================================

W = cfg.MTOW * cfg.G              # weight (N)
S = cfg.WING_AREA
AR = cfg.ASPECT_RATIO
e = cfg.OSWALD_EFF
rho = cfg.RHO_CRUISE
V = cfg.CRUISE_SPEED
CL_max = cfg.CL_MAX
CD0 = cfg.CD0
T_max = cfg.MAX_THRUST
ROC_required = cfg.ROC

# ==========================================================
# 1) WING GEOMETRY
# ==========================================================

b = math.sqrt(AR * S)
MAC = S / b

# recommended taper ratio for BWB
taper = 0.45

Cr = (2 * S) / (b * (1 + taper))
Ct = taper * Cr

print("\n--- Wing Geometry ---")
print(f"Wingspan b        : {b:.3f} m")
print(f"Root chord Cr     : {Cr:.3f} m")
print(f"Tip chord Ct      : {Ct:.3f} m")
print(f"Mean chord MAC    : {MAC:.3f} m")
print(f"Taper ratio       : {taper}")

# ==========================================================
# 2) SWEEP EFFECT
# ==========================================================

sweep = 25  # recommended for BWB
sweep_rad = math.radians(sweep)

AC_location = 0.25 + 0.1 * math.tan(sweep_rad)

print("\n--- Sweep Effect ---")
print(f"Sweep angle       : {sweep} deg")
print(f"Aerodynamic center: {AC_location*100:.1f}% MAC")

# ==========================================================
# 3) CG LOCATION  (MOST IMPORTANT)
# ==========================================================

static_margin = 0.07
CG_location = AC_location - static_margin

print("\n--- CG Location ---")
print(f"Recommended CG    : {CG_location*100:.1f}% MAC")
print(f"Distance from LE  : {CG_location*MAC:.3f} m")

# ==========================================================
# 4) CRUISE LIFT COEFFICIENT
# ==========================================================

CL_cruise = W / (0.5 * rho * V**2 * S)

print("\n--- Cruise Aerodynamics ---")
print(f"CL_cruise         : {CL_cruise:.3f}")

k = 1 / (math.pi * AR * e)

CD_induced = k * CL_cruise**2
CD_total = CD0 + CD_induced

print(f"Induced CD        : {CD_induced:.4f}")
print(f"Total CD          : {CD_total:.4f}")

D = 0.5 * rho * V**2 * S * CD_total

print(f"Cruise Drag       : {D:.1f} N")

# ==========================================================
# 5) STALL SPEED
# ==========================================================

Vs = math.sqrt((2 * W) / (rho * S * CL_max))

print("\n--- Stall ---")
print(f"Predicted Stall Speed : {Vs:.2f} m/s")
print(f"Target Stall Speed    : {cfg.STALL_SPEED:.2f} m/s")

# ==========================================================
# 6) THRUST REQUIRED
# ==========================================================

T_required = D

print("\n--- Thrust ---")
print(f"Required Thrust   : {T_required:.1f} N")
print(f"Available Thrust  : {T_max:.1f} N")
print(f"T/W ratio         : {T_max/W:.2f}")

# ==========================================================
# 7) RATE OF CLIMB
# ==========================================================

excess_thrust = T_max - D
ROC = excess_thrust * V / W

print("\n--- Climb ---")
print(f"Predicted ROC     : {ROC:.2f} m/s")
print(f"Required ROC      : {ROC_required:.2f} m/s")

if ROC > ROC_required:
    print("Climb requirement : PASS")
else:
    print("Climb requirement : FAIL")

# ==========================================================
# 8) EFFICIENCY
# ==========================================================

LD = CL_cruise / CD_total

print("\n--- Efficiency ---")
print(f"Cruise L/D        : {LD:.1f}")

