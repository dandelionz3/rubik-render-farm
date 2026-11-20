# animate_gta6.py — mainkan plan.json GTA 6 Blender 3D di Blender, render Eevee/Cycles.
# Pola: animate_zombie.py. Bangun scene dari build_scene_gta6.py (exec s.d.
# scene.render.filepath = OUT), kelompokkan bagian karakter ke rig empty, keyframe
# tiap frame dari plan.json (interpolasi LINEAR), lalu render per rentang frame.
# Usage:
#   blender -b --factory-startup -P animate_gta6.py -- <out_dir> --start N --end N \
#       --plan plan.json --res 540 960 --lensk 0.62 [--engine eevee|cycles]
#   9:16: --res 540 960 --lensk 0.62 ; 16:9: --res 960 540 --lensk 1.00
#   Frame Blender = f + 1 (plan f 0-based). --start/--end = nomor frame Blender.
#   Cycles: device GPU, samples 32, denoising OPENIMAGEDENOISE, CUDA only.
import bpy
import json
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = args[0] if args else HERE + "/frames"
START = int(args[args.index("--start") + 1]) if "--start" in args else 1
END = int(args[args.index("--end") + 1]) if "--end" in args else 1296
PLAN = args[args.index("--plan") + 1] if "--plan" in args else HERE + "/plan.json"
LENSK = float(args[args.index("--lensk") + 1]) if "--lensk" in args else 0.62
ENGINE = args[args.index("--engine") + 1] if "--engine" in args else "eevee"
assert ENGINE in ("eevee", "cycles"), f"--engine harus eevee|cycles, dapat {ENGINE!r}"

# Build the scene without its still render (build_scene_gta6.py reads OUT and --res from sys.argv)
sys.argv = [sys.argv[0], "--", OUT_DIR + "/unused.png"] + (
    ["--res"] + args[args.index("--res") + 1:args.index("--res") + 3] if "--res" in args else [])
src = open(os.path.join(HERE, "build_scene_gta6.py"), encoding="utf-8").read().split(
    "scene.render.filepath = OUT")[0]
exec(src)

# ---------- engine switch (scene harus engine-agnostic) ----------
if ENGINE == "cycles":
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    _cprefs = bpy.context.preferences.addons["cycles"].preferences
    _cprefs.compute_device_type = "CUDA"
    _cprefs.get_devices()
    for _d in _cprefs.devices:
        _d.use = (_d.type == "CUDA")
    print("CYCLES DEVICES:", [(d.name, d.type, d.use) for d in _cprefs.devices], flush=True)
    print("CYCLES SETTINGS: device=%s samples=%s denoiser=%s" % (
        scene.cycles.device, scene.cycles.samples, scene.cycles.denoiser), flush=True)
else:
    print("EEVEE SETTINGS: samples=%s raytracing=%s vol_tile=%s" % (
        scene.eevee.taa_render_samples,
        getattr(scene.eevee, "use_raytracing", None),
        getattr(scene.eevee, "volumetric_tile_size", None)), flush=True)

plan = [json.loads(line) for line in open(PLAN, encoding="utf-8") if line.strip()]
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


# ---------- rig per karakter: RootRig + HeadRig + ArmRigL/R + LegRigL/R ----------
RIGS = {}
for prefix, info in CHARS.items():
    base = info["base"]
    root = empty(f"{prefix}_RootRig", (base.x, base.y, base.z))
    head_rig = empty(f"{prefix}_HeadRig", (base.x, base.y, base.z + info["head_pivot_z"]), root)
    arm_r = empty(f"{prefix}_ArmRigR", (base.x + info["sho_x"], base.y, base.z + info["sho_z"]), root)
    arm_l = empty(f"{prefix}_ArmRigL", (base.x - info["sho_x"], base.y, base.z + info["sho_z"]), root)
    leg_r = empty(f"{prefix}_LegRigR", (base.x + 0.14 * info["scale"], base.y, base.z + info["hip_z"]), root)
    leg_l = empty(f"{prefix}_LegRigL", (base.x - 0.14 * info["scale"], base.y, base.z + info["hip_z"]), root)
    for o in info["body"]:
        attach(o, root)
    for o in info["head"]:
        attach(o, head_rig)
    for o in info["armR"]:
        attach(o, arm_r)
    for o in info["armL"]:
        attach(o, arm_l)
    for o in info["legR"]:
        attach(o, leg_r)
    for o in info["legL"]:
        attach(o, leg_l)
    for o in info["bag_objs"]:
        attach(o, root)
    RIGS[prefix] = {"root": root, "head": head_rig, "armR": arm_r, "armL": arm_l,
                    "legR": leg_r, "legL": leg_l, "info": info,
                    "parts": (info["body"] + info["head"] + info["armR"] + info["armL"]
                              + info["legR"] + info["legL"])}

# ---------- rig mobil + helikopter + gerbang ----------
car_rig = empty("CarRig", (0, 0, 0))
for o in CAR_PARTS:
    attach(o, car_rig)
heli_rig = empty("HeliRig", (0, 0, 0))
for o in HELI_PARTS:
    attach(o, heli_rig)
heli_rotor = empty("HeliRotor", (0, 0, 0.75), heli_rig)
for o in HELI_ROTOR_PARTS:
    attach(o, heli_rotor)
gate_rig = empty("GateRig", GATE_HINGE)
for o in GATE_PARTS:
    attach(o, gate_rig)

LIGHT_OBJS = {nm: LIGHTS[nm] for nm in LIGHTS}
LIGHT_KEYS = {"neon": ("neon_pink", "neon_cyan"), "sun": ("sun",), "moon": ("moon",),
              "street": ("street",), "heli": ("heli",), "strobe_r": ("strobe_r",),
              "strobe_b": ("strobe_b",), "head": ("head",), "bank": ("bank",),
              "dusk": ("dusk",), "fill": ("fill",)}
WORLD_BG_NODE = WORLD_BG

# ---------- key every frame in range ----------
_last_vis = {}   # prefix -> bool, key hide_render hanya saat berubah
_last_eye = {}   # prefix -> eye_red bool
_last_bag = {}   # prefix -> bag bool
_last_rain = None
for row in plan:
    fr = row["f"] + 1
    if fr < START or fr > END:
        continue
    for prefix, rig in RIGS.items():
        c = row["chars"][prefix]
        root = rig["root"]
        if _last_vis.get(prefix) != c["vis"]:
            for o in rig["parts"]:
                o.hide_render = not c["vis"]
                o.keyframe_insert("hide_render", frame=fr)
            _last_vis[prefix] = c["vis"]
        # tas duffel: key hanya saat berubah (bag terikat RootRig, bukan di rig["parts"])
        if _last_bag.get(prefix) != c["bag"]:
            for o in rig["info"]["bag_objs"]:
                o.hide_render = not c["bag"]
                o.keyframe_insert("hide_render", frame=fr)
            _last_bag[prefix] = c["bag"]
        if not c["vis"]:
            continue
        info = rig["info"]
        root.location = (c["x"], c["y"], c["z"] - 0.30 * c["crouch"] * info["scale"])
        root.rotation_euler = (math.radians(c["lean"] + c["pitch"]), 0.0, math.radians(c["rot"]))
        root.scale = (1.0 / math.sqrt(c["squash"]), 1.0 / math.sqrt(c["squash"]), c["squash"])
        for prop in ("location", "rotation_euler", "scale"):
            root.keyframe_insert(prop, frame=fr)
        rig["head"].rotation_euler = (math.radians(c["head_tilt"]), 0.0, math.radians(c["head_turn"]))
        rig["head"].keyframe_insert("rotation_euler", frame=fr)
        # lengan/kaki: sudut plan positif = ayun ke depan (-Y); rotasi X negatif
        rig["armR"].rotation_euler = (math.radians(-c["armR"]), 0.0, 0.0)
        rig["armL"].rotation_euler = (math.radians(-c["armL"]), 0.0, 0.0)
        rig["legR"].rotation_euler = (math.radians(-c["legR"]), 0.0, 0.0)
        rig["legL"].rotation_euler = (math.radians(-c["legL"]), 0.0, 0.0)
        for r in (rig["armR"], rig["armL"], rig["legR"], rig["legL"]):
            r.keyframe_insert("rotation_euler", frame=fr)
        # mata: hitam <-> merah (key hanya saat berubah; GTA 6 selalu hitam)
        if _last_eye.get(prefix) != c["eye_red"]:
            for o in info["eyes_black"]:
                o.hide_render = c["eye_red"]
                o.keyframe_insert("hide_render", frame=fr)
            for o in info["eyes_red"]:
                o.hide_render = not c["eye_red"]
                o.keyframe_insert("hide_render", frame=fr)
            _last_eye[prefix] = c["eye_red"]
        # mulut: skala dari plan
        m = info["mouth"]
        m.scale = (c["mouthW"], 1.0, c["mouthH"])
        m.keyframe_insert("scale", frame=fr)
    # lampu: energi per frame (satu key plan bisa menggerakkan 2 lampu, mis. neon)
    for key, names in LIGHT_KEYS.items():
        for objname in names:
            o = LIGHT_OBJS[objname]
            o.data.energy = row["lights"][key]
            o.data.keyframe_insert("energy", frame=fr)
    # world: warna + strength langit per frame
    WORLD_BG_NODE.inputs["Color"].default_value = (*row["world"]["bg"], 1.0)
    WORLD_BG_NODE.inputs["Color"].keyframe_insert("default_value", frame=fr)
    WORLD_BG_NODE.inputs["Strength"].default_value = row["world"]["strength"]
    WORLD_BG_NODE.inputs["Strength"].keyframe_insert("default_value", frame=fr)
    # props: mobil, helikopter, gerbang, hujan
    p = row["props"]
    car = p["car"]
    car_rig.location = (car["x"], car["y"], car["z"])
    car_rig.rotation_euler = (0.0, 0.0, math.radians(car["rot"]))
    car_rig.keyframe_insert("location", frame=fr)
    car_rig.keyframe_insert("rotation_euler", frame=fr)
    for o in CAR_PARTS:
        o.hide_render = car["hide"]
        o.keyframe_insert("hide_render", frame=fr)
    heli = p["heli"]
    heli_rig.location = (heli["x"], heli["y"], heli["z"])
    heli_rig.rotation_euler = (0.0, 0.0, math.radians(heli["rot"]))
    heli_rig.keyframe_insert("location", frame=fr)
    heli_rig.keyframe_insert("rotation_euler", frame=fr)
    heli_rotor.rotation_euler = (0.0, 0.0, math.radians(heli["rotor"]))
    heli_rotor.keyframe_insert("rotation_euler", frame=fr)
    for o in HELI_PARTS + HELI_ROTOR_PARTS:
        o.hide_render = heli["hide"]
        o.keyframe_insert("hide_render", frame=fr)
    gate_rig.rotation_euler = (0.0, 0.0, math.radians(p["gate_rot"]))
    gate_rig.keyframe_insert("rotation_euler", frame=fr)
    if _last_rain != p["rain"]:
        for o in RAIN_OBJS:
            o.hide_render = not p["rain"]
            o.keyframe_insert("hide_render", frame=fr)
        _last_rain = p["rain"]
    # kamera dari plan: posisi, bidik target, fokus, lens
    cm = row["cam"]
    cam.location = (cm["x"], cm["y"], cm["z"])
    cam.rotation_euler = (Vector((cm["tx"], cm["ty"], cm["tz"])) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = cm["focus"]
    cam.data.lens = cm["lens"] * LENSK
    cam.keyframe_insert("location", frame=fr)
    cam.keyframe_insert("rotation_euler", frame=fr)
    cam.data.keyframe_insert("dof.focus_distance", frame=fr)
    cam.data.keyframe_insert("lens", frame=fr)

# baked per frame: tanpa easing antar key
for ob in bpy.data.objects:
    ad = ob.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
# data lampu (energy) + world juga LINEAR
for ob in list(objs) + [o.data for o in LIGHT_OBJS.values()]:
    ad = getattr(ob, "animation_data", None)
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
for _inp in (WORLD_BG_NODE.inputs["Color"], WORLD_BG_NODE.inputs["Strength"]):
    _ad = getattr(_inp, "animation_data", None)
    if _ad and _ad.action:
        for _fc in getattr(_ad.action, "fcurves", []):
            for _kp in _fc.keyframe_points:
                _kp.interpolation = "LINEAR"

scene.frame_start = START
scene.frame_end = END
scene.render.fps = 24
scene.render.fps_base = 1.0
scene.render.filepath = OUT_DIR + "/f_"
scene.render.image_settings.file_format = "PNG"
print("RENDER", ENGINE, START, END, "->", OUT_DIR)
bpy.ops.render.render(animation=True)
print("DONE_ANIM")
