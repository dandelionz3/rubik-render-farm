# build_scene_gta6.py — GTA 6 versi Blender 3D penuh (vinyl-toy, fan-made).
# Scene prosedural dari primitif, tanpa .blend / aset impor. Pola: build_scene_zombie.py.
# Tiga set film-set (jalan Vice City x~0, gerbang penjara x=60, pantai x=120),
# 2 karakter vinyl-toy (Lucia + Jason) dengan rig empty (dibuat di animate_gta6.py),
# muscle car + helikopter (prop rig), lampu malam/senja/matahari terbit, kamera.
# Setting render B7 via env FS_*: samples 8, raytracing OFF, volumetrics tile 16,
# DOF ON, motion blur ON, subsurf 1, bevel 0. Engine-agnostic (Principled + lampu
# fisik) — animate_gta6.py boleh switch ke Cycles + CUDA via --engine cycles.
# Run:
#   blender -b --factory-startup -P build_scene_gta6.py -- <out.png> [--res 540 960]
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else "//gta6_preview.png"
RES_X, RES_Y = (540, 960)
if "--res" in args:
    i = args.index("--res")
    RES_X, RES_Y = int(args[i + 1]), int(args[i + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- render setup B7 (Eevee default; animate boleh override ke Cycles) ----------
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"


def _set(obj, attr, value):
    if hasattr(obj, attr):
        setattr(obj, attr, value)


_set(scene.eevee, "use_raytracing", os.environ.get("FS_RAY", "0") == "1")
_set(scene.eevee, "use_shadows", True)
_set(scene.eevee, "volumetric_tile_size", os.environ.get("FS_VOLTILE", "16"))
_set(scene.eevee, "volumetric_end", 60.0)
scene.eevee.taa_render_samples = int(os.environ.get("FS_SAMPLES", "8"))
scene.render.use_motion_blur = os.environ.get("FS_MB", "1") == "1"
_set(scene.render, "motion_blur_shutter", 0.5)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.043, 0.055, 0.102, 1.0)  # langit malam #0B0E1A
bg.inputs["Strength"].default_value = 0.9
WORLD_BG = bg  # animate_gta6.py meng-keyframe warna/strength per frame


# ---------- materials ----------
def mat(name, rgb, rough=0.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


def transparent(name, rgb, alpha):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Alpha"].default_value = alpha
    m.blend_method = "BLEND"
    return m


# palet Vice City (DESIGN.md)
SKIN_LUCIA = mat("SkinLucia", (0.83, 0.62, 0.47), 0.5)      # Latina
SKIN_JASON = mat("SkinJason", (0.79, 0.56, 0.37), 0.5)       # sawo matang #C98E5F
HAIR_DARK = mat("HairDark", (0.10, 0.08, 0.07), 0.55)
TOP_RED = mat("TopRed", (0.76, 0.15, 0.18), 0.55)            # crop top Lucia #C1272D
JEANS = mat("Jeans", (0.23, 0.35, 0.55), 0.6)                # jeans #3A5A8C
TANK_WHITE = mat("TankWhite", (0.93, 0.93, 0.90), 0.55)       # tank top Jason #EDEDE6
SHIRT_TEAL = mat("ShirtTeal", (0.12, 0.48, 0.42), 0.55)      # kemeja Hawaii #1F7A6B
SHIRT_ORANGE = mat("ShirtOrange", (0.91, 0.61, 0.30), 0.55)  # aksen oranye
PANTS_DARK = mat("PantsDark", (0.16, 0.16, 0.18), 0.6)
SHOE = mat("Shoe", (0.07, 0.07, 0.08), 0.5)
EYE_BLACK = mat("EyeBlack", (0.02, 0.02, 0.03), 0.2)
EYE_BROWN = mat("EyeBrown", (0.25, 0.14, 0.08), 0.2)
MOUTH = mat("Mouth", (0.35, 0.10, 0.12), 0.3)
TATTOO = mat("Tattoo", (0.08, 0.08, 0.10), 0.5)
DUFFEL = mat("Duffel", (0.12, 0.12, 0.14), 0.65)
ASPHALT = mat("Asphalt", (0.063, 0.071, 0.086), 0.25, metal=0.1)  # aspal basah glossy #101216
SIDEWALK = mat("Sidewalk", (0.20, 0.20, 0.22), 0.85)
BUILDING = mat("Building", (0.11, 0.12, 0.14), 0.9)
BUILDING2 = mat("Building2", (0.16, 0.13, 0.16), 0.9)
CONCRETE = mat("Concrete", (0.32, 0.31, 0.29), 0.9)
SAND = mat("Sand", (0.76, 0.66, 0.47), 1.0)
SEA = mat("Sea", (0.055, 0.29, 0.42), 0.15, metal=0.2)       # laut #0E4A6B
PALM_TRUNK = mat("PalmTrunk", (0.35, 0.26, 0.16), 0.8)
PALM_LEAF = mat("PalmLeaf", (0.10, 0.35, 0.18), 0.7)
POLE = mat("Pole", (0.15, 0.15, 0.16), 0.5, metal=0.6)
WIN_WARM = emissive("WinWarm", (1.0, 0.72, 0.38), 1.6)
WIN_COOL = emissive("WinCool", (0.45, 0.75, 1.0), 1.4)
WIN_DARK = mat("WinDark", (0.05, 0.06, 0.09), 0.4)
NEON_PINK = emissive("NeonPink", (1.0, 0.18, 0.53), 6.0)     # #FF2E88
NEON_CYAN = emissive("NeonCyan", (0.0, 0.90, 1.0), 6.0)      # #00E5FF
NEON_GOLD = emissive("NeonGold", (0.91, 0.64, 0.30), 5.0)    # #E8A34C
LAMP_GLOW = emissive("LampGlow", (1.0, 0.85, 0.55), 6.0)
BANK_GLOW = emissive("BankGlow", (1.0, 0.80, 0.45), 4.0)
SUN_DISC = emissive("SunDisc", (1.0, 0.60, 0.24), 8.0)       # matahari #FF9A3C
CAR_TEAL = mat("CarTeal", (0.08, 0.26, 0.29), 0.3, metal=0.5)  # muscle car #14424A
CAR_GLASS = mat("CarGlass", (0.05, 0.07, 0.10), 0.1, metal=0.8)
CAR_CHROME = mat("CarChrome", (0.7, 0.72, 0.75), 0.2, metal=0.9)
TIRE = mat("Tire", (0.03, 0.03, 0.03), 0.9)
HEADLIGHT = emissive("Headlight", (1.0, 0.95, 0.75), 8.0)
TAILLIGHT = emissive("Taillight", (1.0, 0.05, 0.05), 5.0)
UNDERGLOW = emissive("Underglow", (0.0, 0.90, 1.0), 3.0)
UNDERGLOW.blend_method = "BLEND"
UNDERGLOW.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
HELI_BODY = mat("HeliBody", (0.12, 0.13, 0.15), 0.4, metal=0.4)
HELI_ROTOR = mat("HeliRotor", (0.05, 0.05, 0.06), 0.4, metal=0.7)
STROBE_R = emissive("StrobeR", (1.0, 0.05, 0.05), 8.0)
STROBE_B = emissive("StrobeB", (0.05, 0.2, 1.0), 8.0)
RAIN_M = transparent("Rain", (0.7, 0.8, 0.9), 0.18)
GATE_METAL = mat("GateMetal", (0.25, 0.25, 0.28), 0.4, metal=0.8)
GAS_CANOPY = mat("GasCanopy", (0.75, 0.15, 0.18), 0.5)
PUMP = mat("Pump", (0.85, 0.85, 0.85), 0.4, metal=0.3)
ROAD_LINE = mat("RoadLine", (0.9, 0.9, 0.85), 0.6)


def smooth(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.select_set(False)


def block(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def ball(name, loc, size, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=32, ring_count=16)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def cylinder(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def cone(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def plane(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return o


def text_obj(name, body, loc, size, m, rot=(math.radians(90), 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.extrude = 0.015
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.resolution_u = 16
    try:
        t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    except Exception:
        pass
    t.data.materials.append(m)
    return t


# ---------- SET A: jalan Vice City (pusat x~0, jalan sepanjang sumbu X) ----------
block("ST_Ground", (0, 0, -0.1), (40, 20, 0.2), ASPHALT)
block("ST_Sidewalk", (0, 5.6, 0.03), (40, 3.0, 0.06), SIDEWALK)
# fasad gedung belakang (y=+7.5) + jendela emissive
_buildings = [(-15, 6.0, 6), (-8, 6.0, 8), (-1, 6.0, 6), (6, 7.0, 7), (13, 6.0, 5)]
for i, (bx, bw, bh) in enumerate(_buildings):
    block(f"ST_Bldg{i}", (bx, 7.5, bh / 2), (bw, 3.0, bh), BUILDING if i % 2 == 0 else BUILDING2)
    for wy in range(2):
        for wx in range(int(bw) - 1):
            warm = ((i + wx + wy) % 3) != 0
            plane(f"ST_Win{i}_{wx}_{wy}", (bx - bw / 2 + 0.9 + wx * 1.1, 5.98, 1.6 + wy * 2.0),
                  (0.55, 0.8), WIN_WARM if warm else (WIN_COOL if (i + wx) % 4 == 0 else WIN_DARK),
                  rot=(math.radians(90), 0, 0))
# gedung samping (menutup ujung jalan)
block("ST_BldgL", (-19.5, 0, 3.0), (3.0, 18, 6.0), BUILDING2)
block("ST_BldgR", (19.5, 0, 3.0), (3.0, 18, 6.0), BUILDING)
# rooftop di atas gedung tengah (S1: Lucia+Jason di tepi rooftop, z=6.0)
block("ST_RoofBldg", (0, 7.5, 3.0), (10, 3.0, 6.0), BUILDING2)
block("ST_RoofEdge", (0, 6.1, 6.05), (10, 0.25, 0.12), CONCRETE)
# papan neon: VICE CITY pink + OCEAN DR cyan + strip neon emas
text_obj("ST_NeonVice", "VICE CITY", (-8, 5.9, 6.2), 1.1, NEON_PINK)
text_obj("ST_NeonOcean", "OCEAN DR", (6, 5.9, 5.2), 0.8, NEON_CYAN)
plane("ST_NeonStrip", (-1, 5.98, 4.4), (5.0, 0.25), NEON_PINK, rot=(math.radians(90), 0, 0))
plane("ST_NeonStrip2", (13, 5.98, 3.6), (4.0, 0.22), NEON_CYAN, rot=(math.radians(90), 0, 0))
# tiang lampu jalan (x=-12,-6,0,6,12 ; y=+4.8)
for i, lx in enumerate((-12, -6, 0, 6, 12)):
    cylinder(f"ST_LampPole{i}", (lx, 4.8, 1.6), 0.07, 3.2, POLE)
    ball(f"ST_LampHead{i}", (lx, 4.55, 3.25), (0.16, 0.16, 0.12), LAMP_GLOW)
# palem (x=-14,-2,10 ; y=5.2)
for i, px in enumerate((-14, -2, 10)):
    cylinder(f"ST_PalmTrunk{i}", (px, 5.2, 1.5), 0.09, 3.0, PALM_TRUNK)
    for k in range(5):
        ang = k * math.radians(72)
        block(f"ST_PalmLeaf{i}_{k}", (px + 0.55 * math.cos(ang), 5.2 + 0.55 * math.sin(ang), 3.15),
              (0.9, 0.22, 0.04), PALM_LEAF, rot=(math.radians(18), 0, ang))
# pom bensin (S3): kanopi + 2 pompa di x=8..14, y=2..5
for i, px in enumerate((9.0, 12.5)):
    cylinder(f"ST_GasPole{i}", (px, 2.2, 1.6), 0.08, 3.2, POLE)
    cylinder(f"ST_GasPoleB{i}", (px, 4.6, 1.6), 0.08, 3.2, POLE)
block("ST_GasCanopy", (10.75, 3.4, 3.3), (6.5, 3.6, 0.3), GAS_CANOPY)
text_obj("ST_GasSign", "GAS", (10.75, 1.55, 3.3), 0.7, NEON_GOLD, rot=(math.radians(90), 0, 0))
for i, px in enumerate((9.5, 12.0)):
    block(f"ST_Pump{i}", (px, 3.4, 0.7), (0.5, 0.4, 1.4), PUMP)
    plane(f"ST_PumpScreen{i}", (px, 3.18, 1.0), (0.3, 0.3), NEON_CYAN, rot=(math.radians(90), 0, 0))
# bank (S4): fasad + pintu bercahaya + tulisan BANK di x=-11
block("ST_Bank", (-11, 7.5, 2.2), (6.0, 3.0, 4.4), BUILDING2)
plane("ST_BankDoor", (-11, 5.95, 1.4), (2.0, 2.6), BANK_GLOW, rot=(math.radians(90), 0, 0))
text_obj("ST_BankSign", "BANK", (-11, 5.9, 4.6), 0.8, NEON_GOLD)
# hujan tipis S4: 48 batang transparan di atas jalan (hidden s.d. S4)
RAIN_OBJS = []
for i in range(48):
    rx = -14 + (i % 12) * 2.6
    ry = -4 + (i // 12) * 3.2
    rz = 2.2 + (i % 4) * 0.5
    r = cylinder(f"ST_Rain{i}", (rx, ry, rz), 0.008, 1.2, RAIN_M)
    r.hide_render = True
    RAIN_OBJS.append(r)

# ---------- SET B: gerbang penjara (offset OX=60) ----------
OX = 60.0
block("PR_Ground", (OX, 0, -0.1), (20, 16, 0.2), CONCRETE)
# tembok: dua segmen + header di atas gerbang (gerbang di x=OX, lebar 3.6)
block("PR_WallL", (OX - 6.8, 0, 1.8), (6.4, 0.4, 3.6), CONCRETE)
block("PR_WallR", (OX + 6.8, 0, 1.8), (6.4, 0.4, 3.6), CONCRETE)
block("PR_WallTop", (OX, 0, 3.4), (3.6, 0.4, 0.8), CONCRETE)
# gerbang jeruji — bagian digabung ke GateRig di animate (engsel di x=OX-1.8)
GATE_HINGE = (OX - 1.8, 0, 0)
GATE_PARTS = []
GATE_PARTS.append(block("PR_GateTop", (OX, 0, 2.9), (3.6, 0.12, 0.12), GATE_METAL))
GATE_PARTS.append(block("PR_GateBottom", (OX, 0, 0.25), (3.6, 0.12, 0.12), GATE_METAL))
for i in range(7):
    GATE_PARTS.append(cylinder(f"PR_GateBar{i}", (OX - 1.5 + i * 0.5, 0, 1.55), 0.05, 2.7, GATE_METAL))
# matahari rendah di utara (belakang gerbang) — disc emissive
ball("PR_SunDisc", (OX, 13, 2.2), (1.5, 1.5, 1.5), SUN_DISC)
# tiang lampu penjara
cylinder("PR_LampPole", (OX + 4.5, -1.5, 1.6), 0.07, 3.2, POLE)
ball("PR_LampHead", (OX + 4.5, -1.5, 3.25), (0.16, 0.16, 0.12), LAMP_GLOW)

# ---------- SET C: pantai + jalan pesisir (offset OX2=120) ----------
OX2 = 120.0
block("BE_Sand", (OX2, 0, -0.1), (26, 16, 0.2), SAND)
plane("BE_Sea", (OX2, 9, 0.05), (26, 10), SEA, rot=(0, 0, 0))
# matahari terbit di atas laut (utara, rendah)
ball("BE_SunDisc", (OX2, 13, 2.0), (1.7, 1.7, 1.7), SUN_DISC)
# jalan pesisir di y=-4 + garis tengah putus-putus
block("BE_Road", (OX2, -4, 0.0), (26, 3.0, 0.08), ASPHALT)
for i in range(9):
    plane(f"BE_RoadLine{i}", (OX2 - 11 + i * 2.75, -4, 0.06), (1.2, 0.12), ROAD_LINE, rot=(0, 0, 0))
# palem pantai
for i, px in enumerate((OX2 - 10, OX2 + 11)):
    cylinder(f"BE_PalmTrunk{i}", (px, 1.8, 1.5), 0.09, 3.0, PALM_TRUNK)
    for k in range(5):
        ang = k * math.radians(72)
        block(f"BE_PalmLeaf{i}_{k}", (px + 0.55 * math.cos(ang), 1.8 + 0.55 * math.sin(ang), 3.15),
              (0.9, 0.22, 0.04), PALM_LEAF, rot=(math.radians(18), 0, ang))

# ---------- MUSCLE CAR (prop, di sekitar origin — CarRig di animate yang menggerakkan) ----------
CAR_PARTS = []
CAR_PARTS.append(block("CAR_Body", (0, 0, 0.45), (2.8, 1.3, 0.55), CAR_TEAL))
CAR_PARTS.append(block("CAR_Cabin", (-0.15, 0, 0.95), (1.4, 1.15, 0.5), CAR_GLASS))
CAR_PARTS.append(block("CAR_Hood", (1.15, 0, 0.68), (0.6, 1.2, 0.12), CAR_TEAL))
CAR_PARTS.append(block("CAR_BumperF", (1.45, 0, 0.35), (0.15, 1.3, 0.2), CAR_CHROME))
CAR_PARTS.append(block("CAR_BumperR", (-1.45, 0, 0.35), (0.15, 1.3, 0.2), CAR_CHROME))
for _wx, _wy in ((0.95, 0.62), (0.95, -0.62), (-0.95, 0.62), (-0.95, -0.62)):
    CAR_PARTS.append(cylinder(f"CAR_Wheel{_wx}_{_wy}", (_wx, _wy, 0.24), 0.26, 0.2, TIRE,
                              rot=(math.radians(90), 0, 0)))
for _hy in (0.42, -0.42):
    CAR_PARTS.append(ball(f"CAR_Head{_hy}", (1.48, _hy, 0.55), (0.09, 0.09, 0.09), HEADLIGHT))
    CAR_PARTS.append(ball(f"CAR_Tail{_hy}", (-1.48, _hy, 0.55), (0.08, 0.08, 0.08), TAILLIGHT))
CAR_PARTS.append(plane("CAR_Underglow", (0, 0, 0.06), (3.0, 1.6), UNDERGLOW, rot=(0, 0, 0)))
# lampu sorot depan mobil (spot, ikut CarRig; arah +X)
bpy.ops.object.light_add(type="SPOT", location=(1.5, 0, 0.55))
_head_spot = bpy.context.object
_head_spot.name = "CAR_HeadSpot"
_head_spot.data.energy = 0.0
_head_spot.data.spot_size = math.radians(50)
_head_spot.data.spot_blend = 0.5
_head_spot.data.color = (1.0, 0.95, 0.75)
_head_spot.rotation_euler = (math.radians(90), 0, math.radians(90))
CAR_PARTS.append(_head_spot)
HEAD_SPOT = _head_spot

# ---------- HELIKOPTER (prop, di sekitar origin — HeliRig di animate) ----------
HELI_PARTS = []
HELI_PARTS.append(ball("HELI_Body", (0, 0, 0), (0.9, 0.7, 0.65), HELI_BODY))
HELI_PARTS.append(ball("HELI_Nose", (0.85, 0, -0.05), (0.45, 0.45, 0.4), CAR_GLASS))
HELI_PARTS.append(cylinder("HELI_Tail", (-1.3, 0, 0.1), 0.12, 1.8, HELI_BODY, rot=(0, math.radians(90), 0)))
HELI_PARTS.append(block("HELI_Fin", (-2.1, 0, 0.35), (0.08, 0.1, 0.6), HELI_BODY))
HELI_PARTS.append(ball("HELI_StrobeR", (0.2, 0.72, -0.3), (0.08, 0.08, 0.08), STROBE_R))
HELI_PARTS.append(ball("HELI_StrobeB", (0.2, -0.72, -0.3), (0.08, 0.08, 0.08), STROBE_B))
# rotor utama — bagian diputar HeliRotor di animate
HELI_ROTOR_PARTS = []
for _a in (0, 90):
    HELI_ROTOR_PARTS.append(block(f"HELI_Rotor{_a}", (0, 0, 0.75), (3.4, 0.18, 0.05), HELI_ROTOR,
                                  rot=(0, 0, math.radians(_a))))
HELI_ROTOR_PARTS.append(cylinder("HELI_RotorHub", (0, 0, 0.72), 0.12, 0.18, HELI_ROTOR))
# lampu sorot helikopter (spot + cone, ikut HeliRig, arah bawah-depan)
bpy.ops.object.light_add(type="SPOT", location=(0.3, 0, -0.6))
_heli_spot = bpy.context.object
_heli_spot.name = "HELI_Spot"
_heli_spot.data.energy = 0.0
_heli_spot.data.spot_size = math.radians(35)
_heli_spot.data.spot_blend = 0.6
_heli_spot.data.color = (1.0, 0.95, 0.8)
_heli_spot.data.use_shadow = True
_heli_spot.rotation_euler = (math.radians(35), 0, 0)
HELI_PARTS.append(_heli_spot)
HELI_SPOT = _heli_spot
_heli_cone = cone("HELI_Cone", (0.3, -0.9, -2.2), 1.1, 3.2, transparent("HeliConeM", (1.0, 0.95, 0.8), 0.06),
                  rot=(math.radians(-25), 0, 0))
HELI_PARTS.append(_heli_cone)

# ---------- haze tipis (volume density 0.008) ----------
def haze(name, loc, scale):
    m = bpy.data.materials.new(name + "M")
    m.use_nodes = True
    nt = m.node_tree.nodes
    nt.remove(nt["Principled BSDF"])
    vol = nt.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.008
    vol.inputs["Color"].default_value = (0.85, 0.88, 0.95, 1.0)
    m.node_tree.links.new(vol.outputs["Volume"], nt["Material Output"].inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    h = bpy.context.object
    h.name = name
    h.scale = scale
    h.data.materials.append(m)
    return h


if os.environ.get("FS_VOL", "1") == "1":
    haze("ST_Haze", (0, 0, 2.0), (20, 10, 4))
    haze("BE_Haze", (OX2, 0, 2.0), (13, 8, 3))

# ---------- karakter vinyl-toy ----------
# Kepala ~40% tinggi, tiap bagian objek terpisah. Karakter menghadap -Y.
# Rig empty dibuat di animate_gta6.py.
CHARS = {}


def make_character(prefix, scale, base, skin_mat, top_mat, pants_mat,
                   hair_style, beard=False, bag=False, hawaiian=False):
    """hair_style: 'long' (Lucia) | 'short' (Jason)."""
    s = scale
    bx, by, bz = base
    hip_z = 0.48 * s
    sho_z = 1.12 * s
    sho_x = 0.38 * s
    head_z = 1.45 * s
    head_r = 0.275 * s

    def P(x, y, z):
        return (bx + x, by + y, bz + z)

    body, head, armL, armR, legL, legR = [], [], [], [], [], []
    for side, sx in (("L", -1), ("R", 1)):
        lst = legL if side == "L" else legR
        lst.append(block(f"{prefix}_Leg{side}", P(0.14 * sx * s, 0, 0.24 * s),
                         (0.17 * s, 0.2 * s, 0.42 * s), pants_mat))
        lst.append(block(f"{prefix}_Shoe{side}", P(0.14 * sx * s, -0.04 * s, 0.07 * s),
                        (0.2 * s, 0.3 * s, 0.12 * s), SHOE))
    # torso + kemeja Hawaii terbuka (Jason): panel teal + aksen oranye
    body.append(block(f"{prefix}_Torso", P(0, 0, 0.78 * s), (0.62 * s, 0.5 * s, 0.6 * s), top_mat))
    if hawaiian:
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Shirt{side}", P(0.20 * sx * s, -0.26 * s, 0.85 * s),
                              (0.16 * s, 0.04 * s, 0.5 * s), SHIRT_TEAL,
                              rot=(0, 0, math.radians(-12 * sx))))
            body.append(block(f"{prefix}_ShirtTrim{side}", P(0.20 * sx * s, -0.28 * s, 0.85 * s),
                              (0.05 * s, 0.04 * s, 0.5 * s), SHIRT_ORANGE,
                              rot=(0, 0, math.radians(-12 * sx))))
    # lengan (pivot di bahu) + tangan kulit
    for side, sx in (("L", -1), ("R", 1)):
        lst = armL if side == "L" else armR
        lst.append(block(f"{prefix}_Arm{side}", P(sho_x * sx, 0, sho_z - 0.28 * s),
                         (0.16 * s, 0.18 * s, 0.5 * s), top_mat))
        lst.append(ball(f"{prefix}_Hand{side}", P(sho_x * sx, 0, sho_z - 0.56 * s),
                        (0.09 * s,) * 3, skin_mat))
    # tato kecil di lengan kiri Lucia
    if prefix == "LUCIA":
        armL.append(block(f"{prefix}_Tattoo", P(-sho_x, -0.10 * s, sho_z - 0.35 * s),
                          (0.18 * s, 0.03 * s, 0.08 * s), TATTOO))
    # kepala + rambut + wajah
    head.append(ball(f"{prefix}_Head", P(0, 0, head_z), (head_r, head_r * 0.92, head_r), skin_mat))
    if hair_style == "long":
        head.append(ball(f"{prefix}_HairTop", P(0, 0.04 * s, head_z + 0.08 * s),
                         (head_r * 1.08, head_r * 1.0, head_r * 0.9), HAIR_DARK))
        head.append(block(f"{prefix}_HairBack", P(0, 0.20 * s, head_z - 0.15 * s),
                          (0.42 * s, 0.12 * s, 0.75 * s), HAIR_DARK))
        head.append(block(f"{prefix}_HairSideL", P(-0.26 * s, 0.05 * s, head_z - 0.1 * s),
                          (0.10 * s, 0.16 * s, 0.5 * s), HAIR_DARK))
        head.append(block(f"{prefix}_HairSideR", P(0.26 * s, 0.05 * s, head_z - 0.1 * s),
                          (0.10 * s, 0.16 * s, 0.5 * s), HAIR_DARK))
    else:
        head.append(ball(f"{prefix}_HairTop", P(0, 0.03 * s, head_z + 0.12 * s),
                         (head_r * 1.02, head_r * 0.95, head_r * 0.55), HAIR_DARK))
    eyes_black, eyes_red = [], []
    for side, sx in (("L", -1), ("R", 1)):
        eyes_black.append(ball(f"{prefix}_EyeB{side}", P(0.11 * sx * s, -0.235 * s, head_z + 0.03 * s),
                               (0.055 * s, 0.03 * s, 0.07 * s), EYE_BLACK))
        er = ball(f"{prefix}_EyeR{side}", P(0.11 * sx * s, -0.24 * s, head_z + 0.03 * s),
                  (0.055 * s, 0.032 * s, 0.07 * s), EYE_BROWN)
        er.hide_render = True
        eyes_red.append(er)
    head.extend(eyes_black)
    head.extend(eyes_red)
    head.append(block(f"{prefix}_Mouth", P(0, -0.25 * s, head_z - 0.13 * s),
                      (0.12 * s, 0.03 * s, 0.03 * s), MOUTH))
    if beard:
        head.append(block(f"{prefix}_Beard", P(0, -0.22 * s, head_z - 0.20 * s),
                          (0.3 * s, 0.06 * s, 0.10 * s), HAIR_DARK))
    for side, sx in (("L", -1), ("R", 1)):
        head.append(block(f"{prefix}_Brow{side}", P(0.11 * sx * s, -0.25 * s, head_z + 0.13 * s),
                          (0.12 * s, 0.03 * s, 0.03 * s), HAIR_DARK, rot=(0, 0, math.radians(-10 * sx))))
    # tas duffel gelap (ikut RootRig; plan flag "bag" yang menampilkan)
    bag_objs = []
    if bag:
        bag_objs.append(block(f"{prefix}_Duffel", P(0.42 * s, -0.05 * s, 0.55 * s),
                              (0.5 * s, 0.28 * s, 0.3 * s), DUFFEL))
        bag_objs.append(block(f"{prefix}_DuffelStrap", P(0.42 * s, -0.05 * s, 0.72 * s),
                              (0.5 * s, 0.28 * s, 0.05 * s), TATTOO))
        for b in bag_objs:
            b.hide_render = True
    info = {
        "base": Vector(base), "scale": s, "kind": prefix.lower(),
        "hip_z": hip_z, "sho_z": sho_z, "sho_x": sho_x, "head_z": head_z,
        "head_pivot_z": 1.18 * s,
        "body": body, "head": head, "armL": armL, "armR": armR,
        "legL": legL, "legR": legR,
        "eyes_black": eyes_black, "eyes_red": eyes_red,
        "mouth": head[[o.name for o in head].index(f"{prefix}_Mouth")],
        "bag_objs": bag_objs,
    }
    CHARS[prefix] = info
    return info


make_character("LUCIA", 0.98, (0, 0, 0), SKIN_LUCIA, TOP_RED, JEANS, "long", bag=True)
make_character("JASON", 1.04, (0, 0, 0), SKIN_JASON, TANK_WHITE, PANTS_DARK, "short",
               beard=True, bag=True, hawaiian=True)

# ---------- lampu ----------
def point_light(name, loc, color, energy, shadow=False):
    bpy.ops.object.light_add(type="POINT", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.shadow_soft_size = 0.5
    o.data.use_shadow = shadow
    return o


def area_light(name, loc, color, energy, size, rot, shadow=False):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.size = size
    o.data.use_shadow = shadow
    o.rotation_euler = rot
    return o


LIGHTS = {}
LIGHTS["neon_pink"] = point_light("NeonPinkLight", (-8, 5.0, 4.5), (1.0, 0.18, 0.53), 800.0)
LIGHTS["neon_cyan"] = point_light("NeonCyanLight", (6, 5.0, 4.0), (0.0, 0.90, 1.0), 800.0)
LIGHTS["street"] = point_light("StreetLight", (0, 4.4, 3.1), (1.0, 0.85, 0.55), 300.0)
LIGHTS["bank"] = point_light("BankLight", (-11, 6.5, 1.5), (1.0, 0.80, 0.45), 0.0)
LIGHTS["moon"] = area_light("MoonLight", (0, 6, 10), (0.55, 0.68, 1.0), 300.0, 18,
                            (math.radians(140), 0, 0), shadow=True)
LIGHTS["dusk"] = area_light("DuskLight", (OX, -8, 8), (1.0, 0.62, 0.35), 0.0, 16,
                            (math.radians(35), 0, 0))
LIGHTS["sun"] = area_light("SunLight", (OX2, 10, 6), (1.0, 0.60, 0.24), 0.0, 18,
                           (math.radians(120), 0, 0), shadow=True)
LIGHTS["fill"] = area_light("CameraFill", (0, -10, 6), (0.62, 0.72, 1.0), 250.0, 14,
                            (math.radians(55), 0, 0))
LIGHTS["head"] = HEAD_SPOT
LIGHTS["heli"] = HELI_SPOT
# strobe helikopter (point, ikut HeliRig di animate — posisi awal di badan heli)
bpy.ops.object.light_add(type="POINT", location=(0.2, 0.72, -0.3))
_strobe_r = bpy.context.object
_strobe_r.name = "HeliStrobeR"
_strobe_r.data.color = (1.0, 0.05, 0.05)
_strobe_r.data.energy = 0.0
HELI_PARTS.append(_strobe_r)
LIGHTS["strobe_r"] = _strobe_r
bpy.ops.object.light_add(type="POINT", location=(0.2, -0.72, -0.3))
_strobe_b = bpy.context.object
_strobe_b.name = "HeliStrobeB"
_strobe_b.data.color = (0.05, 0.2, 1.0)
_strobe_b.data.energy = 0.0
HELI_PARTS.append(_strobe_b)
LIGHTS["strobe_b"] = _strobe_b

# ---------- quality pass B7: subsurf 1 di semua bagian karakter, bevel 0 ----------
SUB = int(os.environ.get("FS_SUB", "1"))
for _info in CHARS.values():
    for _part in (_info["body"] + _info["head"] + _info["armL"] + _info["armR"]
                  + _info["legL"] + _info["legR"] + _info["bag_objs"]):
        if _part.type == "MESH" and SUB > 0:
            _s = _part.modifiers.new("Subdiv", "SUBSURF")
            _s.levels = 0
            _s.render_levels = SUB
# vinyl: clear-coat ringan di kepala + pakaian
for _m, _coat in ((SKIN_LUCIA, 0.5), (SKIN_JASON, 0.5), (TOP_RED, 0.3), (TANK_WHITE, 0.3),
                  (CAR_TEAL, 0.6)):
    _b = _m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in _b.inputs:
        _b.inputs["Coat Weight"].default_value = _coat
        _b.inputs["Coat Roughness"].default_value = 0.15

# ---------- kamera default (plan yang menggerakkan per frame) ----------
bpy.ops.object.camera_add(location=(0, -6.5, 1.7))
cam = bpy.context.object
cam.data.lens = 40
look = Vector((0, 0, 1.3)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = os.environ.get("FS_DOF", "1") == "1"
cam.data.dof.focus_distance = 6.5
cam.data.dof.aperture_fstop = 2.0
scene.camera = cam

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
