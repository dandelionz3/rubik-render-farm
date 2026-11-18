# Plays the GSAP plan (plan.json, one row per frame) back in Blender and renders it.
# Builds the scene from build_scene.py, groups the cat and the cube layers into rigs, keys every frame,
# drives the timer digits from the plan, then renders frames with Eevee (GPU).
# Usage:
#   blender -b --factory-startup -P animate.py -- <out_dir> [--start 1] [--end 1500] [--res 1920 1080]
import bpy
import json
import os
import math
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))  # patched for repo: was hardcoded local path
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = args[0] if args else HERE + "/frames"
START = int(args[args.index("--start") + 1]) if "--start" in args else 1
END = int(args[args.index("--end") + 1]) if "--end" in args else 1500
PLAN = args[args.index("--plan") + 1] if "--plan" in args else HERE + "/plan.json"
TOFF = int(args[args.index("--toff") + 1]) if "--toff" in args else 0  # frame offset for the dust clock (the intro runs before frame 0)
LENSK = float(args[args.index("--lensk") + 1]) if "--lensk" in args else 1.0  # lens multiplier: the vertical (Reels) render uses a wider lens

# Build the scene without its still render (build_scene.py reads OUT and --res from sys.argv)
sys.argv = [sys.argv[0], "--", OUT_DIR + "/unused.png"] + (["--res"] + args[args.index("--res") + 1:args.index("--res") + 3] if "--res" in args else [])
src = open(HERE + "/build_scene_fast.py", encoding="utf-8").read().split("scene.render.filepath = OUT")[0]
exec(src)

plan = json.load(open(PLAN, encoding="utf-8"))
objs = bpy.data.objects
bpy.context.view_layer.update()


def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    if parent is not None:
        e.parent = parent
        e.location = Vector(loc) - parent.location
    bpy.context.view_layer.update()
    return e


def attach(obj, rig):
    m = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = m


# ---------- cat rig: body, head, two arms (the left arm carries the paddle) ----------
CAT_PARTS = [o for o in objs if o.name.split(".")[0] in {
    "LegL", "LegR", "ShoeL", "ShoeR", "SoleL", "SoleR", "Torso", "Kimono", "ShirtFront", "Bag",
    "Tail0", "Tail1", "Tail2"}]
HEAD_PARTS = [o for o in objs if o.name.split(".")[0] in {
    "Head", "EyeL", "EyeR", "Nose", "GlassesL", "GlassesR", "BrowL", "BrowR",
    "GlassesBridge", "Mouth", "CapDome", "CapBrim", "CapButton"}]
ARM_R = [o for o in objs if o.name.split(".")[0] in {"ArmR", "SleeveR", "PawR", "ClawR0", "ClawR1", "ClawR2"}]
ARM_L = [o for o in objs if o.name.split(".")[0] in {"ArmL", "SleeveL", "PawL", "ClawL0", "ClawL1", "ClawL2"}]

cat_rig = empty("CatRig", (CAT.x, CAT.y, 0.0))
head_rig = empty("HeadRig", (CAT.x, CAT.y, HEAD_PIVOT_Z), cat_rig)
arm_r_rig = empty("ArmRigR", (CAT.x + SHOULDER[0], CAT.y, SHOULDER[1]), cat_rig)
arm_l_rig = empty("ArmRigL", (CAT.x - SHOULDER[0], CAT.y, SHOULDER[1]), cat_rig)
for o in CAT_PARTS:
    attach(o, cat_rig)
for o in HEAD_PARTS:
    attach(o, head_rig)
for o in ARM_R:
    attach(o, arm_r_rig)
for o in ARM_L:
    attach(o, arm_l_rig)

# ---------- cube layers: bottom (z = -1) and top (z = +1) rotate about the cube's vertical axis ----------
layer_bottom = empty("LayerBottom", (0.0, 0.0, CUBE_C.z - CELL))
layer_top = empty("LayerTop", (0.0, 0.0, CUBE_C.z + CELL))
hole = None
for o in list(objs):
    base = o.name.split(".")[0]
    if not (base.startswith("Cubie") or base.startswith("Sticker")):
        continue
    z = o.matrix_world.translation.z
    if z < CUBE_C.z - CELL * 0.5:
        attach(o, layer_bottom)
    elif z > CUBE_C.z + CELL * 0.5:
        attach(o, layer_top)
    if base.startswith("Sticker") and (o.matrix_world.translation - Vector((1.5, -2.235, 0.75))).length < 0.06:
        hole = o
assert hole is not None, "hole sticker not found"

# the 3 orange stickers that the stomp (top layer +90) brings to the front top row, by front column:
# rest y = 1.5, 0, -1.5 lands at x = -1.5, 0, 1.5 (plan.mjs COLS)
orange_top = [None, None, None]
for o in objs:
    if not o.name.startswith("Stickerorange"):
        continue
    w = o.matrix_world.translation
    if abs(w.x + 2.235) < 0.06 and abs(w.z - (CUBE_C.z + CELL)) < 0.06:
        orange_top[{1.5: 0, 0.0: 1, -1.5: 2}[round(w.y, 1)]] = o
assert all(orange_top), "top-row orange stickers not found"

# the whole cube rocks on the desk (never twists): every cubie, sticker and both layer rigs hang off CubeRig
cube_rig = empty("CubeRig", (0.0, 0.0, 0.0))
for o in list(objs):
    base = o.name.split(".")[0]
    if o.parent is None and (base.startswith("Cubie") or base.startswith("Sticker") or o in (layer_bottom, layer_top)):
        attach(o, cube_rig)

# a card of spare stickers on the desk (3 greens), and the stickers the fast-forward moves around (world space)
SHEET_MAT = mat("SheetCard", (0.92, 0.9, 0.85), 0.5)
block("SpareSheet", (-1.0, -4.6, 0.02), (4.3, 1.55, 0.04), 0.015, SHEET_MAT)
fx_objs = {"peel": [], "neu": []}
for kind, colour in (("peel", "orange"), ("neu", "green")):
    for k in range(3):
        bpy.ops.mesh.primitive_plane_add(size=CELL * 0.78, location=(0, 0, -5))
        p = bpy.context.object
        p.name = f"Fx{kind}{k}"
        p.data.materials.append(STICKER[colour])
        fx_objs[kind].append(p)

# the loose sticker that flies to the cat's back and later clicks into the hole
bpy.ops.mesh.primitive_plane_add(size=CELL * 0.78, location=(0, 0, -5))
loose = bpy.context.object
loose.name = "LooseSticker"
loose.data.materials.append(STICKER["green"])

# binder clip rig
clip_rig = empty("ClipRig", (2.9, -3.9, 0.0))
for o in objs:
    if o.name.split(".")[0] in {"BinderClipBody", "BinderClipWing"}:
        attach(o, clip_rig)

# timer digits: the text object that reads 00.00
timer_txt = next(o for o in objs if o.type == "FONT" and o.data.body == "00.00")

# ---------- face rig: rest transforms of brows, eyes and mouth (in head space, after parenting) ----------
bpy.context.view_layer.update()
FACE_PARTS = {}
for nm in ("BrowL", "BrowR", "EyeL", "EyeR", "Mouth"):
    o = objs[nm]
    FACE_PARTS[nm] = (o, o.location.copy(), o.rotation_euler.copy(), o.scale.copy())

# ---------- key every frame ----------
for row in plan:
    fr = row["f"] + 1
    if fr < START or fr > END:
        continue
    c = row["cat"]
    cat_rig.location = (c["x"], c["y"], c["z"])
    cat_rig.rotation_euler = (math.radians(-c["lean"]), 0.0, math.radians(c["rot"]))
    cat_rig.scale = (1.0 / math.sqrt(c["squash"]), 1.0 / math.sqrt(c["squash"]), c["squash"])
    for prop in ("location", "rotation_euler", "scale"):
        cat_rig.keyframe_insert(prop, frame=fr)
    head_rig.rotation_euler = (math.radians(row["head"]["tilt"]), 0.0, math.radians(row["head"]["turn"]))
    head_rig.keyframe_insert("rotation_euler", frame=fr)
    arm_r_rig.rotation_euler = (math.radians(row["arm"]["r"]), 0.0, 0.0)
    arm_l_rig.rotation_euler = (math.radians(row["arm"]["l"]), 0.0, 0.0)
    arm_r_rig.keyframe_insert("rotation_euler", frame=fr)
    arm_l_rig.keyframe_insert("rotation_euler", frame=fr)
    layer_bottom.rotation_euler = (0.0, 0.0, math.radians(row["cube"]["bottom"]))
    layer_top.rotation_euler = (0.0, 0.0, math.radians(row["cube"]["top"]))
    layer_bottom.keyframe_insert("rotation_euler", frame=fr)
    layer_top.keyframe_insert("rotation_euler", frame=fr)
    cube_rig.location = (row["cube"]["x"], 0.0, 0.0)
    cube_rig.rotation_euler = (0.0, 0.0, math.radians(row["cube"]["rz"]))
    cube_rig.keyframe_insert("location", frame=fr)
    cube_rig.keyframe_insert("rotation_euler", frame=fr)
    # fast-forward swaps: peeled oranges, carried greens, and the real oranges hidden once peeled
    for kind in ("peel", "neu"):
        for p, st in zip(fx_objs[kind], row["fx"][kind]):
            p.hide_render = st is None
            p.keyframe_insert("hide_render", frame=fr)
            if st is not None:
                p.location = (st["x"], st["y"], st["z"])
                p.rotation_euler = (math.radians(st["rx"]), 0.0, math.radians(st["rz"]))
                p.keyframe_insert("location", frame=fr)
                p.keyframe_insert("rotation_euler", frame=fr)
    for o, hid in zip(orange_top, row["fx"]["hideOrange"]):
        o.hide_render = hid
        o.keyframe_insert("hide_render", frame=fr)
    k = row["clip"]
    clip_rig.location = (k["x"], k["y"], k["z"])
    clip_rig.rotation_euler = (0.0, math.radians(k["rot"]), 0.0)
    clip_rig.keyframe_insert("location", frame=fr)
    clip_rig.keyframe_insert("rotation_euler", frame=fr)
    lo = row["loose"]
    loose.hide_render = lo is None
    if lo is not None:
        loose.location = (lo["x"], lo["y"], lo["z"])
        loose.rotation_euler = (math.radians(lo["rx"]), 0.0, math.radians(lo["rz"]))
        loose.keyframe_insert("location", frame=fr)
        loose.keyframe_insert("rotation_euler", frame=fr)
    loose.keyframe_insert("hide_render", frame=fr)
    hole.hide_render = not row["holeVisible"]
    hole.keyframe_insert("hide_render", frame=fr)
    # face: brows tilt and lift, eyes squint/widen/blink, mouth stretches (emotion per beat)
    fa = row["face"]
    for nm, sx in (("BrowL", -1), ("BrowR", 1)):
        o, loc0, rot0, _ = FACE_PARTS[nm]
        o.location = loc0 + Vector((0.0, 0.0, fa["browUp"]))
        o.rotation_euler = (rot0.x, rot0.y + math.radians(fa["browAng"]) * (-sx), rot0.z)
        o.keyframe_insert("location", frame=fr)
        o.keyframe_insert("rotation_euler", frame=fr)
    for nm in ("EyeL", "EyeR"):
        o, _, _, sc0 = FACE_PARTS[nm]
        o.scale = (sc0.x, sc0.y, sc0.z * fa["eye"])
        o.keyframe_insert("scale", frame=fr)
    o, _, _, sc0 = FACE_PARTS["Mouth"]
    o.scale = (sc0.x * fa["mouthW"], sc0.y, sc0.z * fa["mouthH"])
    o.keyframe_insert("scale", frame=fr)
    # camera from the plan: shot position, aim at the smoothed target, focus on the cat, lens per shot
    cm = row["cam"]
    cam.location = (cm["x"], cm["y"], cm["z"])
    cam.rotation_euler = (Vector((cm["tx"], cm["ty"], cm["tz"])) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = cm["focus"]
    cam.data.lens = cm["lens"] * LENSK
    cam.keyframe_insert("location", frame=fr)
    cam.keyframe_insert("rotation_euler", frame=fr)
    cam.data.keyframe_insert("dof.focus_distance", frame=fr)
    cam.data.keyframe_insert("lens", frame=fr)

# baked per frame: no easing between keys
for ob in bpy.data.objects:
    ad = ob.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


DUST = [(objs[name], Vector(base)) for name, base in DUST_BASE]


def on_frame(scn, *_):
    """Per frame: timer digits from the plan, and a slow drift for the dust in the lamp beam (deterministic)."""
    i = max(0, min(len(plan) - 1, scn.frame_current - 1))
    timer_txt.data.body = plan[i]["timer"]
    t = (scn.frame_current + TOFF) / 60.0
    for n, (d, base) in enumerate(DUST):
        d.location = base + Vector((
            0.35 * math.sin(0.31 * t + n * 1.3),
            0.25 * math.cos(0.23 * t + n * 2.1),
            0.45 * math.sin(0.17 * t + n * 0.7) + 0.05 * t,
        ))


bpy.app.handlers.frame_change_pre.append(on_frame)

scene.frame_start = START
scene.frame_end = END
scene.render.fps = 60
scene.render.fps_base = 1.0
scene.render.filepath = OUT_DIR + "/f_"
scene.render.image_settings.file_format = "PNG"
print("RENDER", START, END, "->", OUT_DIR)
bpy.ops.render.render(animation=True)
print("DONE_ANIM")
