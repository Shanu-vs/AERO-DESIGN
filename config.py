# =====================================================
# GLOBAL CONFIG FILE (CHANGE VALUES ONLY HERE)
# =====================================================

#================ SAVE BEFORE RUNING =================

# ---------------------
# UAV BASIC PARAMETERS
# ---------------------
MTOW = 80.0                  # kg
WING_AREA = 1.2              # m^2
ASPECT_RATIO = 8.0
OSWALD_EFF = 0.8

# Raymer empty weight regression (jet UAV)
A = 0.86
B = 0.94

# ---------------------
# FLIGHT CONDITIONS
# ---------------------
CRUISE_ALTITUDE = 5000      # ft
CRUISE_SPEED = 52.5         # m/s
MAX_SPEED = 110.0            # m/s
STALL_SPEED = 35.0
CRUISE_RANGE = 141_750        # m  (speed * time)     
L_OVER_D = 12.0           # m/s

# ---------------------
# ATMOSPHERE
# ---------------------
RHO_SL = 1.225               # kg/m^3
G = 9.81                     # m/s^2

# ---------------------
# ENGINE PARAMETERS
# ---------------------
MAX_THRUST = 425.0           # N
TSFC = 0.157                 # 1/hr
ENGINE_EFF = 0.32

# ---------------------
# MISSION
# ---------------------
MISSION_TIME = 45 * 60       # seconds
LOITER_TIME = 5 * 60         # seconds

# ---------------------
# MISSION SEGMENT FRACTIONS
# ---------------------
WARMUP_TAKEOFF = 0.98
CLIMB = 0.97
DESCENT = 0.99
LANDING = 0.997


# ---------------------
# RESERVE
# ---------------------
reserve_fraction = 0.05       # 5%

# ---------------------
# LANDING
# ---------------------
STO = 304.8                      # m 
SL_ft = 1000                   # feet

# ---------------------
# CLIMBE
# ---------------------
ROC = 3                     # m/s 

# ---------------------
# AERODYNAMICS
# ---------------------
CD0 = 0.03
CL_MAX = 1.4

# ---------------------
# FILE PATHS
# ---------------------
ATMOSPHERE_CSV = "Atmosphere Model/atmosphere_data.csv"
RESULTS_DIR = "results/"
