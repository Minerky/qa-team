---
name: qa-web-e2e
description: Protokol eksekusi QA E2E khusus web aplikasi — Playwright browser terlihat, watch mode + dashboard + diff engine, eksplorasi menyeluruh, a11y WCAG 2.2 AA, responsif, console/network, API web, dan pentest web detection-safe. Harus dipasangkan dengan core qa-e2e-tester. Trigger: e2e web, test web, jalankan E2E web.
---

# Web QA — protokol eksekusi (`qa-web-e2e`)

**Muat dulu skill `qa-e2e-tester` (CORE).** Skill ini hanya menambah cara eksekusi di browser. Aturan inti — intake, auto-resolve, kredensial, guardrail, format temuan, anotasi merah, satu DOCX, Bab Kesimpulan — tetap mengikuti CORE dan **menang** bila bertentangan.

Target: aplikasi web di URL yang berasal dari perintah atau dokumen pendukung. **Jangan mengarang URL.** Kalau tidak ada sumber, tanya sekali.

---

## 1. Tool browser & mode tampilan

1. Pakai tool Playwright yang tersedia di sesi lewat Code Mode. **Cek katalog dengan `search` dulu** untuk nama/signature yang benar (mis. `tools.playwright.browser_navigate`, `browser_snapshot`, `browser_click`, `browser_evaluate`, `browser_take_screenshot`, `browser_console_messages`, `browser_close`). Jangan mengarang nama tool.
2. Eksekusi ad-hoc tidak perlu `npm install`. CLI/spec Playwright dipakai hanya kalau user minta suite reproducible.
3. **Default: browser terlihat** saat demo dan saat `--watch`. Headless/background hanya untuk regression yang tidak didemokan.
4. `--watch`: aktifkan tiga hal sekaligus — browser terlihat, `watch-dashboard.html`, dan diff engine. Simpan baseline screenshot, lalu bandingkan. Jangan klaim "visual diff" tanpa baseline dan hasil perbandingan nyata. Kalau dashboard tidak bisa dibuat, tandai `BLOCKED`.

---

## 2. Inisialisasi & reset state

1. Buka `TARGET_URL`, lalu `localStorage.clear()` / `sessionStorage.clear()` lewat `browser_evaluate`, reload.
2. Pastikan environment **staging/UAT** atau ada approval tertulis untuk produksi. Data uji harus bisa di-reset.
3. Login memakai akun dari `.env.qa` / `qa-credentials.local.json` — jangan pernah minta di chat. Tampilkan nilai yang tersedia apa adanya sesuai aturan CORE; yang tidak ada → `(...)`.
4. Catat role yang dipakai. Kalau ada beberapa role, ulangi alur inti per role (terutama untuk uji 401/403).

---

## 3. Matrix eksplorasi menyeluruh

Jalankan bertahap **Happy Path → Negative → Boundary → Chaos/Edge Case**, satu per satu, tanpa melewatkan elemen.

### 3.1 Interaktivitas
- `browser_snapshot` / `browser_evaluate` untuk memindai semua `button`, `a`, `input[type=button|submit]`, tab, accordion, modal, dan panel tersembunyi.
- **Semua** tombol diklik (termasuk ikon kecil: +, -, edit, delete, view, download, export, import, print, close, cancel, refresh, collapse, expand). Yang tidak bisa diklik → `BLOCKED` + bukti.
- **Semua** input diuji: text, password, number, date picker, range bulan, dropdown single/multi, radio, checkbox, textarea, file upload.
- **Semua** tab/sub-tab/accordion dibuka; cek konten dan fungsinya, bukan hanya tampil.

### 3.2 Validasi, boundary & probe injeksi
- Submit kosong: pesan error harus spesifik per field.
- Boundary: 0, 1, max, max+1, minus, desimal, email tanpa `@`/domain, telepon berisi teks.
- Anti-duplikasi/primary key bentrok, masking & regex.
- Payload **non-destruktif** pada semua input/search: XSS (`<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`), SQLi (`' OR '1'='1`), path traversal (`../../etc/passwd`). Catat apakah payload dirender, diescape, atau ditolak. Jangan menjalankan payload destruktif seperti `DROP TABLE`.

### 3.3 Tampilan, aksesibilitas & visual regression
- Simpan baseline tiap halaman kunci; saat `--watch`, bandingkan dan laporkan pergeseran layout, tombol, ukuran, font, warna.
- Cek console/pageerror: 404 font/gambar, CSS/JS missing, JS exception. `console/pageerror = 0` untuk halaman inti; kalau tidak, buat temuan.
- Cek z-index bertumpuk/backdrop modal menghalangi klik, overflow horizontal/vertikal tabel, konsistensi label vs placeholder vs format data.
- **Aksesibilitas WCAG 2.2 AA** (minimum): nama aksesibel tombol/input, fokus keyboard & urutan tab, kontras teks, label form terhubung, aria pada modal, target ukuran sentuh yang memadai. Uji dengan snapshot aksesibilitas + navigasi keyboard. Yang tidak bisa diverifikasi otomatis → `BLOCKED`, jangan diklaim lolos.
- **Responsif**: uji breakpoint desktop/tablet/mobile. Cek navbar, tabel, modal, dan tombol aksi tidak terpotong. Screenshot per breakpoint.

### 3.4 Performa & jaringan
- Pantau durasi tiap route dan request API yang dipakai halaman; flag bila > 2.000 ms.
- Catat status HTTP, endpoint, dan request/response ringkas (tanpa credential) untuk temuan yang berkaitan dengan backend.

### 3.5 Resiliensi & keamanan web (izin tertulis sudah ada)
- Rapid multi-click/race condition pada Save/Delete/Approve.
- Inversi tanggal (Date To < Date From), bypass role dengan akses URL langsung.
- Auth/session: tanpa token → `401`, cross-role → `403`, logout menginvalidasi token.
- CSRF token, CORS, security header (CSP, HSTS, X-Frame-Options, X-Content-Type-Options), cookie flag (`HttpOnly`, `Secure`, `SameSite`).
- Upload file: tipe/ukuran/eksekusi; directory listing; verbose error/stack trace; open redirect.
- OWASP ZAP baseline/active scan **hanya pada scope yang disetujui**. Probe deteksi-safe; eksploitasi aktif butuh approval + backup/rollback.
- Validasi manual temuan HIGH/CRITICAL sebelum ditutup.

### 3.6 Clean teardown
Identifikasi data dummy/transaksi uji yang dibuat, lalu lakukan cleanup/rollback yang **disetujui**. Jangan menghapus data produksi. Kalau cleanup tidak bisa dilakukan, catat di Bab Batasan.

---

## 4. Bukti & pelaporan

1. **Screenshot wajib pada tiap temuan**, segera saat anomali/state muncul. Simpan asli di `pendukung/bukti/web/<id>.png`.
2. Cantumkan anotasi di `triage.json` memakai schema CORE: `shots: [{ref, highlight:{type:"circle"|"box", ...}, label}]`. Koordinat relatif 0–1. Tanpa `highlight`, temuan dianggap belum selesai.
3. Dasarkan asersi pada **snapshot aksesibilitas, teks DOM, console, dan response JSON** — jangan klaim "membaca screenshot".
4. `location` memakai format `URL + selector/elemen`, mis. `https://staging.../login · input#nik`.
5. Untuk `e2e all`: tulis `pendukung/ai/triage.web.json`, ID diawali `WEB-`, screenshot di `pendukung/bukti/web/`. **Jangan generate DOCX** — `@qa-lead` yang menggabungkan.
6. Untuk `e2e web` saja: tulis `pendukung/ai/triage.json` dengan `report.profile = "web"`, lalu jalankan generator CORE satu kali dan verifikasi.

---

## 5. Batasan tegas

- Android/APK/iOS → bukan scope skill ini. Kembalikan ke `@qa-lead` untuk `@qa-mobile-engineer`.
- `BLOCKED` lebih baik daripada "lolos" palsu: selector tidak stabil, akses ditolak, CAPTCHA, OTP sungguhan, atau produksi tanpa approval.
- Jangan menulis angka efisiensi atau klaim otomasi penuh tanpa bukti.
- Jangan membuat laporan terpisah untuk aksesibilitas, keamanan, atau performa — semuanya masuk satu DOCX.
