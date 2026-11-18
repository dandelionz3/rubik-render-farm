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
- `pipeline/plan_intro.json` — 330 frame plan intro.
- `.github/workflows/render-test.yml` — uji render 120 frame (4 job × 30 frame)
  di runner GitHub Actions.
- `.github/workflows/render-full.yml` — full run 3.660 frame (20 job paralel);
  frame di-upload langsung ke Google Drive via rclone + service account
  (secret `GDRIVE_SA_JSON`, variable `GDRIVE_FOLDER_ID`). Tanpa keduanya,
  job gagal di langkah upload — lihat header workflow.

## Cara jalanin uji

Tab **Actions** → workflow **render-test** → **Run workflow**.
Tiap job menginstal libEGL/Mesa (wajib — tanpa itu Blender Eevee headless
gagal total), mengunduh Blender 4.5.3 LTS, merender 30 frame, lalu mengunggah
frame sebagai artifact.

## Status uji

- 2026-11-19: uji pertama 120 frame (frame 1–120, film 16:9) — SUKSES
  (run 44389889579, ~24,5 dtk/frame vs ~58 dtk/frame lokal, piksel-identik).

## Full run

Tab **Actions** → workflow **render-full** → **Run workflow**.
Syarat sebelum trigger: secret `GDRIVE_SA_JSON` (isi JSON service account
Google Cloud) dan variable `GDRIVE_FOLDER_ID` (ID folder Drive yang sudah
di-share ke email service account sebagai Editor). 20 job paralel, ~1,5 jam
wall-time, total ~2,2 GB frame langsung ke Drive (bukan artifact).
