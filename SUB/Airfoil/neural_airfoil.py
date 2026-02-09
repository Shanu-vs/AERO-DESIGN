import neuralfoil as nf
import aerosandbox as asb
import numpy as np
import matplotlib.pyplot as plt

# Select an airfoil
airfoil = asb.Airfoil("naca4412")

# Angle of attack range
alpha = np.linspace(-5, 15, 60)   # degrees

# Run NeuralFoil
aero = nf.get_aero_from_airfoil(
    airfoil=airfoil,
    alpha=alpha,
    Re=200000,
)


CL = aero["CL"]
CD = aero["CD"]
CM = aero["CM"]

# Plot CL vs Alpha
plt.plot(alpha, CL)
plt.xlabel("Angle of Attack (deg)")
plt.ylabel("Lift Coefficient (CL)")
plt.title("NACA 4412 - NeuralFoil Prediction")
plt.grid()
plt.show()
