# FAST VARIANT of build_scene.py — quality knobs via env vars (FS_*). Generated from build_scene.py;
# do not hand-edit the scene itself here; regenerate after any change to build_scene.py.
# Rubik-pack style desk scene with the presenter cat, built in Blender from primitives (no imported assets).
# Layout follows the pack's WORLD block: a desk at night, a lamp cone as the key light, a mug, 3 books stacked
# like stairs, a binder clip, and a 5.7 cm Rubik's cube. One unit ~ 1.24 cm, so the cat is ~2.6 cm tall.
# Run from the command line:
#   blender -b --factory-startup -P build_scene.py -- <out.png> [--res 1920 1080]
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else "//scene_preview.png"
RES_X, RES_Y = (1920, 1080)
if "--res" in args:
    i = args.index("--res")
    RES_X, RES_Y = int(args[i + 1]), int(args[i + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- render setup (Eevee, 16:9 like the pack) ----------
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"
scene.eevee.taa_render_samples = 48

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.06, 0.04, 0.03, 1.0)  # dark warm room behind the desk, like the reference
bg.inputs["Strength"].default_value = 0.6


def mat(name, rgb, rough=0.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


# Muse ireng (was the red cat): black fur, dark hoodie, white shirt front,
# transparent round glasses, glowing red eyes, white claws, backwards black cap.
RED = mat("Fur", (0.03, 0.03, 0.035), 0.55)
NAVY = mat("Kimono", (0.05, 0.05, 0.09), 0.6)
WHITE = mat("Shirt", (0.92, 0.92, 0.9), 0.5)
BROWN = mat("Bag", (0.32, 0.18, 0.09), 0.6)
GOLD = mat("Gold", (0.95, 0.66, 0.2), 0.25, metal=1.0)
GREY = mat("Clip", (0.45, 0.46, 0.5), 0.3, metal=1.0)
BLACK = mat("Eye", (0.02, 0.02, 0.03), 0.2)
CAPM = mat("Cap", (0.02, 0.02, 0.025), 0.35)
CLAW = mat("Claw", (0.93, 0.91, 0.86), 0.4)
EYERED = bpy.data.materials.new("EyeRed")
EYERED.use_nodes = True
_er = EYERED.node_tree.nodes["Principled BSDF"]
_er.inputs["Base Color"].default_value = (1.0, 0.05, 0.05, 1.0)
_er.inputs["Emission Color"].default_value = (1.0, 0.02, 0.02, 1.0)
_er.inputs["Emission Strength"].default_value = 2.5
GLASS = bpy.data.materials.new("Glasses")
GLASS.use_nodes = True
_gl = GLASS.node_tree.nodes["Principled BSDF"]
_gl.inputs["Base Color"].default_value = (0.9, 0.92, 0.95, 1.0)
_gl.inputs["Roughness"].default_value = 0.05
_gl.inputs["Alpha"].default_value = 0.4
GLASS.blend_method = "BLEND"
# world
def wood_mat(name):
    """Polished warm wood like the reference: long grain bands, a little noise, and a soft gloss."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"  # stripes run along the desk, like planks
    wave.inputs["Scale"].default_value = 0.5
    wave.inputs["Distortion"].default_value = 5.0
    wave.inputs["Detail"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.25, 0.12, 0.055, 1.0)
    ramp.color_ramp.elements[1].color = (0.36, 0.19, 0.085, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.28  # polished: soft reflections of the lamp and props
    return m


DESK = wood_mat("Desk")
CUBIE = mat("Cubie", (0.02, 0.02, 0.025), 0.35)
SHADE = mat("LampShade", (0.8, 0.78, 0.7), 0.6)
MUG = mat("Mug", (0.9, 0.9, 0.88), 0.18)
COFFEE = mat("Coffee", (0.06, 0.03, 0.015), 0.08)
TIMER_RIM = mat("TimerRim", (0.6, 0.62, 0.66), 0.25, metal=1.0)
TIMER_GLASS = mat("TimerGlass", (0.02, 0.01, 0.01), 0.05)
DIGITS_OFF = mat("DigitsOff", (0.12, 0.02, 0.02), 0.4)
CLIP = mat("BinderClip", (0.03, 0.03, 0.03), 0.4)
BOOK_CREAM = mat("BookCream", (0.85, 0.8, 0.68), 0.6)
BOOK_BLUE = mat("BookBlue", (0.12, 0.25, 0.45), 0.6)
BOOK_ORANGE = mat("BookOrange", (0.75, 0.32, 0.12), 0.6)
INK = mat("Ink", (0.05, 0.05, 0.08), 0.5)
MOUTH = mat("Mouth", (0.12, 0.02, 0.03), 0.3)
EARIN = mat("EarInner", (0.38, 0.12, 0.12), 0.6)
WOOD = mat("Wood", (0.55, 0.36, 0.18), 0.5)
PURPLE = mat("Purple", (0.62, 0.25, 0.85), 0.35)
TIMER_BASE = mat("TimerBase", (0.04, 0.04, 0.05), 0.4)
TIMER_PAD = mat("TimerPad", (0.15, 0.35, 0.75), 0.3)
DIGITS = bpy.data.materials.new("Digits")
DIGITS.use_nodes = True
_e = DIGITS.node_tree.nodes["Principled BSDF"]
_e.inputs["Base Color"].default_value = (1.0, 0.1, 0.05, 1.0)
_e.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1.0)
_e.inputs["Emission Strength"].default_value = 6.0
STICKER = {
    "red": mat("StRed", (0.85, 0.12, 0.1), 0.35),
    "orange": mat("StOrange", (0.95, 0.45, 0.08), 0.35),
    "blue": mat("StBlue", (0.1, 0.3, 0.9), 0.35),
    "green": mat("StGreen", (0.1, 0.7, 0.2), 0.35),
    "white": mat("StWhite", (0.95, 0.95, 0.95), 0.35),
    "yellow": mat("StYellow", (0.95, 0.85, 0.15), 0.35),
}


def smooth(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.select_set(False)


def block(name, loc, size, bevel, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        bev = o.modifiers.new("Bevel", "BEVEL")
        bev.width = bevel
        bev.segments = 6
        bev.limit_method = "ANGLE"
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
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=48)
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


# ---------- the presenter cat (as in build_cat.py, ~2.1 units = 2.6 cm), standing left of the cube ----------
CAT = Vector((-3.4, -3.6, 0.0))


def at(v):
    return Vector(v) + CAT


# Compact vinyl-toy proportions: one big rounded head on a short body, no neck,
# stubby arms and legs set into the body. Muse ireng: black fur, dark hoodie over a
# white shirt front, black sneakers, transparent round glasses, glowing red eyes,
# white claws, and a backwards black cap (no cat ears, no bag, no paddle).
HEAD_PIVOT_Z = 0.92             # head turns and tilts about this height (top of the body)
SHOULDER = (0.38, 0.86)         # arm pivots: x offset and height
for side, sx in (("L", -1), ("R", 1)):
    block(f"Leg{side}", at((0.15 * sx, 0.0, 0.2)), (0.17, 0.2, 0.26), 0.07, RED)
    block(f"Shoe{side}", at((0.15 * sx, -0.04, 0.08)), (0.22, 0.3, 0.16), 0.06, NAVY)
    block(f"Sole{side}", at((0.15 * sx, -0.04, 0.02)), (0.24, 0.32, 0.04), 0.02, WHITE)
block("Torso", at((0, 0, 0.62)), (0.6, 0.48, 0.6), 0.2, RED)
block("Kimono", at((0, -0.01, 0.6)), (0.64, 0.52, 0.52), 0.18, NAVY)
block("ShirtFront", at((0, -0.265, 0.62)), (0.2, 0.02, 0.4), 0.04, WHITE)
for side, sx in (("L", -1), ("R", 1)):
    block(f"Arm{side}", at((SHOULDER[0] * sx, -0.02, 0.66)), (0.16, 0.18, 0.3), 0.07, RED)
    block(f"Sleeve{side}", at((SHOULDER[0] * sx, 0.0, 0.82)), (0.22, 0.24, 0.16), 0.07, NAVY)
    ball(f"Paw{side}", at((0.39 * sx, -0.03, 0.5)), (0.09, 0.09, 0.09), RED)
    # three small white claws on the front of each paw (face is -y)
    for k, (cx, cz) in enumerate(((-0.03, 0.53), (0.0, 0.5), (0.03, 0.47))):
        cone(f"Claw{side}{k}", at((0.39 * sx + cx, -0.12, cz)), 0.02, 0.06, CLAW, rot=(math.radians(90), 0, 0))
block("Head", at((0, 0, 1.18)), (0.84, 0.66, 0.64), 0.28, RED)
for side, sx in (("L", -1), ("R", 1)):
    ball(f"Eye{side}", at((0.18 * sx, -0.32, 1.2)), (0.06, 0.035, 0.08), EYERED)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.02, location=at((0.18 * sx, -0.35, 1.2)), rotation=(math.radians(90), 0, 0))
    g = bpy.context.object
    g.name = f"Glasses{side}"
    g.data.materials.append(GLASS)
    block(f"Brow{side}", at((0.17 * sx, -0.34, 1.37)), (0.17, 0.035, 0.045), 0.015, BLACK, rot=(0, math.radians(-12 * sx), 0))
block("GlassesBridge", at((0, -0.36, 1.22)), (0.1, 0.02, 0.02), 0.0, GLASS)
ball("Nose", at((0, -0.34, 1.1)), (0.035, 0.025, 0.025), BLACK)
# small mouth under the nose; animate.py scales it per expression (smile, grimace, "O")
block("Mouth", at((0, -0.33, 1.02)), (0.1, 0.03, 0.035), 0.012, MOUTH)
# backwards black cap: dome sunk into the top of the head, brim pointing back (+y)
ball("CapDome", at((0, 0.02, 1.47)), (0.46, 0.4, 0.3), CAPM)
block("CapBrim", at((0, 0.42, 1.45)), (0.55, 0.34, 0.05), 0.02, CAPM, rot=(math.radians(-8), 0, 0))
ball("CapButton", at((0, 0.02, 1.76)), (0.05, 0.05, 0.04), CAPM)
for i, (x, y, z) in enumerate(((0.0, 0.27, 0.38), (0.08, 0.33, 0.52), (0.12, 0.33, 0.68))):
    ball(f"Tail{i}", at((x, y, z)), (0.08, 0.08, 0.08), RED)

# ---------- desk ----------
# a thick desktop slab (top at z=0) that ends behind the props; beyond it the room falls into darkness
block("Desk", (0.0, 0.0, -0.6), (48.0, 30.0, 1.2), 0.1, DESK)

# ---------- Rubik's cube: 27 black cubies with stickers on the outside faces (5.7 units ~ 4.6 cat units) ----------
CELL = 1.5
CUBE_C = Vector((0.0, 0.0, CELL * 1.5))  # sits on the desk
FACE_COLOUR = {
    (1, 0, 0): "red", (-1, 0, 0): "orange",
    (0, 1, 0): "blue", (0, -1, 0): "green",
    (0, 0, 1): "white", (0, 0, -1): "yellow",
}
for x in (-1, 0, 1):
    for y in (-1, 0, 1):
        for z in (-1, 0, 1):
            loc = CUBE_C + Vector((x, y, z)) * CELL
            block(f"Cubie{x}{y}{z}", loc, (CELL * 0.96,) * 3, 0.08, CUBIE)
            for n, colour in FACE_COLOUR.items():
                nv = Vector(n)
                if (nv.x and x == nv.x) or (nv.y and y == nv.y) or (nv.z and z == nv.z):
                    bpy.ops.mesh.primitive_plane_add(size=CELL * 0.78, location=loc + nv * (CELL * 0.49))
                    st = bpy.context.object
                    st.name = f"Sticker{colour}"
                    st.rotation_euler = nv.to_track_quat("Z", "Y").to_euler()
                    st.data.materials.append(STICKER[colour])

# ---------- three books stacked like stairs, the top one with DANDELIONZ on its cover ----------
BOOK_X = 4.2
# Sizes are full sizes, so each book's centre is half its height above the one below: flush, no gaps.
BOOKS = [  # (name, x, y, width, depth, height, material)
    ("BookBottom", BOOK_X, 0.6, 3.2, 2.4, 0.55, BOOK_BLUE),
    ("BookMiddle", BOOK_X + 0.4, 0.5, 2.9, 2.2, 0.5, BOOK_ORANGE),
    ("BookTop", BOOK_X + 0.8, 0.4, 2.7, 2.0, 0.45, BOOK_CREAM),
]
_z = 0.0
BOOK_MID_Z = []
for name, bx, by, bw, bd, bh, bm in BOOKS:
    block(name, (bx, by, _z + bh / 2), (bw, bd, bh), 0.04, bm)
    BOOK_MID_Z.append(_z + bh / 2)
    _z += bh


BOLD_FONT = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def text(body, loc, size, m, rot=(math.radians(90), 0, 0), font=None, bevel=0.0):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = body
    t.data.extrude = 0.02
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.resolution_u = 24  # smooth letter curves (HD)
    if font is not None:
        t.data.font = font
    if bevel:
        t.data.bevel_depth = bevel
        t.data.bevel_resolution = 4
    t.data.materials.append(m)
    return t


# name on the top book's front cover (faces the camera); the blue book reads ALGORITHMS
# spines face the camera, as in the reference (PATIENCE / ALGORITHMS / CUBING 101); the top one carries the name
# text sits 0.01 in front of each spine so it reads but casts no gap shadow; baseline offset centres the caps
text("DANDELIONZ", (BOOK_X + 0.8, 0.4 - 1.0 - 0.01, BOOK_MID_Z[2] - 0.12), 0.32, INK)
text("ALGORITHMS", (BOOK_X + 0.4, 0.5 - 1.1 - 0.01, BOOK_MID_Z[1] - 0.1), 0.28, BOOK_CREAM)
text("CUBING 101", (BOOK_X, 0.6 - 1.2 - 0.01, BOOK_MID_Z[0] - 0.1), 0.28, BOOK_CREAM)

# ---------- mug and binder clip on the desk ----------
# mug sits behind, top-left of the cube, as in the reference (not in the foreground)
def hd(o, levels=2):
    """High detail: subdivision smoothing on top of the base mesh."""
    s = o.modifiers.new("Subdiv", "SUBSURF")
    s.levels = 1
    s.render_levels = levels
    return o


# HD ceramic mug: smooth body, rolled rim, coffee inside, smooth handle
MUG_C = Vector((-6.4, 5.5, 0.0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=1.8, location=MUG_C + Vector((0, 0, 0.9)), vertices=128)
mug = bpy.context.object
mug.name = "Mug"
mug.data.materials.append(MUG)
_mb = mug.modifiers.new("Bevel", "BEVEL")
_mb.width = 0.06
_mb.segments = 6
smooth(mug)
bpy.ops.mesh.primitive_torus_add(major_radius=0.82, minor_radius=0.045, location=MUG_C + Vector((0, 0, 1.8)), major_segments=128, minor_segments=24)
bpy.context.object.name = "MugRim"
bpy.context.object.data.materials.append(MUG)
smooth(bpy.context.object)
bpy.ops.mesh.primitive_cylinder_add(radius=0.76, depth=0.02, location=MUG_C + Vector((0, 0, 1.62)), vertices=128)
bpy.context.object.name = "Coffee"
bpy.context.object.data.materials.append(COFFEE)
bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.12, location=MUG_C + Vector((1.18, 0, 0.95)),
                                 rotation=(math.radians(90), 0, 0), major_segments=96, minor_segments=32)
handle = bpy.context.object
handle.name = "MugHandle"
handle.data.materials.append(MUG)
smooth(handle)
hd(handle)
block("BinderClipBody", (2.9, -3.9, 0.2), (1.2, 0.4, 0.4), 0.07, CLIP)
block("BinderClipWing", (2.9, -3.9, 0.55), (1.1, 0.3, 0.4), 0.08, CLIP)

# speedcube timer on the left: black base, blue touch pad, red 7-segment-style digits facing the camera
# HD speedcube timer: a smooth rounded body, two touch pads with rims, a glossy display window in front
# with sharp bold digits and faint unlit "88.88" segments behind them, like a real 7-segment display
TIMER = Vector((-6.0, 0.6, 0.0))
hd(block("TimerBase", TIMER + Vector((0, 0, 0.22)), (3.0, 1.8, 0.44), 0.16, TIMER_BASE))
for _px in (-0.75, 0.75):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.05, location=TIMER + Vector((_px, 0.2, 0.465)), vertices=96)
    _pad = bpy.context.object
    _pad.name = "TimerPad"
    _pad.data.materials.append(TIMER_PAD)
    smooth(_pad)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.56, minor_radius=0.03, location=TIMER + Vector((_px, 0.2, 0.47)), major_segments=96, minor_segments=16)
    bpy.context.object.name = "TimerPadRim"
    bpy.context.object.data.materials.append(TIMER_RIM)
    smooth(bpy.context.object)
hd(block("TimerWindow", TIMER + Vector((0, -0.9, 0.22)), (1.7, 0.04, 0.34), 0.03, TIMER_GLASS))
text("88.88", (TIMER.x, TIMER.y - 0.925, 0.11), 0.3, DIGITS_OFF, font=BOLD_FONT)
text("00.00", (TIMER.x, TIMER.y - 0.93, 0.11), 0.3, DIGITS, font=BOLD_FONT, bevel=0.004)

# ---------- desk lamp: arm and shade on the right, its cone is the key light ----------
LAMP = Vector((10.0, 3.5, 0.0))
cylinder("LampBase", LAMP + Vector((0, 0, 0.2)), 1.3, 0.4, SHADE)
cylinder("LampArm", LAMP + Vector((0, 0, 4.0)), 0.18, 8.0, SHADE)
cone("LampShade", LAMP + Vector((-1.2, 0, 8.4)), 1.9, 2.2, SHADE, rot=(math.radians(40), 0, math.radians(0)))
bpy.ops.object.light_add(type="SPOT", location=LAMP + Vector((-1.2, 0, 6.4)))
lamp = bpy.context.object
lamp.name = "LampCone"
lamp.data.energy = 14000
lamp.data.spot_size = math.radians(95)
lamp.data.spot_blend = 0.6
lamp.data.color = (1.0, 0.86, 0.66)
target = Vector((0.0, 0.0, 2.0))
lamp.rotation_euler = (target - lamp.location).to_track_quat("-Z", "Y").to_euler()

# warm soft bounce from above and in front, like the reference
bpy.ops.object.light_add(type="AREA", location=(0.0, -6.0, 14.0))
bounce = bpy.context.object
bounce.data.energy = 400
bounce.data.size = 14
bounce.data.color = (1.0, 0.85, 0.7)
bounce.rotation_euler = (math.radians(20), 0, 0)

# soft fill from the front-left so the cat's face reads
bpy.ops.object.light_add(type="AREA", location=(-6.0, -20.0, 10.0))
fill = bpy.context.object
fill.data.energy = 900
fill.data.size = 12
fill.data.color = (1.0, 0.82, 0.62)
fill.rotation_euler = (math.radians(60), 0, math.radians(-10))

# ---------- environment and extra light, like the reference ----------
def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


# cool rim light from behind: outlines the cat, the cube edges and the books against the dark room
bpy.ops.object.light_add(type="AREA", location=(-2.0, 14.0, 9.0))
rim = bpy.context.object
rim.name = "RimLight"
rim.data.energy = 2200
rim.data.size = 8
rim.data.color = (0.62, 0.75, 1.0)
rim.rotation_euler = (Vector((-1.0, 0.0, 1.5)) - rim.location).to_track_quat("-Z", "Y").to_euler()

# the lamp's bulb glows inside the shade (the visible source of the key light)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=LAMP + Vector((-1.2, 0, 7.0)), segments=32, ring_count=16)
bulb = bpy.context.object
bulb.name = "LampBulb"
bulb.data.materials.append(emissive("Bulb", (1.0, 0.85, 0.6), 30.0))

# background bokeh: small warm and cool lights far behind the desk; the camera's shallow focus turns them into discs
BOKEH_COLOURS = [(1.0, 0.72, 0.4), (1.0, 0.55, 0.3), (0.55, 0.7, 1.0), (1.0, 0.85, 0.6)]
_bseed = 7
for i in range(36):
    _bseed = (_bseed * 1103515245 + 12345) % 2147483648
    bx = -34 + (_bseed % 6800) / 100.0
    _bseed = (_bseed * 1103515245 + 12345) % 2147483648
    bz = 3.0 + (_bseed % 1500) / 100.0
    _bseed = (_bseed * 1103515245 + 12345) % 2147483648
    by = 26.0 + (_bseed % 1600) / 100.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18 + (i % 4) * 0.06, location=(bx, by, bz), segments=16, ring_count=8)
    bk = bpy.context.object
    bk.name = f"Bokeh{i}"
    bk.data.materials.append(emissive(f"BokehM{i}", BOKEH_COLOURS[i % 4], 6.0 + (i % 3) * 3.0))

# dust motes floating in the lamp beam; animate.py drifts them each frame (DUST_BASE holds their rest positions)
DUST_M = emissive("Dust", (1.0, 0.9, 0.75), 3.0)
DUST_BASE = []
_dseed = 11
for i in range(70):
    pos = []
    for lo, hi in ((-3.0, 9.0), (-3.5, 4.5), (1.0, 9.5)):
        _dseed = (_dseed * 1103515245 + 12345) % 2147483648
        pos.append(lo + (hi - lo) * (_dseed % 10000) / 10000.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=pos, segments=8, ring_count=4)
    d = bpy.context.object
    d.name = f"Dust{i}"
    d.data.materials.append(DUST_M)
    DUST_BASE.append((d.name, tuple(pos)))

# ---------- quality pass (matches the reference's smooth vinyl look) ----------
def _set(obj, attr, value):
    """Set a render setting if this Blender version has it (Eevee settings move between versions)."""
    if hasattr(obj, attr):
        setattr(obj, attr, value)


# 1. smooth shapes: subdivision on every cat part (bevelled blocks become soft vinyl forms)
CAT_PART_NAMES = {
    "LegL", "LegR", "ShoeL", "ShoeR", "SoleL", "SoleR", "Torso", "Kimono", "ShirtFront",
    "ArmL", "ArmR", "SleeveL", "SleeveR", "PawL", "PawR", "Head", "EyeL", "EyeR", "Nose", "Mouth", "BrowL", "BrowR",
    "Tail0", "Tail1", "Tail2", "CapDome", "CapBrim", "CapButton",
    "ClawL0", "ClawL1", "ClawL2", "ClawR0", "ClawR1", "ClawR2",
}
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.split(".")[0] in CAT_PART_NAMES:
        sub = o.modifiers.new("Subdiv", "SUBSURF")
        sub.levels = 1
        sub.render_levels = int(os.environ.get("FS_SUB", "2"))
# props: more bevel segments so cube and book edges catch a soft highlight
if os.environ.get("FS_BEVEL", "1") == "1":
    for o in bpy.data.objects:
        for m in o.modifiers:
            if m.type == "BEVEL":
                m.segments = max(m.segments, 10)

# 2. vinyl: a thin clear coat on the toy and the stickers, a little light through the fur
for mt, coat, sss in ((RED, 0.5, 0.12), (NAVY, 0.35, 0.0), (WHITE, 0.3, 0.0), (CAPM, 0.4, 0.0), (PURPLE, 0.5, 0.0), (EARIN, 0.3, 0.0),
                      (CUBIE, 0.6, 0.0), *[(m, 0.7, 0.0) for m in STICKER.values()]):
    b = mt.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.12
    if sss and "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.15, 0.1)

# 3. light: ray-traced reflections, soft shadows from the lamp, a thin haze so the lamp cone shows
_set(scene.eevee, "use_raytracing", os.environ.get("FS_RAY", "0") == "1")
_set(scene.eevee, "use_shadows", True)
_set(scene.eevee, "shadow_ray_count", 2)
_set(scene.eevee, "shadow_step_count", 8)
_set(scene.eevee, "volumetric_tile_size", os.environ.get("FS_VOLTILE", "8"))
_set(scene.eevee, "volumetric_end", 60.0)
scene.eevee.taa_render_samples = int(os.environ.get("FS_SAMPLES", "16"))
lamp.data.shadow_soft_size = 0.8
if os.environ.get("FS_VOL", "1") == "1":
    haze_m = bpy.data.materials.new("Haze")
    haze_m.use_nodes = True
    _hn = haze_m.node_tree.nodes
    _hn.remove(_hn["Principled BSDF"])
    _vol = _hn.new("ShaderNodeVolumePrincipled")
    _vol.inputs["Density"].default_value = 0.012
    _vol.inputs["Color"].default_value = (1.0, 0.92, 0.82, 1.0)
    haze_m.node_tree.links.new(_vol.outputs["Volume"], _hn["Material Output"].inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 0.0, 8.0))
    haze = bpy.context.object
    haze.name = "Haze"
    haze.scale = (46.0, 30.0, 16.0)
    haze.data.materials.append(haze_m)
# soft glow on the brightest spots (lamp, timer digits), like the reference
scene.use_nodes = True
_ct = scene.node_tree
for _n in list(_ct.nodes):
    _ct.nodes.remove(_n)
_rl = _ct.nodes.new("CompositorNodeRLayers")
_gl = _ct.nodes.new("CompositorNodeGlare")
_gl.glare_type = "FOG_GLOW"
_set(_gl, "threshold", 0.85)
_set(_gl, "size", 7)
_out = _ct.nodes.new("CompositorNodeComposite")
_ct.links.new(_rl.outputs["Image"], _gl.inputs["Image"])
_ct.links.new(_gl.outputs["Image"], _out.inputs["Image"])

# 4. motion blur for the fast moves (fling, spins, fast-forward)
scene.render.use_motion_blur = os.environ.get("FS_MB", "1") == "1"
_set(scene.render, "motion_blur_shutter", 0.5)

# ---------- camera: low and close like the reference, focused on the cat, background soft ----------
bpy.ops.object.camera_add(location=(-1.6, -17.0, 3.6))
cam = bpy.context.object
cam.data.lens = 40
look = Vector((-0.6, 0.0, 2.0)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = os.environ.get("FS_DOF", "1") == "1"
cam.data.dof.focus_distance = (CAT + Vector((0, 0, 1.2)) - cam.location).length
cam.data.dof.aperture_fstop = 0.3  # macro-strength blur: background lights become soft bokeh discs
scene.camera = cam

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
