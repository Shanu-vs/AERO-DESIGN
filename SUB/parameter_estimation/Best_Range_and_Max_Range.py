import numpy as np

# ============================================================
# CONSTANTS
# ============================================================
g = 9.81
rho = 1.058          # kg/m^3 (6000 ft)
pi = np.pi

# ============================================================
# UAV FIXED MASSES (fuel unknown)
# ============================================================
mass_empty = 55    # kg (structure + avionics + engine)
payload = 15       # kg

# ============================================================
# GEOMETRY & AERODYNAMICS
# ============================================================
S = 0.85             # m^2
AR = 8.0
e = 0.8
CD0 = 0.06           # REALISTIC jet UAV value

k = 1 / (pi * e * AR)

# ============================================================
# ENGINE MODEL (REALISTIC MICRO-TURBOJET)
# ============================================================
T_max = 425.0        # N
fuel_flow_max = 1.30 # kg/hr
fuel_flow_idle = 0.65
fuel_flow_min = 0.85 # ABSOLUTE minimum in flight

# ============================================================
# FUNCTIONS
# ============================================================

def drag_force(W, V):
    """Compute drag for given weight and speed"""
    CL = (2 * W) / (rho * V**2 * S)
    CD = CD0 + k * CL**2
    D = 0.5 * rho * V**2 * S * CD
    return D, CL, CD


def fuel_flow_required(thrust):
    """Fuel flow model with hard lower limit"""
    ratio = thrust / T_max
    ratio = np.clip(ratio, 0.3, 1.0)

    m_dot = fuel_flow_idle + ratio * (fuel_flow_max - fuel_flow_idle)
    return max(m_dot, fuel_flow_min)


def fuel_for_range(range_km, V, fuel_guess):
    """Iteratively solve fuel required for given range and speed"""
    for _ in range(40):
        total_mass = mass_empty + payload + fuel_guess
        W = total_mass * g

        D, _, _ = drag_force(W, V)
        m_dot = fuel_flow_required(D)

        time_hr = (range_km * 1000) / (V * 3600)
        fuel_new = m_dot * time_hr

        fuel_guess = 0.7 * fuel_guess + 0.3 * fuel_new

    return fuel_guess, D, m_dot


# ============================================================
# BEST RANGE SPEED SEARCH
# ============================================================
ranges_km = [100, 150, 200, 250, 300, 350, 400]

V_candidates = np.linspace(35, 65, 60)  # m/s

print("\n===== FINAL PHYSICALLY CONSISTENT RESULTS =====\n")

for R in ranges_km:

    best = None

    for V in V_candidates:
        fuel, D, m_dot = fuel_for_range(R, V, fuel_guess=10.0)

        fuel_per_km = fuel / R

        if best is None or fuel_per_km < best["fuel_per_km"]:
            best = {
                "V": V,
                "fuel": fuel,
                "drag": D,
                "fuel_flow": m_dot,
                "fuel_per_km": fuel_per_km
            }

    print(
        f"Range: {R:>3} km | "
        f"Best V: {best['V']:5.1f} m/s | "
        f"Drag: {best['drag']:6.1f} N | "
        f"Fuel flow: {best['fuel_flow']:4.2f} kg/hr | "
        f"Fuel: {best['fuel']:5.1f} kg"
    )
