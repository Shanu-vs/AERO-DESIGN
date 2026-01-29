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
S = 0.85                # m^2
CD0 = 0.03
AR = 8
e = 0.8

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
