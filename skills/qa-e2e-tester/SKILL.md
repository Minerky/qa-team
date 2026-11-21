---
name: qa-e2e-tester
description: CORE aturan QA E2E — intake otomatis, kredensial lokal, guardrail, format temuan + anotasi merah, verifikasi DB read-only, generator satu DOCX dengan Bab Kesimpulan. WAJIB dipasangkan dengan skill domain qa-web-e2e atau qa-mobile-e2e. Dipakai juga saat menggabungkan hasil e2e all.
---

# QA E2E — CORE (`qa-e2e-tester`)

Skill ini adalah **kulit aturan**, bukan protokol eksekusi. Isinya berlaku untuk web maupun mobile. Protokol teknis ada di dua skill domain:

| Skill domain | Dipakai untuk | Agent pemakai |
|---|---|---|
| `qa-web-e2e` | Playwright, browser terlihat/`--watch`, a11y, responsif, console, API web, pentest web | `qa-web-engineer` |
| `qa-mobile-e2e` | AVD/ADB/MuMu, Test Mode, Appium, video asli, logcat, pentest mobile | `qa-mobile-engineer` |

**Aturan di sini selalu menang** bila ada kontradiksi dengan skill domain. Jangan jalankan E2E hanya dengan core — muat salah satu skill domain lebih dulu. Pengecualian: `@qa-lead` boleh memakai core saja untuk **menggabungkan** hasil `e2e all` menjadi satu DOCX.

---

## 0.1 Aturan pelaporan — satu laporan, satu source of truth

- Semua disiplin (functional, web, mobile, API, security, network, performance) masuk **SATU** `Laporan-[TARGET]-v[VER]-[TANGGAL].docx`.
- Jangan membuat `laporan-pentest.docx`, `network-assessment.docx`, `performance-baseline.xlsx`, atau DOCX per disiplin.
- Source of truth temuan: `ai/triage.json`. Untuk `e2e all`, web menulis `triage.web.json` (ID `WEB-`), mobile menulis `triage.mobile.json` (ID `MOB-`), lalu lead menggabungkan keduanya menjadi `triage.json` sebelum generate.
- **Bab Kesimpulan & Rekomendasi Akhir wajib** ada.
- **Temuan sekecil apa pun tidak boleh lolos dari report** — INFO/LOW/cosmetic/typo tetap lengkap.

> Instalasi di laptop baru ada di `PANDUAN-LENGKAP.md` dan `README.md` repo `qa-team` — dibaca manusia, bukan instruksi agent.

---

## 0.2 Perintah & routing

| Perintah | Agent | Skill domain |
|---|---|---|
| `e2e web [url]`, `test web <url>` | `qa-web-engineer` | `qa-web-e2e` |
| `e2e mobile [serial\|app]`, `test apk` | `qa-mobile-engineer` | `qa-mobile-e2e` |
| `e2e all` | `qa-web-engineer` + `qa-mobile-engineer` paralel, digabung `@qa-lead` | keduanya |

Alias yang dikenali: `e2e web`, `e2e mobile`, `jalankan E2E web/mobile`, `run mobile e2e`, `test web <url>`. Semua mode tetap menghasilkan satu `triage.json` dan satu DOCX (mode gabungan digabung lead).

**Auto-resolve — user cukup memerintah + menyediakan dokumen pendukung.** User **tidak** perlu mengubah kode atau men-set env manual. Agent mencari sendiri:

| Input | Sumber otomatis (urutan prioritas) |
|---|---|
| `TARGET_URL` | argumen perintah → dokumen pendukung (FSD/PRD/User Guide/Test Scripts/config di workspace) → **tanya sekali** kalau tidak ada sumber |
| `QA_USER` / `QA_PASS` / `QA_TEST_MODE_PIN` / OTP test | file lokal `.env.qa` atau `qa-credentials.local.json` di workspace → jangan diminta di chat. **Semua nilai yang tersedia di artefak ditampilkan apa adanya di laporan internal**; nilai yang tidak ada ditulis `(...)` — tanpa marker `[REDACTED]` |
| serial ADB | AVD `emulator-5554` → `mumu-cli info` → `adb devices`, bukan hardcode |
| package / APK | argumen → APK di workspace → `pm list packages` / `dumpsys` |
| test case & ekspektasi | dokumen pendukung → generate case otomatis |

**Gate sebelum eksekusi:** target & akun uji berhasil di-resolve; environment UAT/staging (atau ada approval tertulis); data uji bisa di-reset. Kredensial tidak diminta di chat dan tidak ditulis ke log runtime; di laporan internal ditampilkan sesuai aturan tunggal di bawah. RoE dicatat dari dokumen; kalau approval tidak ada, **tanya sekali** sebelum aksi yang mengubah state — jangan mengarang dan jangan berhenti dengan formulir panjang.

**Pelabelan hasil:** setiap case beri `PASS` / `FAIL` / `BLOCKED`. Kalau ada `BLOCKED`, **jangan** klaim "E2E penuh lolos" — tulis di Bab Batasan. Checklist testability: auth deterministik, akun uji + OTP test, data bisa di-reset, selector stabil (`resource-id`/`content-desc`/`data-testid`), network/TLS terkendali, matrix device, dan asersi UI + backend.

### Aturan kredensial — SATU versi (berlaku di seluruh skill)

Identitas, role, sumber akun, metode login, **password, PIN Test Mode, OTP, nomor HP, NIK, token, chat ID, dan Android ID ditampilkan apa adanya** di laporan internal (satu tim/perusahaan) **selama nilainya tersedia di artefak**. Kredensial tetap tidak diminta di chat dan tidak ditulis ke log runtime. Kalau nilai tidak ada, tulis `(...)`; bila alur tidak dijalankan, nyatakan status `BLOCKED`. Jangan mengarang dan jangan memakai marker `[REDACTED]`. Tidak ada aturan lain yang boleh mengubah ini.

### Loop otonom vibe tester

Jalankan tanpa menunggu instruksi per langkah:

1. **Resolve** — baca perintah + dokumen + `.env.qa`; tentukan target, akun, serial, package, test case. Kalau ada yang benar-benar tidak ada, tanya **sekali**.
2. **Execute** — jalankan protokol skill domain; tiap case diberi `PASS` / `FAIL` / `BLOCKED` dengan bukti nyata.
3. **Recover** — kalau tool/ADB/browser gagal, pakai fallback yang tercantum di skill domain. Jangan berhenti hanya karena koneksi putus; coba pulihkan dulu.
4. **Triage** — tulis semua temuan ke `ai/triage.json` (atau `triage.web.json` / `triage.mobile.json` saat mode gabungan), termasuk `BLOCKED`.
5. **Report** — hasilkan satu DOCX: ringkasan, temuan, risk register, daftar test case, batasan, bukti, **Kesimpulan**.
6. **Stop** — hanya saat scope selesai, approval ditolak, atau target produksi berisiko. Laporkan state terakhir tanpa klaim berlebihan.

---

## 0. GUARDRAIL WAJIB (LEGAL & SAFETY)

- **Izin tertulis**: Jalankan pentest/scan HANYA pada target milik sendiri atau yang memiliki authorization/scope tertulis (URL, IP, hostname, APK/IPA, akun uji). Jika tidak ada izin, berhenti dan minta konfirmasi.
- **Batasi scope**: Tidak boleh memindai host di luar daftar yang disetujui. Tidak boleh melakukan eksploitasi destruktif, DDoS, ransomware, defacement, atau penghapusan data produksi.
- **Mode aman default**: Gunakan probe deteksi (payload non-destruktif, scan pasif/ringan, validasi header/konfigurasi). Eksploitasi aktif hanya boleh setelah user menyetujui langkah dan tersedia backup/rollback.
- **Data sensitif**: ikuti **Aturan kredensial — SATU versi** di §0.2. Redaction wajib diterapkan ke DOCX, log, dan artifact.
- **Production gate**: Jika target adalah produksi dan ada risiko outage/perubahan data, minta approval eksplisit sebelum aksi yang mengubah state.
- **Audit trail**: Setiap aksi tercatat di `hasil-test/ai/audit-log.jsonl` (waktu, target, tool, hasil, keputusan).

---

## 1. PRINSIP UTAMA: EXHAUSTIVE & GRANULAR TESTING

1. **Target Interactivity Coverage** (yang tidak bisa diuji → `BLOCKED`, bukan dilewati): semua tombol (primer, sekunder, ikon kecil, tambah/hapus/unduh/ekspor), semua input, semua tab/accordion/panel tersembunyi wajib dicoba.
2. **Validasi & probe keamanan**: blank submission, boundary (0, 1, max, max+1, minus, desimal, format email/telepon salah), anti-duplikasi, masking/regex, serta payload non-destruktif XSS/SQLi/path traversal pada semua field.
3. **Tampilan & visual regression**: simpan baseline, deteksi pergeseran layout/ukuran/font/warna; cek 404 asset, z-index bertumpuk, overflow tabel, konsistensi label vs format data.
4. **Performa & latency**: pantau durasi route halaman dan request API; flag bila > 2.000 ms.
5. **Resiliensi**: rapid multi-click/race condition pada Save/Delete/Approve, inversi tanggal, broken session, dan bypass role.
6. **Data lifecycle**: identifikasi data dummy/transaksi uji, lalu lakukan cleanup/rollback yang disetujui agar lingkungan tetap bersih.

Detail teknis per platform ada di `qa-web-e2e` dan `qa-mobile-e2e`.

---

## 2. DUKUNGAN INPUT PENGUJIAN

| Mode | Input user | Peran & alur QA |
|---|---|---|
| **Mode 1: Script + FSD/PRD + URL** | Spesifikasi + test script + URL | Eksekusi script, validasi terhadap FSD, tambah negative case, laporkan hasil |
| **Mode 2: Spec-Driven** | FSD/PRD/User Guide + URL | Bedah aturan bisnis, susun matrix happy/negative, eksekusi, gap analysis |
| **Mode 3: Whitebox** | Source code + URL | Analisis arsitektur, state, endpoint, validasi form, eksekusi live |
| **Mode 4: Pure Blackbox** | Hanya URL | Eksplorasi UI/UX mandiri, identifikasi role/form/tombol/validasi |
| **Mode 5: Mobile Binary** | APK + akun uji (± source) | Instal, Test Mode, eksplorasi UI, statis + dinamis, pentest mobile |
| **Mode 6: Network Scope** | IP/host/CIDR + izin tertulis | Mapping port/layanan, review TLS, risk scoring jaringan |

Untuk Mode 5 dan Mode 6, **guardrail bagian 0 wajib** dipenuhi sebelum eksekusi.

---

## 3. PROTOKOL LINTAS DOMAIN

### A. API (web & mobile)

1. Ekstraksi endpoint: Base URL, method, path, query, header (mis. `Authorization`, `Android-ID`, `Content-Type`), dan schema payload — dari dokumen, network inspection, atau kode yang tersedia.
2. Happy path: status `200`/`201`, struktur JSON, dan keakuratan data yang tersimpan.
3. Negative & boundary: payload kosong, tipe salah, field wajib hilang, nilai batas → `400`/`422` dengan pesan informatif.
4. Auth/security: tanpa token → `401`, cross-role → `403`, payload XSS/SQLi non-destruktif pada field JSON.
5. Latency: flag > 2.000 ms; uji timeout/offline — jangan menampilkan stack trace mentah ke client.

### B. Jaringan (authorized only)

Prasyarat: daftar IP/host/CIDR + izin tertulis.

1. Recon pasif/ringan: DNS, host hidup, banner/versi layanan.
2. Mapping port: `nmap -sV --top-ports 1000 <scope>` (full port hanya jika disetujui).
3. TLS: versi/cipher, expired/self-signed, redirect HTTP→HTTPS, HSTS.
4. Konfigurasi: firewall/ACL, SSH/Telnet/SNMP terekspos. Default credential **hanya di lab milik sendiri**.
5. Dilarang: exploit aktif, DoS, pivot di luar scope, password spraying tanpa approval.
6. Output: inventory `host:port:service` + risk score per host.

### C. Lapisan orkestrasi AI — koordinator, bukan pengganti bukti

1. **Generate**: test matrix (happy/negative/chaos) dari FSD/PRD/user guide; untuk blackbox, hipotesis dari UI yang ditemukan.
2. **Execute assist**: sarankan langkah berikutnya, parameter boundary, payload aman sesuai guardrail.
3. **Triage**: deduplikasi, klasifikasi Functional Bug / Security Risk / Network Risk, `Risk = Likelihood × Impact`, beri `confidence`.
4. **Explain**: terjemahkan temuan teknis ke dampak bisnis dan prioritas rekomendasi.
5. **Report**: ringkasan eksekutif + heatmap + top risks ke DOCX.
6. **Aturan emas**: AI **tidak boleh mengarang bukti**. Setiap risk harus punya path screenshot/log/request-response nyata dan entri di `triage.json`.

---

## 4. STANDAR FORMAT TEMUAN & ATRIBUT DEFECT REPORTING

- 🔴 **HIGH / CRITICAL**: error sistem, 500, SQLi/XSS, data loss, RBAC bypass, secret terekspos, layanan kritis terekspos.
- 🟡 **MEDIUM**: validasi lolos data invalid, duplikasi, logic error, overlay crash, misconfig TLS/cookie/header, yellow screen.
- 🟢 **LOW / UX**: link/tombol mati, 404 font/gambar, typo, label misleading, indikator mandatory buram.

**Risk scoring (wajib untuk temuan keamanan):** `Likelihood` 1–5 × `Impact` 1–5 → `Risk` 1–25. Mapping: **20–25 Critical**, **12–19 High**, **6–11 Medium**, **1–5 Low**. Boleh tambah CVSS v3.1. Setiap risk wajib punya lokasi eksplisit (URL/endpoint/`host:port`/file/komponen APK/layar). `AI Confidence`: `high`/`medium`/`low`; Critical/High wajib divalidasi manual.

### Aturan bukti — temuan sekecil apa pun tidak boleh lolos dari report

**Semua temuan wajib masuk report. Tidak ada yang boleh dibuang, difilter, atau dianggap terlalu sepele.** Untuk **setiap** temuan:

1. **Proses kejadian (reproduksi) eksplisit** — urutan aksi nyata: klik/tap tombol mana, isi field apa, scroll ke mana, URL/layar/elemen, dan hasil yang terlihat. Jangan hanya menulis "tombol tidak jalan". Contoh: `1. Buka /login; 2. Klik ikon titik-tiga kanan atas; 3. Ketik PIN di field Password; 4. Klik SUBMIT; 5. Amati IS_SERVER berubah menjadi false.`
2. **Screenshot asli + anotasi merah** — ambil screenshot saat asersi, lalu **lingkari** (default) atau **kotakkan merah** area temuan. Simpan aslinya di `pendukung/bukti/<domain>/`, lalu cantumkan anotasinya di `triage.json`:
   ```json
   "shots": [{
     "ref": "pendukung/bukti/web/01_login.png",
     "highlight": {"type": "circle", "x": 0.62, "y": 0.31, "w": 0.18, "h": 0.12},
     "label": "Pesan error di sini"
   }]
   ```
   `x,y,w,h` relatif 0–1 (nilai > 1 dibaca piksel). `type: "box"` untuk kotak; alternatif lingkaran: `{"type":"circle","cx":...,"cy":...,"r":...}`.
3. **Tertanam di DOCX** — generator menyisipkan gambar yang sudah dilingkari merah **tepat di bawah temuan yang bersangkutan**. Bila `highlight` kosong, DOCX menandai *"belum dianotasi merah"* dan temuan dianggap belum selesai.

Template detail bug wajib:

```markdown
### [SEVERITY] [BUG-XX / RISK-XX]: [Judul Singkat]
- **Kategori:** Functional Bug | Security Risk | Network Risk
- **Lokasi / Halaman / Host:** [URL / endpoint / host:port / file / komponen APK/IPA / tab]
- **Likelihood (1-5) / Impact (1-5) / Risk Score:** [L] / [I] / [L×I]
- **CVSS (opsional):** [vektor + skor]
- **Langkah Reproduksi (klik/tap apa, berurutan):**
  1. [Buka halaman/URL mana, klik tombol/link/tab apa]
  2. [Ketik field apa, lalu klik tombol apa]
  3. [Amati perubahan/apa yang muncul — sebut elemen & teksnya]
- **Kondisi Aktual (Actual):** [Apa yang terjadi]
- **Kondisi Harapan (Expected):** [Apa yang seharusnya terjadi sesuai spesifikasi]
- **Dampak Bisnis:** [Contoh: kebocoran data pelanggan, takeover akun, downtime]
- **Rekomendasi Solusi Teknis:** [Saran perbaikan untuk developer/ops]
- **Bukti Visual (screenshot + lingkaran merah):** [path file asli + koordinat `highlight`]
- **AI Confidence:** [high / medium / low]
```

### Verifikasi database (read-only) — lapisan bukti tambahan

Gunakan bila temuan atau alur uji punya **state di database**. Ini melengkapi `UI → API → jaringan → penyimpanan → log`.

1. **Koneksi dari file kredensial lokal** — prioritas: `QA_CREDENTIALS_FILE` → `%USERPROFILE%\.config\opencode\qa-credentials.local.json` → `qa-credentials.local.json` di folder skill. Repo menyimpan **`qa-credentials.example.json`** (template kosong, aman di-commit). Setelah clone: `copy qa-credentials.example.json qa-credentials.local.json`, lalu isi file `.local.json` — nama itu sudah masuk `.gitignore`. Blok `db` berisi `sqlite` / `server` / `database` / `user` / `password` / `auth` / `driver` / `limit`. Environment variable (`QA_DB_SQLITE`, `QA_DB_SERVER`, `QA_DB_NAME`, `QA_DB_USER`, `QA_DB_PASS`, `QA_DB_AUTH`, ...) tetap lebih prioritas. Kredensial **tidak pernah** ditulis di chat/spec/DOCX.
2. **Jalankan** `python db_verify.py --checks <file-json> --out pendukung/ai/db-verification.json`.
3. **Read-only keras** — hanya `SELECT` / `WITH` / `PRAGMA`, satu statement per check. `db_verify.py` menolak `INSERT`/`UPDATE`/`DELETE`/`DROP` dan multi-statement.
4. **Tambahkan bab ke DOCX** — masukkan `"db_verification"` ke `report.chapters` di `triage.json`.
5. **Aturan temuan tetap berlaku** — bila asersi `FAIL`/`ERROR`, buat temuan dengan langkah reproduksi + screenshot lingkaran merah. DB tidak terjangkau → `BLOCKED`.
6. **Gunakan akun read-only dan staging/UAT dulu.** Data pelanggan yang tampil di hasil query tunduk pada aturan pelaporan di atas.
7. **Stored procedure — baca definisi, jangan eksekusi.** SQL Server: kunci `sp` exact/wildcard/schema, `definition_contains`, `definition_all`, `contains_all`, `offset`/`limit`, `total_matching`. `db_verify.py` menerjemahkan ke `SELECT` katalog `sys.sql_modules`/`sys.objects` dengan parameter binding. **`EXEC` tidak didukung** karena isi prosedur bisa mengubah data.
8. **Lacak notifikasi → SP tanpa mengisi kredensial.** `python find_notif.py --text "<notifikasi>"` mencari target dari file kredensial → connection string di `appsettings*.json` / `web.config` / `.env` / `docker-compose*.yml` → instance lokal. Windows Integrated Auth dipakai bila tanpa password. Hanya nama server/database yang diekstrak. Output `pendukung/ai/sp-notif-search.json`. Tetap `SELECT` katalog. Tidak ada target → `BLOCKED`, bukan ditebak.

### 4.1 Skema `triage.json`

Jangan menyensor nilai di artifact maupun DOCX. Terapkan aturan tunggal: nilai tersedia → ditulis apa adanya; nilai tidak ada → `(...)`, bukan `[REDACTED]`; kredensial tidak diminta di chat dan tidak ditulis ke log runtime. Verifikasi akhir memastikan tidak ada marker `[REDACTED]` di DOCX maupun `pendukung/ai/*`.

Field minimal tiap entri: `id`, `title`, `category` (`Functional Bug` / `Security Risk` / `Network Risk`), `severity`, `location`, `likelihood`, `impact`, `risk_score`, `cvss` (opsional), `actual`, `expected`, `business_impact`, `recommendation`, `evidence[]` (path nyata), `confidence`, `chain`, `status` (`PASS`/`FAIL`/`BLOCKED`), `shots[]`.

---

## 5. GENERASI ARTEFAK OUTPUT

Satu folder target berisi **tepat satu `.docx`** di root dan satu folder `pendukung/`:

```
hasil-test-<target>/
  Laporan-<TARGET>-v<VER>-<TANGGAL>.docx   ← satu-satunya file di root
  pendukung/
    ai/triage.json          ← source of truth (mode gabungan: .web + .mobile → digabung)
    ai/triage.web.json      ← khusus e2e all, dari web engineer
    ai/triage.mobile.json   ← khusus e2e all, dari mobile engineer
    ai/audit-log.jsonl      ← jejak eksekusi
    ai/generated-cases.md   ← daftar test case (juga disisipkan di DOCX)
    bukti/web/              ← screenshot, HAR, console (web)
    bukti/mobile/           ← screenshot, MP4, logcat, dump XML (mobile)
    automation/             ← spec Playwright/WDIO (opsional)
```

Isi wajib DOCX: halaman judul & meta, ringkasan eksekutif + metrik, metodologi, lingkungan pengujian (**termasuk akun uji sesuai aturan §0.2**), temuan gabungan (lokasi, `L×I`, CVSS, dampak bisnis, rekomendasi, bukti), hasil functional/web/mobile/API/security/network/performance, **risk register sebagai tabel**, **daftar test case sebagai lampiran**, rekomendasi prioritas, batasan & `BLOCKED`, **bab Kesimpulan & Rekomendasi Akhir**, lampiran bukti. DOCX hanya mencatat hasil uji — **jangan sisipkan catatan pengembangan skill, status tool, atau referensi `SKILL.md`**.

Generator: `python-docx`. `openpyxl` **hanya** bila user eksplisit minta Excel terpisah. Verifikasi akhir: struktur bab lengkap, satu `.docx`, tidak ada `[REDACTED]`, nilai tersedia tampil sesuai aturan §0.2.

### 5.1 Generator kanonik

Jangan menulis ulang script DOCX per target. Pakai generator di folder skill inti `qa-e2e-tester` (atau salinan lokalnya di `~/.config/opencode/skills/qa-e2e-tester/`):

```bash
python <folder skill qa-e2e-tester>/build_report.py --root hasil-test-<target>
python <folder skill qa-e2e-tester>/build_report.py --root hasil-test-<target> --verify
```

- `report_kit.py`: styling, tabel, gambar tertanam (anotasi merah), parser `generated-cases.md`, inventaris bukti, verifier. Buta terhadap web/mobile dan tidak melakukan redaction.
- Target menentukan isi lewat blok `report` di `triage.json`: `profile` (`web`/`mobile`/`api`/`all`), `output`, `header`/`title`/`subtitle`, `chapters`, dan blok tambahan (`table`, `paragraph`, `bullets`, `heading`, `image`, `flow_table`, `perf_table`, `page_break`).
- `--profile` mengoverride profil; `--output` hanya untuk staging saat file asli terkunci. Setelah ditutup, salin ke nama final dan jalankan ulang `--verify`.

---

## 6. RIWAYAT PERUBAHAN

- **Pemisahan domain (2026-11-21)**: `qa-e2e-tester` jadi CORE; protokol web pindah ke `qa-web-e2e`, protokol mobile ke `qa-mobile-e2e`; `qa-engineer` dibagi menjadi `qa-web-engineer` + `qa-mobile-engineer`.
- Aturan kredensial disatukan satu versi; kontradiksi dihapus.
- Output dipaksa satu DOCX; risk register & daftar test case disisipkan, bukan file terpisah.
- Anotasi merah memakai schema `shots` (`ref`/`highlight`/`label`); string lama masih didukung tapi ditandai.
- Verifikasi DB read-only, template kredensial, dan `.gitignore` tersedia di folder skill inti.
- Modul quality/security/network/performance tetap satu laporan DOCX.
- Mode pure blackbox web terbukti di Wisesa; alur eksplorasi tiap target tetap beda, yang distandardisasi hanya kulit laporan.
- Regresi DCT + Wisesa: isi bab berbeda, format identik, verifier `CLEAN`.
