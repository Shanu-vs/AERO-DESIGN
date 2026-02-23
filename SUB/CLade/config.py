# =====================================================
# BWB UAV — MASTER CONFIGURATION
# =====================================================
# All design parameters live here.
# Every module imports from this file — change values
# here only; never hardcode in sub-modules.
# =====================================================

# ---------------------
# UAV BASIC PARAMETERS
# ---------------------
MTOW            = 80.0          # kg   — Max Take-Off Weight
WING_AREA       = 2.711         # m²   — Reference wing area
ASPECT_RATIO    = 9.36          # —     — Wing aspect ratio
OSWALD_EFF      = 0.8           # —     — Oswald span efficiency

# ---------------------
# EMPTY WEIGHT REGRESSION (Raymer — jet UAV)
# We_est = A * MTOW^B
# ---------------------
RAYMER_A        = 0.6091
RAYMER_B        = 0.972         # = 1 - 0.028

# ---------------------
# FLIGHT CONDITIONS
# ---------------------
CRUISE_ALTITUDE = 5000          # ft
CRUISE_SPEED    = 55.5          # m/s
MAX_SPEED       = 110.0         # m/s
STALL_SPEED     = 23.0          # m/s  (1-g, sea level, clean)

# ---------------------
# ATMOSPHERE
# ---------------------
RHO_SL          = 1.225         # kg/m³  sea level
RHO_CRUISE      = 1.0556        # kg/m³  at 5000 ft (from atmosphere model)
MU_CRUISE       = 1.756e-5      # Pa·s   dynamic viscosity at 5000 ft
G               = 9.81          # m/s²

# ---------------------
# AERODYNAMICS
# ---------------------
CD0             = 0.03          # Zero-lift drag coefficient
CL_MAX          = 1.4           # Config value  ⚠ see NOTE below
#
# NOTE: CL_MAX = 1.4 is inconsistent with STALL_SPEED = 23 m/s.
# The stall equation gives CL_max = 0.893.
# The design tool uses 0.893 (from stall speed) as the aerodynamic truth.
# Update either STALL_SPEED = 18.37 m/s  OR  CL_MAX = 0.893 to reconcile.

# ---------------------
# ENGINE / PROPULSION
# ---------------------
MAX_THRUST      = 425.0         # N
TSFC            = 0.157         # 1/hr   — Thrust-Specific Fuel Consumption
ENGINE_EFF      = 0.32

# ---------------------
# FUEL
# ---------------------
FUEL_WEIGHT     = 18.14         # kg

# ---------------------
# MISSION
# ---------------------
MISSION_TIME    = 45 * 60       # s  — Total mission time (45 min)
LOITER_TIME     = 5  * 60       # s  — Loiter phase

# ---------------------
# MISSION SEGMENT WEIGHT FRACTIONS
# ---------------------
SEG_WARMUP_TAKEOFF  = 0.98
SEG_CLIMB           = 0.97
SEG_DESCENT         = 0.99
SEG_LANDING         = 0.997

# ---------------------
# RESERVE
# ---------------------
RESERVE_FRACTION    = 0.05      # 5% fuel reserve

# ---------------------
# TAKEOFF / LANDING
# ---------------------
STO             = 304.8         # m    — Field takeoff distance (config)
SL_ft           = 1000          # ft   — Field elevation

# ---------------------
# CLIMB
# ---------------------
ROC             = 3.0           # m/s  — Design rate of climb

# ---------------------
# STABILITY (BWB estimates)
# ---------------------
NP_FRACTION_MAC = 0.32          # Neutral point at 32% MAC from LE
CG_FRACTION_MAC = 0.27          # CG target at 27% MAC from LE

# ---------------------
# AIRFOIL SECTION CHORD RATIOS (BWB planform)
# ---------------------
CHORD_RATIO_ROOT = 2.0          # Root chord = 2.0 × MAC
CHORD_RATIO_MID  = 1.0          # Mid  chord = 1.0 × MAC
CHORD_RATIO_TIP  = 0.4          # Tip  chord = 0.4 × MAC

# ---------------------
# SPAN STATION BOUNDARIES
# ---------------------
SPAN_ROOT_END   = 0.35          # 0–35% span = root region
SPAN_MID_END    = 0.70          # 35–70% span = mid region
                                # 70–100% span = tip region

# ---------------------
# TWIST SCHEDULE (washout)
# ---------------------
TWIST_ROOT_DEG  = +2.0          # deg
TWIST_MID_DEG   =  0.0          # deg
TWIST_TIP_DEG   = -2.5          # deg

# ---------------------
# FILE PATHS
# ---------------------
ATMOSPHERE_CSV  = "Atmosphere Model/atmosphere_data.csv"
AIRFOIL_DATA    = "SUB/Airfoil/Data"
AIRFOIL_OUT     = "SUB/Airfoil"
RESULTS_DIR     = "results/"
