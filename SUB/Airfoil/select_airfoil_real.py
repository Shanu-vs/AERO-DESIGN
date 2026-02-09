import neuralfoil as nf
import aerosandbox as asb
import numpy as np
import os

# =========================================================
# BWB CRUISE CONDITION
# =========================================================
CL_required = 0.1625      # from your BWB calculation
Re = 1.768e6

AIRFOIL_FOLDER = "SUB/Airfoil/Data"

alpha = np.linspace(-8, 12, 400)


# =========================================================
# AIRFOIL LOADER (handles UIUC files safely)
# =========================================================
def load_airfoil(dat_path, name):

    coords = []

    with open(dat_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                try:
                    coords.append([float(parts[0]), float(parts[1])])
                except:
                    pass

    coords = np.array(coords)

    if len(coords) < 50:
        raise ValueError("Invalid airfoil")

    # smooth reconstruction
    af = asb.Airfoil(name=name, coordinates=coords)
    af = af.to_kulfan_airfoil(n_weights_per_side=8)
    af = af.to_airfoil().repanel(n_points_per_side=160)

    return af


# =========================================================
# ANALYSIS
# =========================================================
results = []

print("\nAnalyzing airfoils for BWB trim-stable cruise...\n")

for file in os.listdir(AIRFOIL_FOLDER):

    if file.endswith(".dat"):

        name = file.replace(".dat", "")
        path = os.path.join(AIRFOIL_FOLDER, file)

        try:
            print(f"Testing: {name}")

            airfoil = load_airfoil(path, name)

            aero = nf.get_aero_from_airfoil(
                airfoil=airfoil,
                alpha=alpha,
                Re=Re
            )

            CL = aero["CL"]
            CD = aero["CD"]
            CM = aero["CM"]

            # -------------------------------------------------
            # 1) Must reach required lift
            # -------------------------------------------------
            if np.min(CL) > CL_required or np.max(CL) < CL_required:
                print("   -> cannot generate required lift")
                continue

            # find cruise point
            idx = np.argmin(np.abs(CL - CL_required))

            cl = CL[idx]
            cd = CD[idx]
            cm = CM[idx]
            aoa = alpha[idx]

            # -------------------------------------------------
            # 2) BWB TRIM CONDITION (CRITICAL)
            # -------------------------------------------------
            # tailless aircraft must have near-zero moment
            if cm < -0.03:
                print(f"   -> rejected (too nose-down Cm = {cm:.3f})")
                continue

            results.append((name, cd, cm, aoa))

            print(f"   -> CD={cd:.5f}, Cm={cm:.3f}, AoA={aoa:.2f}°")

        except Exception as e:
            print(f"   -> {name} failed:", e)


# =========================================================
# RESULTS
# =========================================================
print("\n===================================")
print(" BEST AIRFOIL FOR BWB UAV ")
print("===================================")

if len(results) == 0:
    print("No trim-stable airfoil found.")
    exit()

# lowest drag wins
results.sort(key=lambda x: x[1])

for r in results:
    print(f"{r[0]:12s}  CD={r[1]:.5f}  Cm={r[2]:.3f}  AoA={r[3]:.2f}°")

best = results[0]

print("\n🏆 SELECTED BWB AIRFOIL:")
print(best[0])
