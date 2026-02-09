import neuralfoil as nf
import aerosandbox as asb
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# =========================================================
# UAV CONDITION
# =========================================================
Re = 1.768e6
CL_cruise = 0.1625
alpha = np.linspace(-8, 18, 400)

AIRFOILS = {
    "MH61": "SUB/Airfoil/Data/mh61.dat",
    "MH62": "SUB/Airfoil/Data/mh62.dat",
    "MH60": "SUB/Airfoil/Data/mh60.dat",
}

# =========================================================
# LOAD AIRFOIL
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

    af = asb.Airfoil(name=name, coordinates=coords)
    af = af.to_kulfan_airfoil(n_weights_per_side=8)
    af = af.to_airfoil().repanel(n_points_per_side=160)
    return af

# =========================================================
# ANALYZE AIRFOIL
# =========================================================
def analyze_airfoil(name):
    airfoil = load_airfoil(AIRFOILS[name], name)
    aero = nf.get_aero_from_airfoil(airfoil=airfoil, alpha=alpha, Re=Re)

    CL = aero["CL"]
    CD = aero["CD"]
    CM = aero["CM"]
    LD = CL / CD

    # Cruise
    cruise_idx = np.argmin(np.abs(CL - CL_cruise))

    # Stall
    stall_idx = np.argmax(CL)

    return {
        "name": name,
        "alpha": alpha,
        "CL": CL,
        "CD": CD,
        "CM": CM,
        "LD": LD,
        "alpha_cruise": alpha[cruise_idx],
        "CLc": CL[cruise_idx],
        "CDc": CD[cruise_idx],
        "CMc": CM[cruise_idx],
        "LDc": LD[cruise_idx],
        "alpha_stall": alpha[stall_idx],
        "CLmax": CL[stall_idx],
    }

# Pre-compute all airfoils
airfoil_data = {name: analyze_airfoil(name) for name in AIRFOILS}
current_airfoil = "MH61"
current_mode = 0

# =========================================================
# FIGURE LAYOUT
# =========================================================
fig = plt.figure(figsize=(14,7))

# Main graph (moved UP so labels not hidden)
ax = fig.add_axes([0.07,0.22,0.58,0.70])

# Right info panel
info_ax = fig.add_axes([0.68,0.45,0.30,0.45])
info_ax.axis("off")

# Bottom plot buttons
plot_labels = ["Lift","Drag","Moment","Polar","Efficiency"]
plot_buttons = []

for i in range(5):
    btn_ax = fig.add_axes([0.08 + i*0.115, 0.07, 0.10, 0.07])
    plot_buttons.append(Button(btn_ax, plot_labels[i]))

# Airfoil selection buttons
airfoil_buttons = {}
ypos = 0.33
for name in AIRFOILS:
    btn_ax = fig.add_axes([0.72, ypos, 0.22, 0.06])
    airfoil_buttons[name] = Button(btn_ax, name)
    ypos -= 0.08

# =========================================================
# INFO PANEL
# =========================================================
def update_text(d):
    info_ax.clear()
    info_ax.axis("off")

    text = f"""
AIRFOIL : {d['name']}

Reynolds Number : {Re:,.0f}

--- Cruise ---
AoA : {d['alpha_cruise']:.2f} deg
CL  : {d['CLc']:.3f}
CD  : {d['CDc']:.4f}
Cm  : {d['CMc']:.3f}
L/D : {d['LDc']:.1f}

--- Stall ---
CLmax       : {d['CLmax']:.2f}
Alpha_stall : {d['alpha_stall']:.2f} deg
"""
    info_ax.text(0,1,text,va='top',family='monospace',fontsize=11)

# =========================================================
# DRAW PLOTS
# =========================================================
def draw_plot(mode):
    global current_mode
    current_mode = mode

    ax.clear()
    d = airfoil_data[current_airfoil]

    if mode == 0:  # LIFT
        ax.plot(d["alpha"], d["CL"], linewidth=2)

        ax.scatter(d["alpha_cruise"], d["CLc"], color='red', s=90, label="Cruise")
        ax.scatter(d["alpha_stall"], d["CLmax"], color='orange', s=90, label="Stall")

        ax.legend(loc="upper left", fontsize=11, framealpha=0.9)

        ax.set_title("Lift Curve (CL vs AoA)")
        ax.set_xlabel("Angle of Attack (deg)")
        ax.set_ylabel("CL")

    elif mode == 1:  # DRAG
        ax.plot(d["alpha"], d["CD"], linewidth=2)
        ax.scatter(d["alpha_cruise"], d["CDc"], color='red', s=90, label="Cruise")
        ax.legend()
        ax.set_title("Drag Curve (CD vs AoA)")
        ax.set_xlabel("Angle of Attack (deg)")
        ax.set_ylabel("CD")

    elif mode == 2:  # MOMENT
        ax.plot(d["alpha"], d["CM"], linewidth=2)
        ax.axhline(0, linestyle="--")
        ax.scatter(d["alpha_cruise"], d["CMc"], color='red', s=90, label="Cruise")
        ax.legend()
        ax.set_title("Pitching Moment (Cm vs AoA)")
        ax.set_xlabel("Angle of Attack (deg)")
        ax.set_ylabel("Cm")

    elif mode == 3:  # POLAR
        ax.plot(d["CD"], d["CL"], linewidth=2)
        ax.scatter(d["CDc"], d["CLc"], color='red', s=90, label="Cruise")
        ax.legend()
        ax.set_title("Aerodynamic Polar")
        ax.set_xlabel("CD")
        ax.set_ylabel("CL")

    elif mode == 4:  # EFFICIENCY
        ax.plot(d["alpha"], d["LD"], linewidth=2)
        ax.scatter(d["alpha_cruise"], d["LDc"], color='red', s=90, label="Cruise")
        ax.legend()
        ax.set_title("Efficiency (L/D vs AoA)")
        ax.set_xlabel("Angle of Attack (deg)")
        ax.set_ylabel("L/D")

    ax.grid(True)
    update_text(d)
    fig.canvas.draw_idle()

# =========================================================
# BUTTON CALLBACKS
# =========================================================
def make_plot_callback(i):
    return lambda event: draw_plot(i)

for i, btn in enumerate(plot_buttons):
    btn.on_clicked(make_plot_callback(i))

def make_airfoil_callback(name):
    def callback(event):
        global current_airfoil
        current_airfoil = name
        draw_plot(current_mode)
    return callback

for name, btn in airfoil_buttons.items():
    btn.on_clicked(make_airfoil_callback(name))

# Initial plot
draw_plot(0)
plt.show()
