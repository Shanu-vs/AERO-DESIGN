"""
BEST CRUISE ALTITUDE FINDER - FIXED-WING JET UAV

Purpose:
--------
This script estimates the best cruise altitude for a fixed-wing jet-powered UAV
by identifying the altitude at which the minimum thrust required for steady,
level flight is the lowest.

Key Idea:
---------
For a jet aircraft, fuel consumption is approximately proportional to thrust.
Therefore, the most fuel-efficient cruise condition occurs where the thrust
required (drag) is minimum.

Methodology:
------------
1. A range of altitudes (0 to 6000 ft) is defined based on the UAV’s maximum
   operational ceiling.

2. At each altitude:
   a. Air density is calculated using the ISA atmospheric model.
   b. A range of possible cruise speeds is evaluated.
   c. For each speed:
      - Lift coefficient is computed from the lift = weight condition.
      - Total drag coefficient is calculated as the sum of:
          • Parasite drag (CD0)
          • Induced drag (function of CL, aspect ratio, and Oswald efficiency)
      - Drag (thrust required) is calculated.
   d. The minimum drag at that altitude is selected, representing the most
      efficient cruise speed for that altitude.

3. After evaluating all altitudes, the altitude corresponding to the global
   minimum thrust required is selected as the best cruise altitude.

Assumptions:
------------
- Steady, level, unaccelerated flight
- Fixed-wing configuration
- Incompressible flow (low subsonic speeds)
- Standard ISA atmosphere
- Lift equals weight
- Thrust required equals drag
- Engine thrust lapse and TSFC variation are not yet included

Output:
-------
- Best cruise altitude (ft)
- Minimum thrust required at that altitude (N)

Use Case:
---------
Preliminary UAV sizing and performance estimation for jet-powered fixed-wing
aircraft where cruise efficiency and fuel economy are key design drivers.
"""


import numpy as np

# -----------------------------
# CONSTANTS
# -----------------------------
g = 9.81
R = 287.05

# -----------------------------
# UAV PARAMETERS
# -----------------------------
mass = 80               # kg
W = mass * g            # N
S = 3.13                # m^2
CD0 = 0.02
AR = 2.05
e = 0.8                 # Oswald efficiency factor (accounts for non-ideal lift distribution)

# -----------------------------
# ALTITUDE RANGE
# -----------------------------
altitude_ft = np.linspace(0, 6000, 120)
altitude_m = altitude_ft * 0.3048

# -----------------------------
# SPEED RANGE
# -----------------------------
V_range = np.linspace(20, 60, 120)  # m/s

# -----------------------------
# ISA DENSITY
# -----------------------------
def air_density(h):
    T0 = 288.15
    P0 = 101325
    L = 0.0065
    T = T0 - L*h
    P = P0 * (T/T0)**(g/(R*L))
    return P / (R*T)

# -----------------------------
# MAIN CALCULATION
# -----------------------------
min_thrust_alt = []

for h in altitude_m:
    rho = air_density(h)
    drag_list = []

    for V in V_range:
        CL = W / (0.5 * rho * V**2 * S)
        CDi = CL**2 / (np.pi * AR * e)
        CD = CD0 + CDi
        D = 0.5 * rho * V**2 * S * CD
        drag_list.append(D)

    min_thrust_alt.append(min(drag_list))

min_thrust_alt = np.array(min_thrust_alt)

# -----------------------------
# BEST CRUISE ALTITUDE
# -----------------------------
best_index = np.argmin(min_thrust_alt)

print(f"Best Cruise Altitude ≈ {altitude_ft[best_index]:.0f} ft")
print(f"Minimum Thrust Required ≈ {min_thrust_alt[best_index]:.1f} N")
