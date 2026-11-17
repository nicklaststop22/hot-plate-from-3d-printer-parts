"""
Reflow hot plate frame - parametric. Print in PA-CF (nylon carbon fiber).
Change the numbers in PARAMS and re-run:  python3 hotplate_frame.py
Outputs: hotplate_frame.stl

Layout (top view):
  [fan wall] | plate bay (aluminum plate floats on 4 bed-leveling screws+springs) | divider | THR board bay |
All units mm.
"""
import numpy as np
from manifold3d import Manifold, CrossSection
import trimesh

# ---------------- PARAMS ----------------
PLATE = 50.0          # aluminum plate width/depth (square)
PLATE_HOLE_INSET = 5  # plate mounting holes inset from plate edge
SPRING_GAP = 20.0     # air gap: tower top -> plate bottom (bed springs live here)
TOWER_TOP = 22.0      # tower height above z=0 (floor bottom)
TOWER_D = 12.0
M3_CLEAR = 3.4
NUT_AF = 6.5          # M3 nut across flats (+clearance)
NUT_DEPTH = 2.8

WALL = 3.0
FLOOR = 3.0
WALL_H = 30.0
FEET_H = 6.0

PLATE_BAY_X = 105.0   # inner length of plate bay
ELEC_BAY_X = 55.0     # inner length of electronics bay
INNER_Y = 90.0

# THR board standoffs - MEASURE YOUR BOARD and fix these (hole center to center)
BOARD_HOLE_X = 39.0
BOARD_HOLE_Y = 33.0
STANDOFF_D = 7.0
STANDOFF_H = 8.0
SELF_TAP = 2.6        # M3 self-tapping pilot

FAN = 40.0            # fan size (40x40 spare printer fan)
FAN_SCREW = 32.0
FAN_HOLE_D = 37.0
# ----------------------------------------

SEG = 48
def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
def cyl(x, y, z0, z1, d, seg=SEG):
    return Manifold.cylinder(z1 - z0, d / 2, d / 2, seg).translate([x, y, z0])
def cyl_x(x0, x1, y, z, d):  # cylinder along X
    return Manifold.cylinder(x1 - x0, d / 2, d / 2, SEG).rotate([0, 90, 0]).translate([x0, y, z])
def hexprism(x, y, z0, z1, af):
    r = af / np.sqrt(3)  # circumradius from across-flats
    return Manifold.cylinder(z1 - z0, r, r, 6).translate([x, y, z0])

X_TOTAL = WALL + PLATE_BAY_X + WALL + ELEC_BAY_X + WALL
Y_TOTAL = WALL + INNER_Y + WALL
DIV_X0 = WALL + PLATE_BAY_X
EB_X0 = DIV_X0 + WALL
PCX = WALL + PLATE_BAY_X * 0.55     # plate center pushed away from fan wall
PCY = Y_TOTAL / 2
PLATE_Z0 = TOWER_TOP + SPRING_GAP
FAN_Z = FLOOR + 2 + FAN / 2
FAN_WALL_H = FAN_Z + FAN / 2 + 3

# shell
shell = box(0, 0, 0, X_TOTAL, Y_TOTAL, WALL_H) - box(WALL, WALL, FLOOR, X_TOTAL - WALL, Y_TOTAL - WALL, WALL_H + 1)
shell += box(DIV_X0, 0, 0, DIV_X0 + WALL, Y_TOTAL, WALL_H)                       # divider
shell += box(0, PCY - FAN / 2 - 6, 0, WALL, PCY + FAN / 2 + 6, FAN_WALL_H)        # raised fan wall

# feet
for fx, fy in [(0, 0), (X_TOTAL - 12, 0), (0, Y_TOTAL - 12), (X_TOTAL - 12, Y_TOTAL - 12)]:
    shell += box(fx, fy, -FEET_H, fx + 12, fy + 12, 0)

# plate towers
h = PLATE / 2 - PLATE_HOLE_INSET
towers = [(PCX + sx * h, PCY + sy * h) for sx in (-1, 1) for sy in (-1, 1)]
for tx, ty in towers:
    shell += cyl(tx, ty, 0, TOWER_TOP, TOWER_D)
cuts = []
for tx, ty in towers:
    cuts.append(cyl(tx, ty, -1, TOWER_TOP + 1, M3_CLEAR))
    cuts.append(hexprism(tx, ty, -1, NUT_DEPTH, NUT_AF))      # nut trap from underside

# floor vents under plate (between towers)
for dx in (-10, -5, 0, 5, 10):
    cuts.append(box(PCX + dx - 1.5, PCY - 15, -1, PCX + dx + 1.5, PCY + 15, FLOOR + 1))

# fan opening + screws in fan wall
cuts.append(cyl_x(-1, WALL + 1, PCY, FAN_Z, FAN_HOLE_D))
for sy in (-1, 1):
    for sz in (-1, 1):
        cuts.append(cyl_x(-1, WALL + 1, PCY + sy * FAN_SCREW / 2, FAN_Z + sz * FAN_SCREW / 2, 3.2))

# wire notch in divider (heater/thermistor/fan leads)
cuts.append(box(DIV_X0 - 1, PCY - 7, WALL_H - 12, DIV_X0 + WALL + 1, PCY + 7, WALL_H + 1))
# fan lead notch along the long wall near fan
cuts.append(box(WALL + 6, Y_TOTAL - WALL - 1, WALL_H - 8, WALL + 14, Y_TOTAL + 1, WALL_H + 1))
# power + USB notch at far end
cuts.append(box(X_TOTAL - WALL - 1, PCY - 12, FLOOR + 4, X_TOTAL + 1, PCY + 12, FLOOR + 16))
# zip-tie strain relief slots near the power notch
for sy in (-1, 1):
    cuts.append(box(X_TOTAL - WALL - 12, PCY + sy * 16 - 2, -1, X_TOTAL - WALL - 8, PCY + sy * 16 + 2, FLOOR + 1))

# THR board standoffs
EBCX = EB_X0 + ELEC_BAY_X / 2
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = EBCX + sx * BOARD_HOLE_X / 2, PCY + sy * BOARD_HOLE_Y / 2
        shell += cyl(x, y, FLOOR, FLOOR + STANDOFF_H, STANDOFF_D)
        cuts.append(cyl(x, y, FLOOR + 1, FLOOR + STANDOFF_H + 1, SELF_TAP))
# vent slots under board
for dx in (-12, -6, 0, 6, 12):
    cuts.append(box(EBCX + dx - 1.2, PCY - 10, -1, EBCX + dx + 1.2, PCY + 10, FLOOR + 1))

for c in cuts:
    shell -= c

mesh = shell.to_mesh()
tm = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)
tm.export("hotplate_frame.stl")
print(f"frame {X_TOTAL:.0f} x {Y_TOTAL:.0f} x {FAN_WALL_H + FEET_H:.0f} mm, watertight={tm.is_watertight}, "
      f"plate bottom at z={PLATE_Z0:.0f}, plate edge->fan wall {PCX - PLATE/2 - WALL:.0f} mm, ->divider {DIV_X0 - (PCX + PLATE/2):.0f} mm")
