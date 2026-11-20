#!/usr/bin/env python3
# plan_gta6.py — generator plan.json film GTA 6 Blender 3D (1296 frame, 24 fps).
# Satu baris per frame (f 0..1295). Per frame: rig Lucia/Jason, posisi mobil +
# helikopter, intensitas lampu, warna world, kamera, flag (hide/show, tas, hujan, gerbang).
# Murni Python (tanpa bpy) — jalan di VM maupun di kernel Kaggle.
#   python3 plan_gta6.py [plan.json]
import json
import math
import os
import sys

N = 1296
OX = 60.0    # gerbang penjara (sama dengan build_scene_gta6.py)
OX2 = 120.0  # pantai (sama dengan build_scene_gta6.py)

# segmen (DESIGN.md): S1 0-143, S2 144-287, S3 288-431, S4 432-599,
# S5 600-767, S6 768-935, S7 936-1127, S8 1128-1295


def clamp(x, a, b):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def seg_t(f, a, b):
    """Progress 0..1 di dalam [a,b]."""
    return clamp((f - a) / max(1, b - a), 0.0, 1.0)


def shake(f, amp, freq=1.7):
    """Goyang deterministik (handheld) — tanpa random."""
    return amp * (math.sin(f * 0.9 * freq) * 0.6 + math.sin(f * 2.3 * freq + 1.3) * 0.4)


def walk_cycle(phase, amp, arm_amp=None):
    """Ayun kaki/lengan berlawanan + bob. phase dalam radian."""
    if arm_amp is None:
        arm_amp = amp * 0.8
    return {
        "legL": amp * math.sin(phase),
        "legR": -amp * math.sin(phase),
        "armL": -arm_amp * math.sin(phase),
        "armR": arm_amp * math.sin(phase),
        "bob": 0.045 * abs(math.cos(phase)),
    }


def char(x=0, y=0, z=0, rot=0, lean=0, squash=1.0, crouch=0.0, pitch=0.0,
         head_tilt=0, head_turn=0, armL=0, armR=0, legL=0, legR=0,
         eye_red=False, vis=True, mouthW=1.0, mouthH=1.0, bag=False):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "rot": round(rot, 2),
            "lean": round(lean, 2), "squash": round(squash, 3), "crouch": round(crouch, 3),
            "pitch": round(pitch, 2), "head_tilt": round(head_tilt, 2),
            "head_turn": round(head_turn, 2), "armL": round(armL, 2), "armR": round(armR, 2),
            "legL": round(legL, 2), "legR": round(legR, 2),
            "eye_red": bool(eye_red), "vis": bool(vis),
            "mouthW": round(mouthW, 2), "mouthH": round(mouthH, 2),
            "bag": bool(bag)}


def hidden():
    return char(vis=False)


def cam(x, y, z, tx, ty, tz, focus, lens):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
            "tx": round(tx, 3), "ty": round(ty, 3), "tz": round(tz, 3),
            "focus": round(focus, 2), "lens": round(lens, 1)}


def lights(neon=800, sun=0, moon=300, street=300, heli=0, strobe_r=0, strobe_b=0,
           head=0, bank=0, dusk=0, fill=250):
    return {"neon": round(neon, 1), "sun": round(sun, 1), "moon": round(moon, 1),
            "street": round(street, 1), "heli": round(heli, 1),
            "strobe_r": round(strobe_r, 1), "strobe_b": round(strobe_b, 1),
            "head": round(head, 1), "bank": round(bank, 1),
            "dusk": round(dusk, 1), "fill": round(fill, 1)}


def world(rgb, strength):
    return {"bg": [round(c, 3) for c in rgb], "strength": round(strength, 2)}


# warna world per segmen (palet DESIGN.md)
W_NIGHT = world((0.043, 0.055, 0.102), 0.9)      # langit malam #0B0E1A
W_GOLD = world((0.28, 0.15, 0.08), 1.0)          # golden hour penjara
W_DUSK = world((0.16, 0.10, 0.14), 0.9)          # senja gas station
W_DARK = world((0.02, 0.03, 0.07), 0.8)          # jalan gelap S6
W_SUNRISE = world((0.45, 0.22, 0.10), 1.1)       # matahari terbit pantai
W_SUNSET = world((0.35, 0.14, 0.08), 1.0)        # matahari terbenam pesisir


def car_prop(hide=True, x=0, y=0, z=0, rot=0):
    return {"hide": bool(hide), "x": round(x, 3), "y": round(y, 3),
            "z": round(z, 3), "rot": round(rot, 2)}


def heli_prop(hide=True, x=0, y=0, z=0, rot=0, rotor=0):
    return {"hide": bool(hide), "x": round(x, 3), "y": round(y, 3),
            "z": round(z, 3), "rot": round(rot, 2), "rotor": round(rotor, 1)}


rows = []
for f in range(N):
    chars = {}
    props = {"car": car_prop(), "heli": heli_prop(), "gate_rot": 0.0, "rain": False}

    # ================= S1 SKYLINE (0-143): rooftop, slow push-in =================
    if f < 144:
        t = seg_t(f, 0, 143)
        # Lucia+Jason kecil di tepi rooftop (z=6.0, di atas gedung ST_RoofBldg)
        sway = 2 * math.sin(f * 0.05)
        chars["LUCIA"] = char(-0.7, 7.5, 6.0, rot=0, lean=2, head_tilt=-3,
                              head_turn=sway, armL=5, armR=5)
        chars["JASON"] = char(0.7, 7.5, 6.0, rot=0, lean=2, head_tilt=-3,
                              head_turn=-sway, armL=5, armR=5)
        chars_cam = cam(0, lerp(-7.0, -5.0, smooth(t)), lerp(6.9, 6.4, smooth(t)),
                        0, 7.5, 6.5, 14.0, lerp(62, 55, smooth(t)))
        li = lights(neon=800, moon=300, street=200, fill=250)
        w = W_NIGHT
    # ================= S2 PRISON (144-287): Lucia keluar gerbang, golden hour =================
    elif f < 288:
        t = seg_t(f, 144, 287)
        lu_y = lerp(3.0, -3.0, t)
        ph = f * 0.16
        c = walk_cycle(ph, 25)
        chars["LUCIA"] = char(OX, lu_y, c["bob"], rot=0, lean=5,
                              armL=c["armL"], armR=c["armR"],
                              legL=c["legL"], legR=c["legR"], bag=True)
        chars["JASON"] = hidden()
        # gerbang terbuka 70 derajat, menutup f 200-260
        props["gate_rot"] = lerp(70, 0, smooth(seg_t(f, 200, 260)))
        chars_cam = cam(OX, lerp(-7.0, -5.5, smooth(t)), lerp(2.2, 1.9, smooth(t)),
                        OX, lu_y, 1.2, 6.5, lerp(45, 58, smooth(t)))
        li = lights(neon=0, moon=60, street=100, dusk=900, sun=500, fill=200)
        w = W_GOLD
    # ================= S3 JASON (288-431): bersandar di mobil, slow pan kanan =================
    elif f < 432:
        t = seg_t(f, 288, 431)
        # mobil parkir di pom bensin
        props["car"] = car_prop(hide=False, x=10.0, y=2.0, z=0, rot=0)
        # Jason bersandar di sisi mobil (x=8.4), lengan menyilang
        head_turn = 0
        if f >= 400:
            head_turn = -35 * smooth(seg_t(f, 400, 431))  # menoleh saat Lucia datang
        chars["JASON"] = char(8.4, 2.0, 0, rot=0, lean=-8, head_turn=head_turn,
                              armL=55, armR=55, legL=8, legR=-8)
        if f >= 400:
            # Lucia berjalan masuk dari kiri
            lu_t = seg_t(f, 400, 431)
            lu_x = lerp(4.0, 7.0, lu_t)
            c = walk_cycle(f * 0.16, 22)
            chars["LUCIA"] = char(lu_x, 2.0, c["bob"], rot=90, lean=5,
                                  armL=c["armL"], armR=c["armR"],
                                  legL=c["legL"], legR=c["legR"], bag=True)
        else:
            chars["LUCIA"] = hidden()
        chars_cam = cam(lerp(4.0, 12.0, t), -6.0, 1.8, 9.0, 2.0, 1.2, 7.5, 48)
        li = lights(neon=400, moon=100, street=300, dusk=500, sun=150, fill=200)
        w = W_DUSK
    # ================= S4 HEIST (432-599): ke pintu bank, hujan tipis =================
    elif f < 600:
        t = seg_t(f, 432, 599)
        props["rain"] = True
        # Lucia+Jason jalan beriringan ke pintu bank (-11, 5.8)
        wx = lerp(-14.0, -11.0, t)
        wy = lerp(1.0, 5.8, t)
        ph = f * 0.16
        c1 = walk_cycle(ph, 25)
        c2 = walk_cycle(ph + 1.2, 25)
        chars["LUCIA"] = char(wx - 0.7, wy, c1["bob"], rot=148, lean=6,
                              armL=c1["armL"], armR=c1["armR"],
                              legL=c1["legL"], legR=c1["legR"], bag=True)
        chars["JASON"] = char(wx + 0.7, wy, c2["bob"], rot=148, lean=6,
                              armL=c2["armL"], armR=c2["armR"],
                              legL=c2["legL"], legR=c2["legR"], bag=True)
        chars_cam = cam(lerp(-12.5, -11.0, smooth(t)), lerp(-5.0, -3.5, smooth(t)),
                        lerp(2.0, 1.7, smooth(t)), wx, wy, 1.2, 6.0,
                        lerp(50, 55, smooth(t)))
        li = lights(neon=900, moon=250, street=350, bank=1200, fill=250)
        w = W_NIGHT
    # ================= S5 CHASE (600-767): mobil melaju, fast zoom-out + shake =================
    elif f < 768:
        t = seg_t(f, 600, 767)
        car_x = lerp(-14.0, 14.0, t)
        car_y = 0.4 * math.sin(f * 0.15)
        props["car"] = car_prop(hide=False, x=car_x, y=car_y, z=0, rot=0)
        chars["LUCIA"] = hidden()
        chars["JASON"] = hidden()
        chars_cam = cam(car_x * 0.3 + shake(f, 0.08), lerp(-7.0, -11.0, smooth(t)),
                        lerp(2.2, 3.0, smooth(t)) + shake(f + 9, 0.05),
                        car_x, 0, 1.0, 9.0, lerp(40, 55, smooth(t)))
        li = lights(neon=1000, moon=250, street=300, head=800, fill=200)
        w = W_NIGHT
    # ================= S6 HELICOPTER (768-935): sorot menyapu, kilat merah/biru =================
    elif f < 936:
        t = seg_t(f, 768, 935)
        heli_x = lerp(-8.0, 8.0, math.sin(t * math.pi * 0.5))  # menyapu kiri-kanan
        props["heli"] = heli_prop(hide=False, x=heli_x, y=2.0, z=7.0, rot=0,
                                  rotor=(f * 45) % 360)
        # mobil melintas cepat di bawah (f 800-860)
        if 800 <= f <= 860:
            props["car"] = car_prop(hide=False, x=lerp(-14.0, 14.0, seg_t(f, 800, 860)),
                                    y=0, z=0, rot=0)
        chars["LUCIA"] = hidden()
        chars["JASON"] = hidden()
        # strobe merah/biru bergantian tiap 6 frame
        strobe_r = 1500 if (f // 6) % 2 == 0 else 0
        strobe_b = 0 if (f // 6) % 2 == 0 else 1500
        chars_cam = cam(0, lerp(-8.0, -6.0, smooth(t)), lerp(2.5, 2.0, smooth(t)),
                        heli_x, 2.0, 4.0, 9.0, lerp(50, 58, smooth(t)))
        li = lights(neon=500, moon=150, street=200, heli=2500,
                    strobe_r=strobe_r, strobe_b=strobe_b, head=600, fill=150)
        w = W_DARK
    # ================= S7 SUNRISE (936-1127): duduk di kap mobil, slow zoom-out =================
    elif f < 1128:
        t = seg_t(f, 936, 1127)
        props["car"] = car_prop(hide=False, x=OX2, y=-4.0, z=0, rot=0)
        # duduk di kap mobil (ujung depan +X, permukaan kap z=0.74). CATATAN: char z
        # adalah ROOT (setara telapak saat berdiri), BUKAN tinggi kaki saat duduk:
        # kaki tekuk 70-75 derajat -> telapak berada ~0,35 di ATAS root (hip_z 0,48,
        # geometri rig terverifikasi dari render fix v1: gap kaki-kap ~0,35 m).
        # z=0,33 -> telapak ~0,68 (nyaris menapak kap 0,74, clip 0,06 tak terlihat),
        # pantat (torso bawah = root+0,48) ~0,81 (0,07 di atas kap, tak terlihat).
        # z=0,74 (v1) SALAH: telapak di 1,09, melayang 0,35 di atas kap.
        chars["LUCIA"] = char(OX2 + 1.1, -4.0, 0.33, rot=180, lean=-6, head_tilt=-8,
                              head_turn=10, armL=20, armR=15, legL=75, legR=70)
        chars["JASON"] = char(OX2 + 1.1, -4.0, 0.33, rot=180, lean=-6, head_tilt=-8,
                              head_turn=-10, armL=15, armR=20, legL=70, legR=75)
        # catatan: keduanya di titik kap yang sama (berdampingan) — offset x kecil
        chars["LUCIA"]["x"] = round(OX2 + 1.1, 3)
        chars["LUCIA"]["y"] = round(-4.45, 3)
        chars["JASON"]["x"] = round(OX2 + 1.1, 3)
        chars["JASON"]["y"] = round(-3.55, 3)
        chars_cam = cam(OX2, lerp(-9.0, -12.0, smooth(t)), lerp(2.2, 3.0, smooth(t)),
                        OX2 + 0.5, -4.0, 1.5, 9.5, lerp(45, 40, smooth(t)))
        li = lights(neon=0, moon=0, street=0, sun=1200, dusk=300, fill=150)
        w = W_SUNRISE
    # ================= S8 ROAD (1128-1295): mobil di jalan pesisir, aerial push-in =================
    else:
        t = seg_t(f, 1128, 1295)
        car_x = lerp(108.0, 132.0, t)
        props["car"] = car_prop(hide=False, x=car_x, y=-4.0, z=0, rot=0)
        chars["LUCIA"] = hidden()
        chars["JASON"] = hidden()
        chars_cam = cam(lerp(car_x - 4.0, car_x + 0.0, smooth(t)),
                        lerp(-9.5, -7.0, smooth(t)), lerp(5.5, 4.2, smooth(t)),
                        car_x, -4.0, 1.0, 11.0, lerp(55, 60, smooth(t)))
        li = lights(neon=0, moon=0, street=0, sun=800, dusk=400, head=400, fill=150)
        w = W_SUNSET

    rows.append({"f": f, "t": round(f / 24.0, 4), "chars": chars, "lights": li,
                 "cam": chars_cam, "props": props, "world": w})


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plan.json")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":"), allow_nan=False) + "\n")
    print(f"WROTE {out}: {len(rows)} rows")
    # self-checks
    assert len(rows) == N, f"rows={len(rows)} != {N}"
    assert rows[0]["f"] == 0 and rows[-1]["f"] == N - 1
    for r in rows:
        assert set(r["chars"]) == {"LUCIA", "JASON"}, f"f{r['f']}: chars={r['chars'].keys()}"
        assert set(r["lights"]) == {"neon", "sun", "moon", "street", "heli", "strobe_r",
                                    "strobe_b", "head", "bank", "dusk", "fill"}, f"f{r['f']}"
        assert set(r["props"]) == {"car", "heli", "gate_rot", "rain"}, f"f{r['f']}"
        assert len(r["world"]["bg"]) == 3
        for v in (r["cam"]["x"], r["cam"]["y"], r["cam"]["z"], r["cam"]["tx"],
                  r["cam"]["ty"], r["cam"]["tz"], r["cam"]["focus"], r["cam"]["lens"]):
            assert math.isfinite(v), f"f{r['f']}: cam NaN/inf {v}"
        for c in r["chars"].values():
            for k in ("x", "y", "z", "rot", "lean", "legL", "legR", "armL", "armR"):
                assert math.isfinite(c[k]), f"f{r['f']}: char {k} NaN/inf"
    # ringkasan per segmen (visibilitas + mobil/helikopter)
    bounds = [(0, 143, "S1"), (144, 287, "S2"), (288, 431, "S3"), (432, 599, "S4"),
              (600, 767, "S5"), (768, 935, "S6"), (936, 1127, "S7"), (1128, 1295, "S8")]
    for a, b, name in bounds:
        seg = rows[a:b + 1]
        lu = sum(1 for r in seg if r["chars"]["LUCIA"]["vis"])
        ja = sum(1 for r in seg if r["chars"]["JASON"]["vis"])
        car = sum(1 for r in seg if not r["props"]["car"]["hide"])
        heli = sum(1 for r in seg if not r["props"]["heli"]["hide"])
        rain = sum(1 for r in seg if r["props"]["rain"])
        print(f"CHECK {name} f{a}-{b}: LUCIA vis {lu}/{len(seg)}, JASON vis {ja}/{len(seg)}, "
              f"car {car}, heli {heli}, rain {rain}")
    print("CHECK OK: 1296 rows, no NaN, all frames have LUCIA+JASON+lights+props+world")


if __name__ == "__main__":
    main()
