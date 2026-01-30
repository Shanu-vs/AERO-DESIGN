import math
import csv
from pathlib import Path

# ==============================
# CONSTANTS
# ==============================
g = 9.80665          # Gravity (m/s^2)
R = 287.05           # Specific gas constant for air (J/kg·K)
gamma = 1.4          # Ratio of specific heats

T0 = 288.15          # Sea level temperature (K)
P0 = 101325          # Sea level pressure (Pa)
L = -0.0065          # Temperature lapse rate (K/m)

h_tropopause = 11000  # Tropopause altitude (m)

# Mach numbers to evaluate
mach_values = [round(m, 2) for m in [0.1 + i*0.05 for i in range(9)]]  # 0.10 to 0.50

# ==============================
# ISA ATMOSPHERE FUNCTION
# ==============================
def isa_atmosphere(h):
    if h <= h_tropopause:
        T = T0 + L * h
        P = P0 * (T / T0) ** (-g / (L * R))
    else:
        T = T0 + L * h_tropopause
        P_tropopause = P0 * (T / T0) ** (-g / (L * R))
        P = P_tropopause * math.exp(-g * (h - h_tropopause) / (R * T))

    rho = P / (R * T)
    a = math.sqrt(gamma * R * T)

    return T, P, rho, a


# ==============================
# SAVE CSV IN SCRIPT DIRECTORY
# ==============================
current_dir = Path(__file__).parent
output_file = current_dir / "atmosphere_data.csv"

with open(output_file, mode="w", newline="") as file:
    writer = csv.writer(file)

    # Header
    header = [
        "Altitude_m",
        "Temperature_K",
        "Pressure_Pa",
        "Density_kg_m3",
        "Speed_of_Sound_m_s"
    ]

    # Add Mach speed headers
    for M in mach_values:
        header.append(f"UAV_Speed_M{M}_m_s")

    writer.writerow(header)

    # Data rows
    for h in range(0, 20001, 500):
        T, P, rho, a = isa_atmosphere(h)

        row = [h, T, P, rho, a]

        # Add speeds for each Mach number
        for M in mach_values:
            V = M * a
            row.append(V)

        writer.writerow(row)

print(f"✅ Atmosphere data with Mach speeds saved to: {output_file}")
