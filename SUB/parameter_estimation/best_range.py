import numpy as np
import sys
import os
import json

# ==========================================================
# PATH SETUP
# ==========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

import config as cfg

# ==========================================================
# UAV & MISSION PARAMETERS (FROM CONFIG)
# ==========================================================
W = cfg.MTOW * cfg.G           # N
CD0 = cfg.CD0
AR = cfg.ASPECT_RATIO
e = cfg.OSWALD_EFF

T_max = cfg.MAX_THRUST
TSFC = cfg.TSFC / 3600         # 1/s (ranking only)

rho0 = cfg.RHO_SL
h = cfg.CRUISE_ALTITUDE * 0.3048   # ft → m
E = cfg.MISSION_TIME              # seconds

# ==========================================================
# OPERATIONAL CONSTRAINTS
# ==========================================================
CL_max = cfg.CL_MAX
V_stall_max = cfg.STALL_SPEED
WS_max = 1200                     # N/m² (design choice)
Mach_max = 0.3

# ==========================================================
# ATMOSPHERE (SIMPLE ISA)
# ==========================================================
rho = rho0 * (1 - 2.25577e-5 * h) ** 4.256
a = 340

# ==========================================================
# SEARCH SPACE
# ==========================================================
S_range = np.linspace(0.8, 2.2, 120)
V_range = np.linspace(35, 90, 160)

best_solution = None
max_range = 0

# ==========================================================
# ITERATIVE OPTIMIZATION
# ==========================================================
for S in S_range:

    # Stall constraint
    S_stall_min = (2 * W) / (rho * CL_max * V_stall_max**2)
    if S < S_stall_min:
        continue

    # Wing loading constraint
    if W / S > WS_max:
        continue

    for V in V_range:

        if V / a > Mach_max:
            continue

        CL = (2 * W) / (rho * V**2 * S)
        if CL <= 0 or CL > CL_max:
            continue

        CD = CD0 + (CL**2) / (np.pi * AR * e)
        T_req = 0.5 * rho * V**2 * S * CD

        if T_req > T_max:
            continue

        R = V * E

        if R > max_range:
            max_range = R
            best_solution = {
                "endurance_min": E / 60,
                "wing_area_m2": round(S, 3),
                "wing_loading_kg_m2": round((cfg.MTOW) / S, 2),
                "velocity_m_s": round(V, 2),
                "mach": round(V / a, 3),
                "CL": round(CL, 3),
                "CD": round(CD, 4),
                "thrust_required_N": round(T_req, 2),
                "range_km": round(R / 1000, 2)
            }

# ==========================================================
# SAFETY CHECK
# ==========================================================
if best_solution is None:
    print("\n❌ No feasible design found. Constraints too tight.\n")
    sys.exit()

# ==========================================================
# OUTPUT TO TERMINAL
# ==========================================================
print("\n===== BEST RANGE FOR 45 MIN ENDURANCE =====\n")
for k, v in best_solution.items():
    print(f"{k}: {v}")

# ==========================================================
# STORE RESULTS INSIDE FOLDER
# ==========================================================

# ---- Python file (importable) ----
result_py = f'''"""
AUTO-GENERATED FILE
DO NOT EDIT MANUALLY
"""

BEST_RANGE_KM = {best_solution["range_km"]}
BEST_WING_AREA = {best_solution["wing_area_m2"]}
BEST_VELOCITY = {best_solution["velocity_m_s"]}
BEST_MACH = {best_solution["mach"]}
BEST_CL = {best_solution["CL"]}
BEST_CD = {best_solution["CD"]}
BEST_THRUST_REQUIRED = {best_solution["thrust_required_N"]}
BEST_WING_LOADING = {best_solution["wing_loading_kg_m2"]}
'''

with open(os.path.join(CURRENT_DIR, "best_range_result.py"), "w") as f:
    f.write(result_py)

print("\n✅ Results stored in performance folder")
