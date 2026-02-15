import numpy as np

# ======================================
# GIVEN VALUES (FROM YOUR DESIGN)
# ======================================

AR = 9.81
S  = 2.711

sweep_deg = -30
sweep_rad = np.deg2rad(sweep_deg)

# Airfoil Cm values (from your scan output)
CM_root = -0.010   # mh61
CM_tip  =  0.018   # E184

# Design values
CL_design = 0.6
St = 0.08     # slightly realistic static margin for BWB

# Zero lift angles (assume similar airfoils)
alpha_L0_root = -2.0
alpha_L0_tip  = -1.0   # E184 slightly different

# ======================================
# GEOMETRY CALCULATION
# ======================================

b = np.sqrt(AR * S)
c_bar = b / AR

# Assume taper ratio (you used earlier)
Gamma = 0.45

c_root = (2 * S) / (b * (1 + Gamma))
c_tip  = Gamma * c_root

# ======================================
# K1, K2 CALCULATION
# ======================================

K1 = 0.25 * (3 + 2*Gamma + Gamma**2) / (1 + Gamma + Gamma**2)
K2 = 1 - K1

# ======================================
# MAIN FORMULA
# ======================================

denom = 1.4e-5 * (AR ** 1.43) * sweep_rad

numerator = (K1 * CM_root + K2 * CM_tip) - CL_design * St

alpha_total = numerator / denom

alpha_geo = alpha_total - (alpha_L0_root - alpha_L0_tip)

# ======================================
# OUTPUT
# ======================================

print("===== DEBUG INFO =====")
print("Denominator:", denom)
print("Numerator:", numerator)

print("\n===== RESULTS =====")
print("Alpha Total:", round(alpha_total, 3), "deg")
print("Geometric Twist:", round(alpha_geo, 3), "deg")
