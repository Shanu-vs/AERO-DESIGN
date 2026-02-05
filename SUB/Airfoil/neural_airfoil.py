import numpy as np
import matplotlib.pyplot as plt
import aerosandbox as asb
import neuralfoil as nf

# =====================================================
# DESIGN PARAMETERS (JET UAV)
# =====================================================
RE = 1.7e6

ALPHA_CLEAN = np.linspace(-4, 8, 49)
ALPHA_FLAP  = np.linspace(-4, 12, 65)

FLAP_HINGE_X = 0.75
FLAP_DEFLECTION = 30  # degrees

# =====================================================
# CREATE AIRFOIL (IMPORTANT FIX)
# =====================================================
airfoil = asb.Airfoil.from_naca("63412")

# =====================================================
# CLEAN AIRFOIL ANALYSIS
# =====================================================
aero_clean = nf.get_aero_from_airfoil(
    airfoil=airfoil,
    alpha=ALPHA_CLEAN,
    Re=RE
)

CL_clean = aero_clean["CL"]
CD_clean = aero_clean["CD"]
CM_clean = aero_clean["CM"]
LD_clean = CL_clean / CD_clean

# =====================================================
# FLAPPED AIRFOIL ANALYSIS
# =====================================================
airfoil_flap = airfoil.add_flap(
    hinge_x=FLAP_HINGE_X,
    flap_angle=FLAP_DEFLECTION
)

aero_flap = nf.get_aero_from_airfoil(
    airfoil=airfoil_flap,
    alpha=ALPHA_FLAP,
    Re=RE
)

CL_flap = aero_flap["CL"]
CD_flap = aero_flap["CD"]
CM_flap = aero_flap["CM"]
LD_flap = CL_flap / CD_flap

# =====================================================
# PRINT KEY RESULTS
# =====================================================
idx_cruise = np.argmin(np.abs(CL_clean - 0.20))

print("\n===== JET UAV AIRFOIL (NeuralFoil) =====\n")

print("--- CRUISE (Clean) ---")
print(f"Alpha (deg)            : {ALPHA_CLEAN[idx_cruise]:.2f}")
print(f"CL                     : {CL_clean[idx_cruise]:.3f}")
print(f"CD                     : {CD_clean[idx_cruise]:.4f}")
print(f"L/D                    : {LD_clean[idx_cruise]:.1f}")
print(f"Cm                     : {CM_clean[idx_cruise]:.3f}")

print("\n--- TAKEOFF (Flapped) ---")
print(f"CL_max (flapped)       : {np.max(CL_flap):.2f}")
print(f"Alpha at CL_max (deg)  : {ALPHA_FLAP[np.argmax(CL_flap)]:.2f}")
print(f"ΔCL due to flap        : {np.max(CL_flap) - np.max(CL_clean):.2f}")

# =====================================================
# PLOTS
# =====================================================
plt.figure(figsize=(14, 10))

# CL vs Alpha
plt.subplot(2, 2, 1)
plt.plot(ALPHA_CLEAN, CL_clean, label="Clean")
plt.plot(ALPHA_FLAP, CL_flap, "--", label="Flap 30°")
plt.xlabel("Alpha (deg)")
plt.ylabel("CL")
plt.legend()
plt.grid(True)

# CD vs CL
plt.subplot(2, 2, 2)
plt.plot(CL_clean, CD_clean, label="Clean")
plt.plot(CL_flap, CD_flap, "--", label="Flap 30°")
plt.xlabel("CL")
plt.ylabel("CD")
plt.legend()
plt.grid(True)

# L/D vs CL
plt.subplot(2, 2, 3)
plt.plot(CL_clean, LD_clean, label="Clean")
plt.plot(CL_flap, LD_flap, "--", label="Flap 30°")
plt.xlabel("CL")
plt.ylabel("L/D")
plt.legend()
plt.grid(True)

# Cm vs Alpha
plt.subplot(2, 2, 4)
plt.plot(ALPHA_CLEAN, CM_clean, label="Clean")
plt.plot(ALPHA_FLAP, CM_flap, "--", label="Flap 30°")
plt.xlabel("Alpha (deg)")
plt.ylabel("Cm")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
