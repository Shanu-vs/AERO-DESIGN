# =====================================================
# MODULE: airfoil_selector.py
# NeuralFoil-based airfoil selection for BWB UAV.
# Imports ALL parameters from airfoil_selection.py.
# =====================================================

import sys
import os
import json
import numpy as np

THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))

for p in [PROJECT_ROOT, THIS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Validate dependencies
for check, label in [
    (os.path.join(PROJECT_ROOT, "config.py"),         "config.py"),
    (os.path.join(THIS_DIR,     "airfoil_selection.py"), "airfoil_selection.py"),
]:
    if not os.path.exists(check):
        raise FileNotFoundError(f"\n[ERROR] {label} not found at:\n  {check}")

import config as cfg
from airfoil_selection import run_airfoil_selection

try:
    import neuralfoil as nf
    import aerosandbox as asb
    NEURALFOIL_AVAILABLE = True
except ImportError:
    NEURALFOIL_AVAILABLE = False
    print("[WARNING] neuralfoil / aerosandbox not installed.")
    print("          Run: pip install neuralfoil aerosandbox")
    print("          Exiting airfoil_selector.\n")
    sys.exit(0)

# --------------------------------------------------
# IMPORT DESIGN PARAMETERS
# --------------------------------------------------
_, chords, AFS = run_airfoil_selection(verbose=True)

CL_CRUISE  = AFS["CL_CRUISE"]
C_LI       = AFS["c_li"]
C_LMAX_NET = AFS["c_lmax_net"]
Re_root    = AFS["Re_root"]
Re_mid     = AFS["Re_mid"]
Re_tip     = AFS["Re_tip"]

print(f"\n[airfoil_selector] Design parameters:")
print(f"  CL_CRUISE (aircraft) = {CL_CRUISE:.4f}")
print(f"  c_li (section)       = {C_LI:.4f}")
print(f"  c_lmax_net           = {C_LMAX_NET:.4f}")
print(f"  Re_root = {Re_root:.3e} | Re_mid = {Re_mid:.3e} | Re_tip = {Re_tip:.3e}")

# --------------------------------------------------
# PATHS (relative to THIS file — works from any CWD)
# --------------------------------------------------
AIRFOIL_DATA = os.path.join(THIS_DIR, "..", "Airfoil", "Data")
AIRFOIL_OUT  = os.path.join(THIS_DIR, "..", "Airfoil")

if not os.path.isdir(AIRFOIL_DATA):
    raise FileNotFoundError(
        f"\n[ERROR] Airfoil data folder not found:\n  {os.path.abspath(AIRFOIL_DATA)}"
        f"\n  Expected: SUB/Airfoil/Data/*.dat"
    )

alpha = np.linspace(-8, 18, 500)


# =====================================================
# LOADER
# =====================================================
def load_airfoil(dat_path: str, name: str):
    coords = []
    with open(dat_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                try:
                    coords.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    pass
    coords = np.array(coords)
    if len(coords) < 50:
        raise ValueError(f"Only {len(coords)} points — file may be corrupt")
    af = asb.Airfoil(name=name, coordinates=coords)
    af = af.to_kulfan_airfoil(n_weights_per_side=8)
    af = af.to_airfoil().repanel(n_points_per_side=160)
    return af


# =====================================================
# ANALYZE AT A GIVEN REYNOLDS NUMBER
# =====================================================
def analyze_airfoil(path: str, name: str, Re: float) -> dict:
    airfoil = load_airfoil(path, name)
    aero    = nf.get_aero_from_airfoil(airfoil=airfoil, alpha=alpha, Re=Re)

    CL = np.array(aero["CL"])
    CD = np.array(aero["CD"])
    CM = np.array(aero["CM"])

    # Operating point matched to section design CL (c_li)
    idx     = int(np.argmin(np.abs(CL - C_LI)))
    CLc     = float(CL[idx])
    CDc     = float(CD[idx])
    CMc     = float(CM[idx])
    alpha_c = float(alpha[idx])
    LD      = CLc / CDc if CDc > 1e-6 else 0.0

    stall_idx   = int(np.argmax(CL))
    CLmax       = float(CL[stall_idx])
    alpha_stall = float(alpha[stall_idx])

    coords = airfoil.coordinates
    tc     = float(np.max(coords[:, 1]) - np.min(coords[:, 1]))

    return {
        "name":          name,
        "Re":            Re,
        "CLc":           CLc,
        "CDc":           CDc,
        "CMc":           CMc,
        "alpha_cruise":  alpha_c,
        "CLmax":         CLmax,
        "alpha_stall":   alpha_stall,
        "LD":            LD,
        "tc":            tc,
    }


# =====================================================
# SCORING — tailless BWB jet
# =====================================================

def root_score(a: dict) -> float:
    """
    Root: Cm ≤ 0 (pitch-up → unstable for tailless), high L/D,
    thick section for fuel and structure volume.
    """
    if a["CMc"] > 0.005:
        return -9999.0    # hard reject: any pitch-up at cruise
    cm_penalty  = abs(a["CMc"]) * 5.0
    ld_norm     = a["LD"] / 50.0
    thick_score = min(a["tc"] / 0.15, 1.0)
    stall_score = a["CLmax"] / C_LMAX_NET
    return 0.35*ld_norm + 0.30*(1.0 - cm_penalty) + 0.20*thick_score + 0.15*stall_score


def mid_score(a: dict) -> float:
    """Mid: smooth transition, operates near c_li, moderate Cm."""
    if a["CMc"] > 0.010:
        return -9999.0
    ld_norm  = a["LD"] / 50.0
    cl_match = 1.0 - abs(a["CLc"] - C_LI) / max(C_LI, 1e-6)
    cm_ok    = 1.0 - abs(a["CMc"]) * 3.0
    return 0.50*ld_norm + 0.30*cl_match + 0.20*cm_ok


def tip_score(a: dict) -> float:
    """
    Tip: CLmax LOWER than root → root stalls first → safe BWB.
    Lower Re, thin section preferred.
    """
    stall_protect = (C_LMAX_NET - a["CLmax"]) / C_LMAX_NET
    ld_norm       = a["LD"] / 40.0
    cm_ok         = 1.0 - abs(a["CMc"]) * 2.0
    return 0.55*stall_protect + 0.30*ld_norm + 0.15*cm_ok


# =====================================================
# MAIN SCAN
# =====================================================
print(f"\nScanning: {os.path.abspath(AIRFOIL_DATA)}\n")
print(f"{'Name':15s} | {'Re':>10s} | {'CLc':>6s} | {'CDc':>7s} | "
      f"{'Cm':>7s} | {'L/D':>6s} | {'CLmax':>6s} | {'t/c':>5s}")
print("-" * 90)

root_candidates, mid_candidates, tip_candidates = [], [], []

for file in sorted(os.listdir(AIRFOIL_DATA)):
    if not file.endswith(".dat"):
        continue
    name = file.replace(".dat", "")
    path = os.path.join(AIRFOIL_DATA, file)
    try:
        dr = analyze_airfoil(path, name, Re_root)
        dm = analyze_airfoil(path, name, Re_mid)
        dt = analyze_airfoil(path, name, Re_tip)
        root_candidates.append(dr)
        mid_candidates.append(dm)
        tip_candidates.append(dt)
        print(f"{name:15s} | {dr['Re']:.2e} | {dr['CLc']:.3f} | {dr['CDc']:.4f} | "
              f"{dr['CMc']:+.3f} | {dr['LD']:.1f} | {dr['CLmax']:.2f} | {dr['tc']:.3f}")
    except Exception as e:
        print(f"{name:15s} | FAILED: {e}")

if len(root_candidates) < 3:
    print("\n[ERROR] Need at least 3 valid airfoils.")
    sys.exit(1)

# =====================================================
# SELECTION
# =====================================================
root = max(root_candidates, key=root_score)

rem_mid = [r for r in mid_candidates if r["name"] != root["name"]]
rem_tip = [r for r in tip_candidates if r["name"] != root["name"]]

tip     = max(rem_tip, key=tip_score)
rem_mid = [r for r in rem_mid if r["name"] != tip["name"]]
mid     = max(rem_mid, key=mid_score)

# =====================================================
# PRINT RESULTS
# =====================================================
print("\n" + "=" * 62)
print("  BWB AIRFOIL SELECTION RESULTS")
print("=" * 62)

for label, af, score_fn in [("ROOT", root, root_score),
                              ("MID",  mid,  mid_score),
                              ("TIP",  tip,  tip_score)]:
    cm_flag = "✓ stable" if af["CMc"] <= 0.005 else "⚠ CHECK Cm"
    print(f"\n  {label} : {af['name']}")
    print(f"    Section Re    : {af['Re']:.3e}")
    print(f"    CL @ c_li     : {af['CLc']:.4f}  (target: {C_LI:.4f})")
    print(f"    CD            : {af['CDc']:.4f}")
    print(f"    Cm            : {af['CMc']:+.4f}  {cm_flag}")
    print(f"    L/D           : {af['LD']:.1f}")
    print(f"    CLmax         : {af['CLmax']:.3f}  (c_lmax_net: {C_LMAX_NET:.4f})")
    print(f"    α stall       : {af['alpha_stall']:.1f}°")
    print(f"    t/c           : {af['tc']:.3f}")
    print(f"    Score         : {score_fn(af):.4f}")

print("\n" + "-" * 62)
print("  SPAN DISTRIBUTION")
print(f"    0%–{cfg.SPAN_ROOT_END*100:.0f}% span  : {root['name']}")
print(f"   {cfg.SPAN_ROOT_END*100:.0f}%–{cfg.SPAN_MID_END*100:.0f}% span  : {mid['name']}")
print(f"   {cfg.SPAN_MID_END*100:.0f}%–100% span : {tip['name']}")
print(f"\n  TWIST:  Root {cfg.TWIST_ROOT_DEG:+.1f}°  |  Mid {cfg.TWIST_MID_DEG:+.1f}°  |  Tip {cfg.TWIST_TIP_DEG:+.1f}°")

print("\n  STALL PROGRESSION")
if root["CLmax"] > tip["CLmax"]:
    print(f"  ✓ Root ({root['CLmax']:.3f}) > Tip ({tip['CLmax']:.3f}) — root stalls first")
else:
    print(f"  ⚠ Tip ({tip['CLmax']:.3f}) >= Root ({root['CLmax']:.3f}) — tip may stall first!")

# =====================================================
# SAVE
# =====================================================
os.makedirs(AIRFOIL_OUT, exist_ok=True)
out_path = os.path.join(AIRFOIL_OUT, "selected_airfoils.json")
with open(out_path, "w") as f:
    json.dump({"design_parameters": AFS,
               "root": root, "mid": mid, "tip": tip}, f, indent=4)
print(f"\n  Saved → {os.path.abspath(out_path)}")
print("=" * 62)
