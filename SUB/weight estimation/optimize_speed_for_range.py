import math
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

import config as cfg

# ======================================
# CONSTANTS
# ======================================
rho = cfg.RHO_CRUISE
g = cfg.G

# ======================================
# SEARCH RANGES
# ======================================
V_range = [v for v in range(25, 75, 2)]          # m/s
WS_range = [ws for ws in range(300, 1200, 50)]  # N/m²

best = None

# ======================================
# DESIGN LOOP
# ======================================
for V in V_range:
    q = 0.5 * rho * V**2

    for WS in WS_range:

        # Wing area
        S = cfg.MTOW * g / WS

        # Required CL at cruise
        CL = WS / q

        if CL > cfg.CL_MAX_CRUISE:
            continue  # infeasible

        # -------------------------------
        # Wing structural weight model
        # (simple but physically meaningful)
        # -------------------------------
        W_wing = cfg.K_WING * (WS**0.55) * (S**0.6)

        # -------------------------------
        # Empty weight model
        # -------------------------------
        We = (
            W_wing +
            cfg.W_FIXED +          # fuselage, landing gear, avionics
            cfg.W_ENGINE +
            cfg.W_SYSTEMS
        )

        # -------------------------------
        # Fuel weight (Breguet – jet)
        # -------------------------------
        c = (cfg.TSFC * g) / 3600

        cruise_fraction = math.exp(
            -(cfg.CRUISE_RANGE * c) / (V * cfg.L_OVER_D)
        )

        mission_weight_fraction = (
            cfg.WARMUP_TAKEOFF *
            cfg.CLIMB *
            cruise_fraction *
            cfg.DESCENT *
            cfg.LANDING
        )

        fuel_weight = (1 - mission_weight_fraction) * cfg.MTOW

        payload = cfg.MTOW - (We + fuel_weight)

        if payload <= 0:
            continue

        # -------------------------------
        # Store minimum empty weight
        # -------------------------------
        if best is None or We < best["We"]:
            best = {
                "V": V,
                "WS": WS,
                "S": S,
                "CL": CL,
                "We": We,
                "fuel": fuel_weight,
                "payload": payload
            }

# ======================================
# OUTPUT
# ======================================
print("\nMINIMUM EMPTY WEIGHT DESIGN")
print("===================================")

if best:
    print(f"Cruise Speed            : {best['V']} m/s")
    print(f"Wing Loading (W/S)      : {best['WS']} N/m²")
    print(f"Wing Area               : {best['S']:.2f} m²")
    print(f"Cruise CL               : {best['CL']:.3f}")
    print(f"Empty Weight            : {best['We']:.2f} kg")
    print(f"Fuel Weight             : {best['fuel']:.2f} kg")
    print(f"Payload                 : {best['payload']:.2f} kg")
else:
    print("❌ No feasible design found")

print("===================================\n")
