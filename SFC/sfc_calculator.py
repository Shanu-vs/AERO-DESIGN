import pandas as pd

# -----------------------------
# ENGINE DATA (from your table)
# -----------------------------
ENGINE = {
    "name": "P400-PRO-LN",
    "max_thrust_N": 425,
    "idle_thrust_N": 14,
    "max_fuel_ml_min": 1392,
    "idle_fuel_ml_min": 200,
    "fuel_density_kg_L": 0.80  # Jet A1 / Kerosene approx
}

# -----------------------------
# FUNCTION: Convert ml/min -> kg/hr
# -----------------------------
def fuel_flow_kg_hr(fuel_ml_min, density_kg_L=0.80):
    # ml/min -> L/min
    fuel_L_min = fuel_ml_min / 1000.0
    # L/min -> L/hr
    fuel_L_hr = fuel_L_min * 60.0
    # L/hr -> kg/hr
    return fuel_L_hr * density_kg_L

# -----------------------------
# FUNCTION: TSFC calculation
# -----------------------------
def tsfc_kg_Nh(mdot_kg_hr, thrust_N):
    if thrust_N <= 0:
        return None
    return mdot_kg_hr / thrust_N


# -----------------------------
# MISSION PROFILE INPUT
# You can edit thrust_fraction and duration_min
# -----------------------------
mission_profile = [
    {"segment": "Idle / Taxi", "duration_min": 5, "thrust_fraction": 0.05},
    {"segment": "Takeoff",     "duration_min": 1, "thrust_fraction": 1.00},
    {"segment": "Climb",       "duration_min": 6, "thrust_fraction": 0.80},
    {"segment": "Cruise",      "duration_min": 12, "thrust_fraction": 0.60},
    {"segment": "Loiter",      "duration_min": 8, "thrust_fraction": 0.40},
    {"segment": "Descent",     "duration_min": 5, "thrust_fraction": 0.20},
    {"segment": "Landing",     "duration_min": 2, "thrust_fraction": 0.10},
]

# -----------------------------
# SIMPLE FUEL MODEL:
# Fuel scales linearly from idle -> full thrust
# mdot = idle + fraction*(max-idle)
# -----------------------------
idle_flow = fuel_flow_kg_hr(ENGINE["idle_fuel_ml_min"], ENGINE["fuel_density_kg_L"])
max_flow  = fuel_flow_kg_hr(ENGINE["max_fuel_ml_min"],  ENGINE["fuel_density_kg_L"])

results = []

for seg in mission_profile:
    frac = seg["thrust_fraction"]

    # Thrust (linear model)
    thrust = ENGINE["idle_thrust_N"] + frac * (ENGINE["max_thrust_N"] - ENGINE["idle_thrust_N"])

    # Fuel flow (linear model)
    mdot = idle_flow + frac * (max_flow - idle_flow)

    # TSFC
    sfc = tsfc_kg_Nh(mdot, thrust)

    # Fuel used in that segment
    duration_hr = seg["duration_min"] / 60.0
    fuel_used = mdot * duration_hr

    results.append({
        "Segment": seg["segment"],
        "Duration (min)": seg["duration_min"],
        "Thrust fraction": frac,
        "Thrust (N)": round(thrust, 2),
        "Fuel flow (kg/hr)": round(mdot, 3),
        "SFC (kg/Nh)": round(sfc, 4),
        "Fuel Used (kg)": round(fuel_used, 3)
    })

df = pd.DataFrame(results)

total_fuel = df["Fuel Used (kg)"].sum()

print("=== Mission TSFC / Fuel Summary ===")
print(df.to_string(index=False))
print("\nTotal Mission Fuel Used (kg):", round(total_fuel, 3))
