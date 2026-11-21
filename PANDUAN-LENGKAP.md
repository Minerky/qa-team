# Panduan Setup Lengkap QA Team — clone → langsung pakai

Panduan ini untuk **manusia yang baru clone repo**. Tujuannya: setelah mengikuti bagian 1–4, tim QA bisa dipanggil dari chat OpenCode untuk web, mobile, database, dan bug hunting tanpa bertanya konfigurasi lagi.

Instruksi untuk agent ada di `SKILL.md` masing-masing. Panduan ini tidak mengubah aturan itu — hanya menyiapkan lingkungannya.

---

## 0. Peta cepat

| Kebutuhan | Bagian | Perintah singkat |
|---|---|---|
| Pasang agent + skill | [2](#2-instalasi-inti) | `setup.ps1` → `opencode reload` |
| Cek installment | [10](#10-verifikasi--troubleshooting) | `verify_setup.ps1` |
| Python / Playwright | [3](#3-dependensi-python) | `pip install ...` → `playwright install chromium` |
| Kredensial & DB | [4](#4-kredensial--database) | isi `qa-credentials.local.json` |
| Lacak notifikasi → SP | [4.5](#45-lacak-notifikasi--stored-procedure) | `find_notif.py --text "..."` |
| E2E web | [5](#5-web-e2e) | `@qa-lead e2e web <url>` |
| E2E Android | [6](#6-mobile-e2e) | `@qa-lead e2e mobile` |
| Bug hunt | [7](#7-bug-hunter) | `@qa-lead hunt web <url>` |
| Gabung web + mobile, 1 DOCX | [8](#8-cara-pakai-sehari-hari) | `@qa-lead e2e all <url>` |

**Aturan emas yang tidak bisa dilewati:** satu DOCX final per laporan · Bab **Kesimpulan** wajib · temuan sekecil apa pun wajib masuk · tiap temuan punya urutan klik/tap + screenshot lingkaran merah berlabel · kredensial tidak pernah diminta di chat · DB read-only · `EXEC` ditolak · video mobile asli tidak dihapus · iOS/IPA `BLOCKED`.

---

## 1. Prasyarat

### Wajib untuk semua

| Kebutuhan | Versi / catatan |
|---|---|
| Windows 10/11 | Panduan ini memakai PowerShell |
| Git | untuk `clone` / `pull` |
| OpenCode CLI | terpasang dan bisa dijalankan sebagai `opencode` |
| Python | **3.10+** (3.12 teruji). Cek: `python --version` |
| Internet | sekali untuk `pip install` dan `playwright install chromium` |

### Opsional sesuai domain

| Domain | Yang dibutuhkan |
|---|---|
| Web | Modul `playwright` + browser Chromium. Tool browser di sesi OpenCode dipakai lewat Code Mode; **tidak perlu `npm install`** untuk eksekusi ad-hoc |
| Mobile — default | Android Studio + **AVD resmi**, virtualisasi aktif (VT-x/AMD-V + WHPX/HAEVM). Android SDK minimal: `platform-tools\adb.exe` **plus** `AdbWinApi.dll` dan `AdbWinUsbApi.dll` |
| Mobile — Appium | Node 20+, Appium 4.x, driver `uiautomator2` 9.2.2, JDK 21, WebdriverIO 10.x |
| Mobile — demo lama | MuMu Player (bukan fondasi CI; port ADB harus ditanya ke `mumu-cli`, jangan ditebak `7555`) |
| Database | Akses jaringan ke SQL Server UAT/staging **atau** file SQLite. Pakai akun read-only. ODBC driver terpasang |
| FIRERPA (opsional) | Hanya evaluasi/training. Status: `DIPELAJARI · TERINSTALL DI LAB · PILOT TERBATAS PASS`. Tidak dipakai untuk produksi/MITM/Frida tanpa approval |

Catatan portabilitas: `agents/qa-lead.md` saat ini menentukan `model: opencode/big-pickle`. Bila model itu tidak tersedia di mesin/License Anda, hapus baris `model:` tersebut sebelum menjalankan `setup.ps1`, lalu simpan perubahan lokal itu (atau ganti dengan model yang tersedia).

---

## 2. Instalasi inti

Jalankan dari folder tempat Anda ingin menyimpan repo:

```powershell
git clone https://github.com/Minerky/qa-team.git
cd qa-team
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
```

`setup.ps1` melakukan:

- menyalin `agents\*.md` ke `%USERPROFILE%\.config\opencode\agents\`
- menyalin keenam folder skill ke `%USERPROFILE%\.config\opencode\skills\`
- menghapus agent lama `qa-engineer.md` bila masih ada
- membuat `%USERPROFILE%\.config\opencode\qa-credentials.local.json` **hanya bila belum ada**

Verifikasi dari **folder workspace**, bukan dari dalam `qa-team` (API bisa mengembalikan hanya built-in bila dijalankan dari repo):

```powershell
opencode api get /api/agent
opencode api get /api/skill
```

Yang harus muncul:

```
agent → qa-lead, qa-web-engineer, qa-mobile-engineer, bug-hunter, sp-specialist
skill → qa-e2e-tester, qa-web-e2e, qa-mobile-e2e, firerpa-eval, bug-hunter, sp-tracer
```

Kalau kosong sesaat, ulangi sekali setelah reload.

---

## 3. Dependensi Python

```powershell
python -m pip install python-docx pillow pyodbc playwright openpyxl
python -m playwright install chromium
```

Fungsinya:

| Modul | Dipakai untuk |
|---|---|
| `python-docx` | generator satu DOCX + verifier |
| `pillow` | anotasi merah (lingkaran/kotak + label) pada screenshot |
| `pyodbc` | koneksi SQL Server read-only |
| `playwright` | browser Chromium untuk web |
| `openpyxl` | **hanya** bila user eksplisit minta Excel terpisah |

Cek cepat:

```powershell
python -c "import docx, PIL, pyodbc, playwright, openpyxl; print('OK')"
```

---

## 4. Kredensial & database

### 4.1 Lokasi dan prioritas

File nyata:

```
%USERPROFILE%\.config\opencode\qa-credentials.local.json
```

File itu **di luar repo** dan sudah masuk `.gitignore`. Template kosong di repo bernama `qa-credentials.example.json` — **jangan pernah mengisinya dengan password**, karena ikut ter-commit.

Urutan prioritas pembacaan:

1. Environment variable `QA_CREDENTIALS_FILE` (path ke file lokal)
2. `%USERPROFILE%\.config\opencode\qa-credentials.local.json`
3. `qa-credentials.local.json` di folder skill

Environment variable `QA_DB_*` meng-override nilai di file.

**Password, PIN, OTP, dan token tidak pernah diketik di chat, tidak ditulis di spec, tidak masuk log runtime, dan tidak masuk DOCX.**

### 4.2 Isi blok `db`

Buka file lokal tersebut dan isi **salah satu** mode.

**SQL Server — Windows Integrated Auth** (disarankan bila tersedia):

```json
"db": {
  "sqlite": "",
  "server": "HOST\\\\SQLEXPRESS",
  "database": "NamaDatabaseUAT",
  "user": "",
  "password": "",
  "auth": "windows",
  "driver": "SQL Server",
  "limit": 20
}
```

**SQL Server — SQL Auth:**

```json
"db": {
  "sqlite": "",
  "server": "HOST,1433",
  "database": "NamaDatabaseUAT",
  "user": "svc_qa_readonly",
  "password": "ISI_DI_FILE_LOKAL_SAJA",
  "auth": "sql",
  "driver": "ODBC Driver 18 for SQL Server",
  "limit": 20
}
```

**SQLite:**

```json
"db": {
  "sqlite": "C:\\path\\ke\\database-uat.db",
  "server": "",
  "database": "",
  "user": "",
  "password": "",
  "auth": "sql",
  "driver": "",
  "limit": 20
}
```

Catatan yang sering bikin gagal:

- `server` memakai **backslash dobel** di JSON: `HOST\\SQLEXPRESS` ditulis `"HOST\\\\SQLEXPRESS"`. Ambil nama persis dari SSMS → klik kanan server → Properties → Server name.
- `auth`: `"windows"` atau `"sql"` (huruf kecil).
- `driver`: pada mesin dengan ODBC legacy, isi **`"SQL Server"`**. Bila ODBC 17/18 terpasang, pakai `"ODBC Driver 17 for SQL Server"` / `"ODBC Driver 18 for SQL Server"`. Dibiarkan kosong = default ODBC 18 dan bisa error bila tidak terpasang.
- `limit`: maksimal baris per query, default 20; naikkan ke 50 bila banyak stored procedure.
- Bila `sqlite` terisi, SQLite dipakai duluan dan koneksi SQL Server diabaikan.

Override Environment (opsional): `QA_DB_SQLITE`, `QA_DB_SERVER`, `QA_DB_NAME`, `QA_DB_USER`, `QA_DB_PASS`, `QA_DB_AUTH`, `QA_DB_DRIVER`, `QA_DB_LIMIT`.

### 4.3 Uji koneksi read-only

Buat file sementara `db-checks.json` di workspace:

```json
[
  {
    "id": "DB-01",
    "name": "Koneksi terbaca",
    "sql": "SELECT 1 AS ok",
    "expect": {"column": "ok", "value": 1}
  }
]
```

Jalankan:

```powershell
python "%USERPROFILE%\.config\opencode\skills\sp-tracer\db_verify.py" --checks db-checks.json --out pendukung/ai/db-verification.json
```

Hasil di `pendukung/ai/db-verification.json`. Bila DB tidak terjangkau, hasilnya **`BLOCKED`** — itu jawaban yang benar, bukan kegagalan tersembunyi. Yang dibutuhkan dari Anda adalah **nama instance / akses jaringan**, bukan password di chat.

Expect yang didukung: `value`, `min`, `max`, `contains`, `contains_all`, `row_count`, `row_count_min`, `row_count_max`, `exists`.

### 4.4 Verifikasi data saat E2E

Bila alur uji menyentuh database, minta agent menyertakan bab DB:

- buat asersi `SELECT` di `db-checks.json`
- jalankan `db_verify.py`
- tambahkan `"db_verification"` ke `report.chapters` di `triage.json`
- generator menyisipkan hasilnya ke DOCX yang sama

### 4.5 Lacak notifikasi → stored procedure

Dari teks toast/error saja — tidak perlu tahu nama SP dan tidak perlu mengisi kredensial:

```powershell
python "%USERPROFILE%\.config\opencode\skills\sp-tracer\find_notif.py" --text "Validasi gagal: area wajib diisi"
```

Opsi: `--text` (wajib), `--server`, `--database`, `--windows`, `--limit`, `--out`, `--no-discover`.

Target dicari otomatis, berurutan: file kredensial lokal → connection string di `appsettings*.json` / `web.config` / `.env` / `docker-compose*.yml` di sekitar workspace → instance SQL Server lokal. Dari file konfigurasi aplikasi, **hanya nama server dan database** yang diekstrak.

Output `pendukung/ai/sp-notif-search.json` berisi `status` (`FOUND`/`NOT_FOUND`/`BLOCKED`), `connection`, `matches[].database.schema.prosedur`, `matching_lines`, dan `definition` lengkap.

Untuk pencarian terarah, pakai `db_verify.py` dengan kunci `sp`:

```json
[
  {"id":"SP-01", "sp":"dbo.ValidateProblem",
   "expect":{"column":"definisi","contains_all":["IF @area","RAISERROR"]}},
  {"id":"SP-02", "sp":"Valid*", "limit":10, "offset":0},
  {"id":"SP-03", "sp":"*", "definition_contains":"area wajib diisi"},
  {"id":"SP-04", "sp":"*", "definition_all":["IF @status","RAISERROR"], "limit":20, "offset":20}
]
```

### 4.6 Aturan keras database

- Hanya `SELECT` / `WITH` / `PRAGMA`, **satu statement** per check.
- `INSERT` / `UPDATE` / `DELETE` / `DROP` / multi-statement ditolak.
- **`EXEC` tidak didukung** — definisi SP dibaca lewat `SELECT` katalog (`sys.sql_modules` / `sys.objects`). Prosedur tidak pernah dijalankan.
- SQLite tidak punya stored procedure; check `sp` di SQLite gagal dengan pesan jelas, bukan diklaim lolos.
- Gunakan akun read-only dan staging/UAT dulu.
- DB tidak terjangkau → `BLOCKED`, jangan dikarang.

---

## 5. Web E2E

### 5.1 Siapkan

1. Pastikan bagian [3](#3-dependensi-python) selesai dan Chromium terpasang.
2. Tool browser di sesi OpenCode dipakai lewat Code Mode. Nama namespace bisa berubah (`tools.playwright.*` atau `tools.browser.*`); agent akan mengecek katalog dengan `search` dulu. Anda tidak perlu menginstal npm apa pun untuk eksekusi ad-hoc.
3. Simpan input uji di **workspace**, bukan di repo, dalam file `.env.qa` (sudah masuk `.gitignore`):

```ini
TARGET_URL=https://staging.contoh.com
QA_USER=qa_user_uat
QA_PASS=ISI_DI_FILE_LOKAL
```

Tambahkan `QA_TEST_MODE_PIN=...` bila aplikasi memakai Test Mode. Jangan commit file ini.

### 5.2 Jalankan

```
@qa-lead e2e web https://staging.contoh.com
@qa-lead e2e web https://staging.contoh.com --watch
@qa-web-engineer test web https://staging.contoh.com --watch — sertakan aksesibilitas
```

`--watch` mengaktifkan **tiga hal sekaligus**: browser terlihat, `watch-dashboard.html`, dan diff engine dengan baseline screenshot. Tanpa baseline, jangan klaim visual diff.

Cakupan yang dijalankan agent: semua tombol/input/tab (termasuk ikon kecil), happy/negative/boundary, payload injeksi non-destruktif, aksesibilitas WCAG 2.2 AA, responsif desktop/tablet/mobile, console/network, API, dan probe keamanan deteksi-safe.

Target URL tidak boleh dikarang. Bila tidak ada di perintah maupun dokumen pendukung, agent bertanya **sekali**.

---

## 6. Mobile E2E

### 6.1 AVD — jalur default

```powershell
emulator -accel-check
emulator -list-avds
emulator -avd Pixel8_API_34 -no-boot-anim
adb devices        # harus ada emulator-5554
```

Profil disarankan: **Pixel**, API 34/35, `x86_64`, variant `google_apis` (atau `google_play` bila aplikasi bergantung Play Store/FCM). Gunakan `-wipe-data` untuk kondisi awal dan snapshot hanya untuk boot cepat.

Pastikan `platform-tools` berisi `adb.exe`, `AdbWinApi.dll`, dan `AdbWinUsbApi.dll` — tanpa dua DLL itu Appium tidak melihat device.

Pasang aplikasi dan deteksi identitas sungguhan:

```powershell
adb install -r app.apk
adb shell pm list packages | findstr <nama-package>
adb shell dumpsys activity activities | findstr mResumedActivity
```

### 6.2 Appium + WebdriverIO (resep terverifikasi)

Stack: **Appium 4.0.0**, `uiautomator2@9.2.2`, **JDK 21**, **Node 20+**, **WebdriverIO 10.x**.

```powershell
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
$env:ANDROID_HOME="$env:LOCALAPPDATA\android-sdk-minimal"
$env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
$env:PATH="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
appium server --port 4723 --base-path /wd/hub
```

Capabilities inti: `platformName: Android`, `appium:automationName: UiAutomator2`, `appium:udid: <serial>`, `appium:app: <path.apk>` atau `appPackage`/`appActivity`, `appium:noReset: false`, `appium:newCommandTimeout: 120`.

Jebakan yang sudah diatasi (jangan dihapus saat copy script lama):

- `activateApp()` wajib — tanpa itu Appium bisa membuka launcher.
- Dialog izin/notifikasi bisa muncul **dua kali**; tangani sebelum dan sesudah login.
- Toggle Test Mode harus idempoten — klik kedua akan mematikannya.
- Field PIN dialog dan password login bisa punya `resource-id` sama; scope ke dialog.
- Verifikasi NIK terbaca sebelum klik login.

### 6.3 Test Mode DCT

Untuk aplikasi DCT (Asset, Cargo, CDC, FLM, dll), **sebelum** memasukkan kredensial:

1. Di halaman login, klik ikon **titik 3** di pojok kanan atas.
2. Klik toggle **Test Mode**.
3. Masukkan PIN dari `QA_TEST_MODE_PIN`, klik **Submit**.
4. Tekan **Back** ke halaman login.
5. Pastikan mode testing aktif.

### 6.4 MuMu — hanya untuk demo visual

```powershell
& "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" info --vmindex 0
# ambil field adb_port dari JSON (contoh nyata: 16384 — jangan asumsikan 7555)

$adb = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
& $adb kill-server
& $adb start-server
& $adb connect 127.0.0.1:<adb_port>
& $adb devices
```

`unauthorized` → klik Allow. `offline` → disconnect lalu connect ulang. MuMu dicatat di Bab Lingkungan sebagai **lingkungan demo**, bukan fondasi CI. Genymotion Desktop tidak dipakai untuk automation; perangkat fisik untuk UAT akhir.

### 6.5 Bukti video

```powershell
adb -s <serial> shell screenrecord --time-limit 180 /sdcard/test.mp4
adb -s <serial> pull /sdcard/test.mp4 pendukung/bukti/mobile/e2e-lengkap.mp4
```

Video asli dari **login sampai seluruh test selesai** wajib ada bila diminta dan **tidak boleh dihapus** setelah laporan jadi. Jangan memakai `>` PowerShell untuk menyimpan PNG (merusak biner) — pakai `adb pull`, lalu cek header `\x89PNG\r\n\x1a\n`.

### 6.6 Jalankan

```
@qa-lead e2e mobile
@qa-mobile-engineer test apk — APK di folder hasil-test, rekam videonya
```

Android yang tidak bisa di-resolve, GMS tidak didukung, ADB offline permanen, atau **iOS/IPA → `BLOCKED`** (butuh macOS + Xcode; jangan diklaim tervalidasi).

---

## 7. Bug Hunter

Wajib: **otorisasi tertulis**, target (URL/IP/hostname/APK), environment (staging/UAT/produksi), daftar akun uji, dan scope yang disetujui. Tanpa itu → `BLOCKED`, bukan "coba sebentar".

```
@qa-lead hunt web https://staging.contoh.com/
@qa-lead hunt apk app-release.apk
@qa-lead hunt apk com.target.app
@qa-lead hunt all https://staging.contoh.com/ app-release.apk
@qa-lead hunt --watch 30 https://staging.contoh.com/
```

Alias: `bughunt <target>`, `bug hunter web <url>`, `bug hunter apk <file>`.

Guardrail: probe non-destruktif sebagai default, tanpa DoS/flood, tanpa eksploitasi yang mengubah data produksi permanen. Bila ada risiko perubahan permanen tanpa rollback → **berhenti**, tandai `BLOCKED`. Draft HackerOne/Bugcrowd masuk **appendix di dalam DOCX**, bukan file `.md` terpisah.

Mode `--watch` memakai browser terlihat + `watch-dashboard.html` + diff engine seperti web E2E.

---

## 8. Cara pakai sehari-hari

### Coordinator (disarankan)

```
@qa-lead
Jalankan E2E dan hunt staging ini. Kalau ada notifikasi validasi,
suruh sp-specialist lacak SP-nya. Gabungkan buktinya ke satu laporan.
```

### Mode gabungan web + mobile

```
@qa-lead
e2e all https://staging.contoh.com — sertakan video dari login sampai selesai
```

Konvensi `e2e all`:

- web menulis `pendukung/ai/triage.web.json` (ID `WEB-`), bukti di `pendukung/bukti/web/`
- mobile menulis `pendukung/ai/triage.mobile.json` (ID `MOB-`), bukti di `pendukung/bukti/mobile/`
- `@qa-lead` menggabungkan keduanya jadi satu `triage.json` dengan `report.profile = "all"`
- **satu kali** `build_report.py --root ... --verify` → **satu DOCX**
- web/mobile **tidak boleh** membuat DOCX sendiri dalam mode gabungan

### Langsung ke spesialis

```
@qa-web-engineer e2e web https://staging.contoh.com --watch — sertakan aksesibilitas
@qa-mobile-engineer e2e mobile — test APK di app.apk, rekam videonya
@bug-hunter hunt web https://staging.contoh.com/
@sp-specialist cari notifikasi: "Validasi gagal: area wajib diisi"
```

---

## 9. Struktur output & generator

Satu folder target berisi **tepat satu `.docx`** di root:

```
hasil-test-<target>/
  Laporan-<TARGET>-v<VER>-<TANGGAL>.docx   ← satu-satunya file di root
  pendukung/
    ai/triage.json                         ← source of truth
    ai/triage.web.json                     ← khusus e2e all
    ai/triage.mobile.json                  ← khusus e2e all
    ai/audit-log.jsonl
    ai/generated-cases.md
    ai/db-verification.json                ← bila menyentuh DB
    ai/sp-notif-search.json                ← bila melacak notifikasi
    bukti/web/                             ← screenshot, HAR, console
    bukti/mobile/                          ← screenshot, MP4, logcat, UI XML
    automation/                            ← spec Playwright/WDIO (opsional)
```

Generator kanonik — jangan menulis ulang per target:

```powershell
python "%USERPROFILE%\.config\opencode\skills\qa-e2e-tester\build_report.py" --root hasil-test-<target>
python "%USERPROFILE%\.config\opencode\skills\qa-e2e-tester\build_report.py" --root hasil-test-<target> --verify
```

Isi wajib DOCX: halaman judul & meta, ringkasan eksekutif, metodologi, lingkungan pengujian, temuan gabungan, risk register (tabel), daftar test case (lampiran), rekomendasi prioritas, batasan & `BLOCKED`, **Kesimpulan & Rekomendasi Akhir**, lampiran bukti.

Bila temuan belum punya `shots[].highlight`, DOCX menandai *"belum dianotasi merah"* — itu berarti temuan belum selesai. Koordinat `x,y,w,h` relatif 0–1.

---

## 10. Verifikasi & troubleshooting

### Preflight otomatis

Dari folder repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify_setup.ps1
```

Skrip ini hanya mengecek keberadaan dan versi. **Tidak pernah membaca atau menampilkan isi kredensial.**

### Masalah umum

| Gejala | Penyebab | Solusi |
|---|---|---|
| Agent/skill tidak muncul di `/api/agent` atau `/api/skill` | API dijalankan dari dalam repo, atau belum reload | Jalankan dari folder workspace, `opencode reload`, ulangi sekali |
| `ModuleNotFoundError: docx` / `PIL` / `pyodbc` | Dependensi belum terpasang | Ulangi bagian [3](#3-dependensi-python) |
| Browser gagal dibuka | Chromium belum terinstall | `python -m playwright install chromium` |
| Agent mengarang nama tool browser | Namespace berubah | Agent wajib `search` dulu; bila perlu muat skill `browser` |
| DB `BLOCKED` | Nama instance/driver/jaringan salah | Cek `server` (backslash dobel), `driver`, konektivitas ke UAT. **Jangan kirim password ke chat** |
| `driver` error walaupun server benar | Default ODBC 18 tidak terpasang | Isi `"driver": "SQL Server"` atau nama driver yang benar |
| `EXEC` ditolak | Sesuai desain | Baca definisi SP lewat `db_verify.py` kunci `sp`, bukan `EXEC` |
| AVD tidak muncul | Virtualisasi mati / SDK tidak lengkap | `emulator -accel-check`, lengkapi `platform-tools` + DLL |
| Appium membuka launcher, bukan app | `activateApp()` belum dipanggil | Tambahkan `activateApp()` di script |
| Test Mode mati sendiri | Toggle diklik dua kali | Buat toggle idempoten: `checked === 'true'` → skip |
| MuMu `unauthorized` / `offline` | Port salah / belum diizinkan | Tanya `mumu-cli info --vmindex 0`, connect ulang, klik Allow |
| Screenshot PNG rusak | PowerShell `>` dipakai untuk biner | Pakai `adb pull`, verifikasi header PNG |
| DOCX tanpa anotasi merah | `shots[].highlight` kosong | Tambahkan `highlight` + `label` pada tiap temuan |
| Dua DOCX muncul | Mode `e2e all` tapi agent buat laporan sendiri | Hapus yang duplikat; biarkan `@qa-lead` yang gabung & generate |

### Update

```powershell
cd qa-team
git pull
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
powershell -ExecutionPolicy Bypass -File .\verify_setup.ps1
```

---

## 11. Ringkasan aturan yang tidak berubah

1. Satu DOCX final per laporan, termasuk `e2e all`.
2. Bab **Kesimpulan & Rekomendasi Akhir** wajib.
3. Temuan sekecil apa pun tidak boleh lolos, termasuk typo dan tooltip salah.
4. Urutan klik/tap eksplisit + screenshot lingkaran/border merah berlabel, tertanam di DOCX.
5. Uji sungguhan, bukti sungguhan; video mobile asli tidak dihapus.
6. DB read-only; `EXEC` ditolak; DB tidak terjangkau → `BLOCKED`.
7. Bug hunt butuh otorisasi tertulis; eksploitasi destruktif dilarang; berhenti bila produksi berisiko permanen.
8. Kredensial tidak pernah di chat; tidak ada `[REDACTED]` di DOCX/artifact — nilai tersedia ditulis apa adanya, nilai tidak ada ditulis `(...)`.
9. AVD = default automation; MuMu = demo; perangkat fisik = UAT akhir; iOS/IPA = `BLOCKED`.
10. FIRERPA/lamda hanya evaluasi + pilot terbatas di lab; tidak ada klaim benchmark dan tidak menggantikan guardrail.

Detail teknis ada di `README.md`, `skills/qa-e2e-tester/SKILL.md`, dan `SKILL.md` skill domain.
