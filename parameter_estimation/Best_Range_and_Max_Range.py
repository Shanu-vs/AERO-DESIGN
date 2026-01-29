import numpy as np

# ----------------------------------
# UAV & ENGINE PARAMETERS
# ----------------------------------
W = 80 * 9.81            # N
CD0 = 0.03
AR = 8
e = 0.8
T_max = 425              # N
TSFC = 0.187 / 3600      # 1/s

rho0 = 1.225
h = 1800                 # meters (~6000 ft)
E = 45 * 60              # endurance in seconds

# ----------------------------------
# AIR DENSITY
# ----------------------------------
rho = rho0 * (1 - 2.25577e-5 * h) ** 4.256

# ----------------------------------
# SEARCH SPACE
# ----------------------------------
S_range = np.linspace(0.6, 1.2, 60)
V_range = np.linspace(35, 85, 150)

best_solution = None
max_range = 0

# ----------------------------------
# ITERATIVE SEARCH
# ----------------------------------
for S in S_range:
    for V in V_range:

        CL = (2 * W) / (rho * V**2 * S)
        if CL < 0.1 or CL > 1.2:
            continue

        CD = CD0 + (CL**2) / (np.pi * AR * e)
        T_req = 0.5 * rho * V**2 * S * CD

        if T_req > T_max:
            continue

        # Fuel required for 45 min
        fuel_required = TSFC * T_req * E

        # Range
        R = V * E   # meters

        if R > max_range:
            max_range = R
            best_solution = {
                "Endurance (min)": 45,
                "Wing Area (m²)": round(S, 3),
                "Velocity (m/s)": round(V, 2),
                "CL": round(CL, 3),
                "CD": round(CD, 4),
                "Thrust Required (N)": round(T_req, 2),
                "Fuel Used (kg equiv)": round(fuel_required, 4),
                "Range (km)": round(R / 1000, 2)
            }

# ----------------------------------
# OUTPUT
# ----------------------------------
print("\nBEST RANGE FOR 45 MIN ENDURANCE\n")
for k, v in best_solution.items():
    print(f"{k}: {v}")
