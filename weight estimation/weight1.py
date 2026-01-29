import math

# =====================================================
# INPUT DATA
# =====================================================

# Maximum Take-Off Weight (kg)
W0 = 80.0

# Mission parameters
cruise_range = 100_000          # m
cruise_speed = 40.0            # m/s
L_over_D = 10.0

# Loiter parameters
loiter_time_min = 5            # minutes
loiter_time = loiter_time_min * 60  # seconds

# Engine data
TSFC = 0.187                   # kg/(N·hr)
g = 9.81                       # m/s^2

# Mission segment weight fractions (standard)
warmup_takeoff = 0.99
climb = 0.98
descent_landing = 0.995

# Raymer empty weight regression constants (jet aircraft)
A = 0.86
B = 0.94

# =====================================================
# EMPTY WEIGHT CALCULATION (Raymer)
# =====================================================
We = A * (W0 ** B)
empty_weight_fraction = We / W0

# =====================================================
# TSFC CONVERSION
# =====================================================
c = (TSFC * g) / 3600           # 1/s

# =====================================================
# CRUISE FUEL FRACTION (Breguet Range – Jet)
# =====================================================
cruise_fraction = math.exp(
    -(cruise_range * c) / (cruise_speed * L_over_D)
)

# =====================================================
# LOITER FUEL FRACTION (Breguet Endurance – Jet)
# =====================================================
loiter_fraction = math.exp(
    -(loiter_time * c) / (L_over_D)
)

# =====================================================
# TOTAL MISSION WEIGHT FRACTION
# =====================================================
total_weight_fraction = (
    warmup_takeoff *
    climb *
    cruise_fraction *
    loiter_fraction *
    descent_landing
)

# =====================================================
# FUEL WEIGHT
# =====================================================
fuel_fraction = 1 - total_weight_fraction
fuel_weight = fuel_fraction * W0

# =====================================================
# PAYLOAD WEIGHT
# =====================================================
payload_weight = W0 - (We + fuel_weight)

# =====================================================
# OUTPUT
# =====================================================
print("\nJET UAV PRELIMINARY WEIGHT SIZING (WITH LOITER)")
print("==============================================")

print("\n--- INPUT PARAMETERS ---")
print(f"Maximum Take-Off Weight (W0)     : {W0:.2f} kg")
print(f"Cruise Range                     : {cruise_range/1000:.1f} km")
print(f"Cruise Speed                     : {cruise_speed:.1f} m/s")
print(f"Lift-to-Drag Ratio (L/D)         : {L_over_D:.1f}")
print(f"Loiter Time                      : {loiter_time_min} min")
print(f"TSFC                             : {TSFC:.3f} kg/(N·hr)")

print("\n--- EMPTY WEIGHT (Raymer) ---")
print(f"Empty Weight (We)                : {We:.2f} kg")
print(f"Empty Weight Fraction            : {empty_weight_fraction:.4f}")

print("\n--- MISSION FUEL ANALYSIS ---")
print(f"Cruise Weight Fraction           : {cruise_fraction:.4f}")
print(f"Loiter Weight Fraction           : {loiter_fraction:.4f}")
print(f"Total Mission Weight Fraction    : {total_weight_fraction:.4f}")
print(f"Fuel Fraction                    : {fuel_fraction:.4f}")
print(f"Fuel Weight                      : {fuel_weight:.2f} kg")

print("\n--- PAYLOAD ---")
print(f"Payload Weight                   : {payload_weight:.2f} kg")

print("\n--- FEASIBILITY CHECK ---")
if payload_weight > 0:
    print("Payload Feasibility              : ✅ POSSIBLE")
else:
    print("Payload Feasibility              : ❌ NOT POSSIBLE – Revise mission or W0")

print("\n==============================================\n")
