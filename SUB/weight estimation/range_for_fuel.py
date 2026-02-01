import math

# =====================================================
# AIRCRAFT
# =====================================================
MTOW = 80.0
EMPTY_WEIGHT = 44.0
G = 9.81

TOTAL_FUEL = 20
RESERVE_FRACTION = 0.05

# =====================================================
# MISSION
# =====================================================
TOTAL_MISSION_TIME = 45 * 60
LOITER_TIME = 5 * 60
FIXED_TIME = 10 * 60

# =====================================================
# AERODYNAMICS
# =====================================================
RHO = 0.736
S = 1.6
AR = 8.0
e = 0.85
CD0 = 0.025

k = 1 / (math.pi * e * AR)

# =====================================================
# ENGINE
# =====================================================
TSFC = 0.157
c = (TSFC * G) / 3600

# =====================================================
# SPEED SWEEP
# =====================================================
V_MIN = 30.0
V_MAX = 90.0
V_STEP = 0.5

solutions = []

# =====================================================
# MAIN LOOP
# =====================================================
for i in range(int((V_MAX - V_MIN) / V_STEP) + 1):
    V = V_MIN + i * V_STEP

    W_start = MTOW * G

    CL = W_start / (0.5 * RHO * V**2 * S)
    CD = CD0 + k * CL**2
    L_over_D = CL / CD

    # Loiter
    loiter_fraction = math.exp(-(LOITER_TIME * c) / L_over_D)
    W_after_loiter = W_start * loiter_fraction
    loiter_fuel = (W_start - W_after_loiter) / G

    usable_fuel = TOTAL_FUEL * (1 - RESERVE_FRACTION)
    cruise_fuel = usable_fuel - loiter_fuel
    if cruise_fuel <= 0:
        continue

    W_end = W_after_loiter - cruise_fuel * G
    if W_end <= 0:
        continue

    cruise_range = (V / c) * L_over_D * math.log(W_after_loiter / W_end)
    cruise_time = cruise_range / V
    total_time = cruise_time + LOITER_TIME + FIXED_TIME

    solutions.append({
        "speed": V,
        "range_km": cruise_range / 1000,
        "time_min": total_time / 60,
        "fuel": loiter_fuel + cruise_fuel,
        "L_over_D": L_over_D,
        "time_margin": (TOTAL_MISSION_TIME - total_time) / 60
    })

# =====================================================
# SORT BY RANGE
# =====================================================
solutions.sort(key=lambda x: x["range_km"], reverse=True)
top5 = solutions[:5]

print("\nTOP 5 BEST POSSIBLE SOLUTIONS (DIAGNOSTIC)")
print("================================================================================")
print("Rank | Speed | Range | Time | Time Margin | Fuel | L/D")
print("--------------------------------------------------------------------------------")

for i, s in enumerate(top5, 1):
    print(f"{i:>3}  |"
          f" {s['speed']:6.1f} |"
          f" {s['range_km']:6.1f} |"
          f" {s['time_min']:6.2f} |"
          f" {s['time_margin']:7.2f} |"
          f" {s['fuel']:5.2f} |"
          f" {s['L_over_D']:5.2f}")

print("================================================================================\n")
