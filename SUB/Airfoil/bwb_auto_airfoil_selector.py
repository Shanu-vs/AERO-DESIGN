import neuralfoil as nf
import aerosandbox as asb
import numpy as np
import os

# -------------------------------------------------------
# FLIGHT CONDITION (from your aircraft sizing)
# -------------------------------------------------------
Re = 1.768e6
CL_CRUISE = 0.1579
alpha = np.linspace(-8, 18, 500)

AIRFOIL_FOLDER = "SUB/Airfoil/Data"

# -------------------------------------------------------
# LOAD AIRFOIL FUNCTION
# -------------------------------------------------------
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
        raise ValueError("Invalid coordinate file")

    af = asb.Airfoil(name=name, coordinates=coords)
    af = af.to_kulfan_airfoil(n_weights_per_side=8)
    af = af.to_airfoil().repanel(n_points_per_side=160)

    return af

# -------------------------------------------------------
# ANALYZE ONE AIRFOIL
# -------------------------------------------------------
def analyze_airfoil(path, name):

    airfoil = load_airfoil(path, name)

    aero = nf.get_aero_from_airfoil(
        airfoil=airfoil,
        alpha=alpha,
        Re=Re
    )

    CL = aero["CL"]
    CD = aero["CD"]
    CM = aero["CM"]

    # Cruise condition
    idx = np.argmin(np.abs(CL - CL_CRUISE))

    CLc = CL[idx]
    CDc = CD[idx]
    CMc = CM[idx]
    alpha_c = alpha[idx]
    LD = CLc / CDc

    # Stall
    stall_idx = np.argmax(CL)
    CLmax = CL[stall_idx]
    alpha_stall = alpha[stall_idx]

    return {
        "name": name,
        "CLc": CLc,
        "CDc": CDc,
        "CMc": CMc,
        "alpha_cruise": alpha_c,
        "CLmax": CLmax,
        "alpha_stall": alpha_stall,
        "LD": LD
    }

# -------------------------------------------------------
# SCORING FUNCTIONS
# -------------------------------------------------------

# ROOT AIRFOIL → stability (Cm ≈ 0 or slightly positive)
def root_score(a):
    trim_score = 1 - abs(a["CMc"]) * 10          # best near zero
    drag_score = 1 / a["CDc"]                     # lower drag
    eff_score = a["LD"] / 40                      # normalize
    return 0.5*trim_score + 0.3*drag_score*0.01 + 0.2*eff_score

# MID AIRFOIL → smooth lift transition
def mid_score(a):
    return (a["LD"] / 40) + (a["CLmax"] / 2)

# TIP AIRFOIL → stall protection (LOWER CLmax preferred)
def tip_score(a):
    stall_safety = 1 / a["CLmax"]
    stability = 1 - abs(a["CMc"])
    return 0.7*stall_safety + 0.3*stability

# -------------------------------------------------------
# MAIN ANALYSIS
# -------------------------------------------------------
results = []

print("\nScanning airfoil database...\n")

for file in os.listdir(AIRFOIL_FOLDER):
    if file.endswith(".dat"):

        name = file.replace(".dat", "")
        path = os.path.join(AIRFOIL_FOLDER, file)

        try:
            data = analyze_airfoil(path, name)
            results.append(data)

            print(f"{name:10s} | CLmax={data['CLmax']:.2f} | CD={data['CDc']:.4f} | Cm={data['CMc']:.3f} | L/D={data['LD']:.1f}")

        except Exception as e:
            print(name, "failed:", e)

if len(results) < 3:
    print("\nNot enough valid airfoils!")
    exit()

# -------------------------------------------------------
# SELECT ROOT / MID / TIP
# -------------------------------------------------------
root = max(results, key=root_score)
remaining = [r for r in results if r != root]

tip = max(remaining, key=tip_score)
remaining.remove(tip)

mid = max(remaining, key=mid_score)

# -------------------------------------------------------
# OUTPUT
# -------------------------------------------------------
print("\n=======================================")
print(" FINAL BWB AIRFOIL DISTRIBUTION")
print("=======================================\n")

print(f"ROOT AIRFOIL : {root['name']}")
print(f"MID  AIRFOIL : {mid['name']}")
print(f"TIP  AIRFOIL : {tip['name']}")

print("\nRecommended span placement:")
print(f"0%  - 35% span  : {root['name']}")
print(f"35% - 70% span  : {mid['name']}")
print(f"70% - 100% span : {tip['name']}")

print("\nRecommended twist (washout):")
print("Root : +2°")
print("Mid  :  0°")
print("Tip  : -2.5°")

print("\n(Ensures trim stability + root-first stall + controllability)")


import json
import os

# -------------------------------------------------------
# SAVE SELECTED AIRFOILS INSIDE SUB/Airfoil/
# -------------------------------------------------------

AIRFOIL_SAVE_FOLDER = "SUB/Airfoil"
os.makedirs(AIRFOIL_SAVE_FOLDER, exist_ok=True)

selected_path = os.path.join(AIRFOIL_SAVE_FOLDER, "selected_airfoils.json")

selected_airfoils = {
    "root": root,
    "mid": mid,
    "tip": tip
}

with open(selected_path, "w") as f:
    json.dump(selected_airfoils, f, indent=4)

print(f"\nSelected airfoils saved to {selected_path}")
