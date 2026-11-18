# rubik-render-farm

Uji render film animasi 3D di GitHub Actions (runner gratis, tanpa GPU).

Filmnya: **Muse ireng** — maskot vinyl-toy hitam yang menepuk Rubik's cube sampai
selesai, lalu stikernya lepas dan menempel di punggungnya tanpa ia sadari.
Scene dibangun prosedural di Blender dari primitif (tanpa aset impor), animasi
digerakkan plan frame-by-frame (`pipeline/plan.json`).

## Kredit

Konsep dan pipeline film diadaptasi dari proyek **rubik-cat** karya
[@ahmadaryanto_](https://github.com/ahmadaryanto/rubik-cat)
(repo: https://github.com/ahmadaryanto/rubik-cat) — dipakai sebagai template
pribadi dengan kredit penulis. Maskot asli (kucing merah) diganti menjadi
Muse ireng (maskot hitam berkacamata, bertopi).

## Isi repo

- `pipeline/build_scene_fast.py` — membangun scene (meja, lampu, mug, buku,
  kubus Rubik, maskot) dari primitif Blender.
- `pipeline/animate_fast.py` — memainkan `plan.json`, keyframe tiap frame,
  lalu render dengan Eevee (setting B7: 960×540, 8 sample, raytracing OFF,
  DOF ON, motion blur ON).
- `pipeline/plan.json` — 1.500 frame plan animasi (GSAP).
- `.github/workflows/render-test.yml` — uji render 120 frame (4 job × 30 frame)
  di runner GitHub Actions.

## Cara jalanin uji

Tab **Actions** → workflow **render-test** → **Run workflow**.
Tiap job menginstal libEGL/Mesa (wajib — tanpa itu Blender Eevee headless
gagal total), mengunduh Blender 4.5.3 LTS, merender 30 frame, lalu mengunggah
frame sebagai artifact.

## Status uji

- 2026-11-19: uji pertama 120 frame (frame 1–120, film 16:9).
