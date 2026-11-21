---
name: firerpa-eval
description: Evaluasi & training FIRERPA/lamda — pemetaan kapabilitas dari dokumentasi publik, hasil pilot terbatas di lab, batas otorisasi MITM/Frida/root, dan kriteria adopsi untuk qa-team. Status DIPELAJARI · TERINSTALL DI LAB (v10.12) · PILOT TERBATAS PASS. Tidak mengklaim benchmark. Trigger: evaluasi lamda, training firerpa, bandingkan qa-team dengan firerpa, hasil pilot lamda.
---

# Evaluasi referensi FIRERPA / lamda (`firerpa-eval`)

Skill ini untuk **belajar, menilai, dan merangkum pilot terbatas** FIRERPA/lamda — bukan untuk menggantikan alur QA reguler. Dia menjawab: "apa yang ditawarkan repo itu, apa relevannya untuk PT Wisesa, apa yang sudah dibuktikan di lab, dan apa yang harus dibuktikan sebelum dipakai?"

## Ringkasan 1 menit

| | |
|---|---|
| **Status** | `DIPELAJARI · TERINSTALL DI LAB (v10.12) · PILOT TERBATAS PASS` |
| **Yang sudah dibuktikan** | Koneksi, info device, 85 package, screenshot, buka app, hierarchy 31 node, WebUI 200 |
| **Yang belum** | MITM/Frida/root/device farm, AVD re-pilot, perbandingan Appium, pemakaian produksi → `BLOCKED` |
| **Batasan** | Sumber kapabilitas = dokumentasi publik; tidak ada klaim benchmark/efisiensi; guardrail CORE tetap menang |

**Peta isi:** 0. Status — 1. Sumber — 2. Pemetaan kapabilitas — 3. Gap analysis — 4. Checklist pilot — 5. Cara menyampaikan — 6. Guardrail — 7. Riwayat

## 0. Status — baca ini dulu

| Status | Arti |
|---|---|
| **DIPELAJARI** | Sumbernya dokumentasi publik GitHub, sudah dibaca dan dipetakan |
| **TERINSTALL DI LAB** | Client `lamda 10.12` di venv `~/.config/opencode/firerpa-lab/venv`; server `lamda-server-x86_64 10.12` di emulator MuMu. Kedua artifact diverifikasi SHA-256 terhadap rilis GitHub resmi |
| **PILOT TERBATAS — PASS** | Koneksi, `server_info`/`device_info`, 85 package, screenshot, buka app UAT, dump hierarchy (31 node), dan WebUI HTTP 200 berhasil. Bukti lokal ada di `~/.config/opencode/firerpa-lab/` |

Konsekuensi:

- **Boleh** mengatakan "sudah terpasang di lab" dan "pilot terbatas berhasil", dengan menyebut cakupannya. **Dilarang** mengklaim "sudah dipakai di QA reguler/produksi" atau memberi angka efisiensi/benchmark — tidak ada datanya.
- Pilot ini **read-only dan non-root**: tidak ada MITM, Frida, proxy, script injection, klik, login, atau perubahan data aplikasi.
- Eksekusi MITM/Frida/root/device farm tetap **`BLOCKED`** sampai ada approval tertulis formal, scope UAT, backup/rollback, dan pilot lanjutan yang lulus.
- Penyimpangan yang tercatat: pilot memakai **MuMu**, bukan AVD resmi, karena binary emulator AVD tidak tersedia di mesin ini. Ini **bukan** pengganti kebijakan default `AVD = automation`; untuk adopsi tetap harus diulang di AVD.
- Layanan FIRERPA default **tanpa autentikasi**. Selama pilot hanya diakses lewat `adb forward tcp:65000 tcp:65000` di localhost. Jangan diekspos ke LAN tanpa sertifikat/auto-auth.
- Skill ini **tidak mengubah guardrail qa-team**. Aturan di `qa-e2e-tester` tetap menang.

---

## 1. Sumber (dokumentasi publik, bukan pengujian sendiri)

- Repository: `https://github.com/firerpa/lamda` — lisensi **MIT**.
- Saat dibaca: ~8.8k stars, ~1.2k forks. Angka ini bisa berubah; jangan dipakai sebagai metrik kinerja.
- Yang dijelaskan dokumentasinya: platform kontrol Android **full-stack** — remote desktop WebRTC/H.264 multi-user, UI automation (selector, OCR, image matching, virtual display), one-click MITM, Frida bawaan, MCP/Agent, **160+ API**, dan orientasi device farm / multi-device.

Semua pernyataan di skill ini bersifat **"menurut dokumentasi publik"**. Tulis prefix itu setiap kali menyampaikan ke manajer atau tim.

---

## 2. Pemetaan kapabilitas → relevansi Wisesa

| Kapabilitas (menurut docs) | Relevansi | Posisi qa-team hari ini | Keputusan |
|---|---|---|---|
| Remote desktop WebRTC/H.264, multi-user | Demo manajer & sesi bareng tim | Browser terlihat + video MP4 asli | **Dipelajari** — belum perlu |
| UI automation: selector, OCR, image matching | Alternatif bila selector rapuh | Appium/ADB + `resource-id`/`content-desc` | **Peluang latihan** — pilot dulu |
| Virtual display / multi-instance | Regresi paralel | Satu AVD/emulator per sesi | **Peluang latihan** |
| One-click MITM | Analisis traffic aplikasi | Probe pasif + logcat + response API | **Hanya UAT + approval tertulis** |
| Frida bawaan / root | Analisis dinamis lanjutan | Tidak dipakai | **Ditolak untuk saat ini** — di luar scope & risiko |
| MCP / agent natural language | Antarmuka tool untuk AI engineer | Agent & skill di OpenCode | **Dipelajari** — pahami kontrak tool-nya |
| 160+ API / device farm | Orkestrasi multi-device | Belum ada infra farm | **Perlu pilot & approval** |
| Tata kelola (otorisasi, read-only, `BLOCKED`) | Wajib untuk audit | Sudah melekat di qa-team | **Pertahankan sebagai keunggulan** |

---

## 3. Gap analysis ringkas

| Dimensi | qa-team | Referensi lamda | Aksi |
|---|---|---|---|
| Eksekusi mobile | Appium/ADB, AVD default, MuMu untuk demo | Selector, virtual display, OCR, image match | Latih selector lanjutan & OCR di UAT |
| Demo langsung | Emulator terlihat + video | WebRTC/H.264, multi-user | Coba sesi remote bareng manajer |
| Analisis dinamis | Probe pasif, logcat, storage | MITM + Frida | MITM terkontrol di UAT saja |
| Multi-device | Satu device/emulator | Hub / P2P / device farm | Coba 2 device saat pilot |
| Antarmuka agent | Agent & skill OpenCode | MCP server + natural language agent | Pelajari kontrak tool/MCP |
| Governance | Otorisasi, read-only, `BLOCKED` | Perlu kontrol yang sama saat dipakai | Jangan ditukar dengan fitur baru |

---

## 4. Checklist pilot — hasil 2026-11-21

| # | Syarat | Hasil |
|---|---|---|
| 1 | Approval + scope target | **Partial** — instruksi langsung user di sesi ini untuk "install, pilotkan", cakupan dibatasi lab non-produksi. Untuk adopsi resmi tetap perlu approval tertulis formal + penanggung jawab |
| 2 | Install di mesin laboratorium | **Done** — client `lamda 10.12` (SHA-256 `9ca7d3be…0639a`), server `x86_64 10.12` (SHA-256 `aafdf163…85d12`). venv dan artifact di `~/.config/opencode/firerpa-lab/` |
| 3 | Koneksi ADB terverifikasi | **Done dengan catatan** — `127.0.0.1:16384`, shell non-root, Android 15 `x86_64`. Memakai MuMu karena AVD tidak tersedia; harus diulang di AVD sebelum adopsi |
| 4 | Skenario pembanding login → Home | **Belum** — baru sebatas buka `com.bhn.advantage.dctmob/.SplashActivity`, dump hierarchy 31 node, dan screenshot. Belum ada perbandingan berpasangan dengan Appium; butuh kredensial uji + scope |
| 5 | Uji demo remote desktop | **Partial** — WebUI `http://localhost:65000/` merespons HTTP 200 (31 KB HTML). Belum diuji multi-user / rekaman demo bareng manajer |
| 6 | Uji MITM | **Tidak dilakukan** — sesuai guardrail; butuh consent tertulis, backup/rollback, dan UAT |
| 7 | Catat hasil apa adanya | **Done** — `pilot-result.json`, `pilot-app-result.json`, `pilot-hierarchy.xml`, dan 2 screenshot asli di folder lab. Tanpa angka rekaan |
| 8 | Keputusan | **`DIPAKAI SEBAGIAN — PILOT LANJUTAN`** — layak untuk evaluasi selector/screenshot/remote desktop; belum untuk adopsi penuh. Blocker: ulang di AVD, pembandingan Appium, approval formal |

Bukti pilot bukan artefak QA dan **tidak boleh** dimasukkan ke `triage.json` atau DOCX E2E.

---

## 5. Cara menyampaikan hasil evaluasi

- Bentuknya ringkasan kualitatif: tabel pemetaan, gap analysis, checklist pilot, dan rekomendasi adopsi.
- Boleh masuk ke slide training/PPTX manajer bila diminta, sebagai **lampiran evaluasi**, bukan laporan temuan QA.
- Jangan campur dengan `triage.json` atau DOCX E2E — ini bukan hasil pengujian aplikasi.
- Tiap kapabilitas beri status: `DIPELAJARI` / `PERLU PILOT` / `DITOLAK (alasan)`.
- Bahasa profesional: "evaluasi referensi", "belum diintegrasikan", "menunggu pilot". Hindari "AI hacker otonom" dan angka efisiensi buatan.

---

## 6. Guardrail

- Install dan pilot read-only di lab dilakukan atas instruksi langsung user. **Semua hal di luar itu** (MITM, Frida, root, device farm, produksi) tetap butuh otorisasi tertulis.
- MITM, Frida, root, dan device farm **hanya** setelah pilot lanjutan + approval; tidak pernah di produksi.
- Kredensial uji tetap di `qa-credentials.local.json`, tidak di chat. Pilot ini tidak memakai kredensial apa pun.
- Bila ada risiko perubahan permanen pada data produksi → **berhenti**, laporkan `BLOCKED`.
- Layanan FIRERPA tidak boleh diekspos tanpa autentikasi/sertifikat. Selama pilot: localhost + `adb forward` saja.
- Hasil pilot tidak boleh dibungkus sebagai bukti bahwa fitur sudah dipakai di QA reguler atau lebih cepat/lebih baik dari Appium.

---

## 7. Riwayat

- 2026-11-21: skill dibuat sebagai referensi evaluasi/training. Status awal sengaja `DIPELAJARI · BELUM DIINSTALL · BELUM DIPILOTKAN` agar tidak ada klaim berlebih.
- 2026-11-21: atas instruksi user, client/server `lamda 10.12` dipasang di lab terpisah (artifact terverifikasi SHA-256). Pilot terbatas non-root di MuMu Android 15: koneksi, info device, 85 package, screenshot, buka app UAT, dump hierarchy 31 node, WebUI HTTP 200 — **PASS**. MITM/Frida/root tidak dijalankan. Status diperbarui menjadi `DIPELAJARI · TERINSTALL DI LAB · PILOT TERBATAS PASS`; adopsi penuh masih menunggu pilot di AVD + pembandingan Appium + approval formal.
