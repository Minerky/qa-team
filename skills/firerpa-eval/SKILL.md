---
name: firerpa-eval
description: Referensi evaluasi & training FIRERPA/lamda — pemetaan kapabilitas dari dokumentasi publik, checklist pilot, batas otorisasi MITM/Frida/root, dan kriteria adopsi untuk qa-team. Status DIPELAJARI, BELUM DIINSTALL, BELUM DIPILOTKAN. Tidak menjalankan alat dan tidak mengklaim benchmark. Trigger: evaluasi lamda, training firerpa, bandingkan qa-team dengan firerpa.
---

# Evaluasi referensi FIRERPA / lamda (`firerpa-eval`)

Skill ini **hanya untuk belajar dan menilai**, bukan untuk menjalankan FIRERPA/lamda. Dia menjawab: "apa yang ditawarkan repo itu, apa relevannya untuk PT Wisesa, dan apa yang harus dibuktikan sebelum dipakai?"

## 0. Status — baca ini dulu

| Status | Arti |
|---|---|
| **DIPELAJARI** | Sumbernya dokumentasi publik GitHub, sudah dibaca dan dipetakan |
| **BELUM DIINSTALL** | lamda tidak ada di mesin kita; tidak ada biner/layanan yang dijalankan |
| **BELUM DIPILOTKAN** | Tidak ada skenario uji, tidak ada metrik, tidak ada bukti lokal |

Konsekuensi:

- **Dilarang** mengklaim "sudah memakai lamda", "sudah menguji", atau memberi angka efisiensi/benchmark. Tidak ada datanya.
- **Dilarang** menjalankan MITM, Frida, root, device farm, atau fitur lain dari lamda lewat skill ini.
- Kalau user meminta eksekusi/implementasi, jawab **`BLOCKED`** dan sebut syaratnya: install di mesin laboratorium, scope UAT tertulis, approval, dan pilot yang lulus. **Jangan** mencoba "coba sebentar saja".
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

## 4. Checklist pilot — syarat sebelum adopsi

Jalankan **hanya setelah** item ini lengkap:

1. **Approval tertulis** + scope target (UAT/staging), daftar akun uji, dan penanggung jawab.
2. **Install lamda di mesin laboratorium**, catat versi dan konfigurasi. Jangan langsung ke laptop kerja produksi.
3. **Koneksi ADB terverifikasi** ke AVD resmi (`emulator-5554`) atau perangkat uji — bukan ke perangkat produksi.
4. **Satu skenario pembanding**: jalankan alur login → Home yang sudah ada di qa-team, lalu ulangi dengan selector/OCR lamda. Bandingkan dengan hasil Appium yang sudah terverifikasi.
5. **Uji demo**: apakah remote desktop benar-benar terlihat dan bisa dipakai bareng manajer? Rekam buktinya bila ya.
6. **Uji MITM hanya bila diizinkan**: di UAT, dengan consent tertulis, ada backup/rollback, dan tidak menyentuh data pelanggan sungguhan.
7. **Catat hasil apa adanya**: yang berhasil, yang gagal, stabilitas, dan biaya. **Tanpa angka rekaan.**
8. **Keputusan**: `DIPAKAI` / `DIPAKAI SEBAGIAN` / `TIDAK DIPAKAI`, disertai alasan. Kalau pilot tidak bisa dijalankan, status tetap **`BELUM DIPILOTKAN`**.

---

## 5. Cara menyampaikan hasil evaluasi

- Bentuknya ringkasan kualitatif: tabel pemetaan, gap analysis, checklist pilot, dan rekomendasi adopsi.
- Boleh masuk ke slide training/PPTX manajer bila diminta, sebagai **lampiran evaluasi**, bukan laporan temuan QA.
- Jangan campur dengan `triage.json` atau DOCX E2E — ini bukan hasil pengujian aplikasi.
- Tiap kapabilitas beri status: `DIPELAJARI` / `PERLU PILOT` / `DITOLAK (alasan)`.
- Bahasa profesional: "evaluasi referensi", "belum diintegrasikan", "menunggu pilot". Hindari "AI hacker otonom" dan angka efisiensi buatan.

---

## 6. Guardrail

- Otorisasi tertulis untuk apa pun yang keluar dari membaca dokumentasi.
- MITM, Frida, root, dan device farm **hanya** setelah pilot + approval; tidak pernah di produksi.
- Kredensial uji tetap di `qa-credentials.local.json`, tidak di chat.
- Bila ada risiko perubahan permanen pada data produksi → **berhenti**, laporkan `BLOCKED`.
- Hasil evaluasi tidak boleh dibungkus sebagai bukti bahwa fitur sudah bekerja.

---

## 7. Riwayat

- 2026-11-21: skill dibuat sebagai referensi evaluasi/training. Status sengaja `DIPELAJARI · BELUM DIINSTALL · BELUM DIPILOTKAN` agar tidak ada klaim berlebih.
