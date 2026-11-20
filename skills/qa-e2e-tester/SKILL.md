---
name: qa-e2e-tester
description: Vibe QA tester — user gives only a command and supporting docs; agent self-resolves inputs, self-recovers from tool failures, and produces ONE consolidated Word (.docx) report. Covers end-to-end (E2E) testing of web, Android and iOS apps (Playwright browser tools, ADB with MuMu/physical devices, Appium/WebdriverIO/XCTest), backend/mobile APIs (REST/JSON/HTTP), authorized pentesting and network assessment, and performance/stability testing. Trigger perintah "e2e web [url]", "e2e mobile [serial|app]", "e2e all", juga "e2e web", "e2e mobile", "jalankan E2E web/mobile", "test web <url>". Input FSD/PRD/User Guide/Test Scripts, APK/IPA, config, atau URL saja. Kredensial di-resolve otomatis dari .env.qa / qa-credentials.local.json. Test Mode DCT otomatis. Hasil satu ai/triage.json lalu satu DOCX berisi risk register, daftar test case, CVSS, dan screenshot.
---

# VIBE QA TESTER (`qa-e2e-tester`)

Skill ini mengubah satu perintah menjadi pengujian yang berjalan sendiri. User cukup memerintah (`e2e web`, `e2e mobile`, `e2e all`) dan menyediakan dokumen/APK; agent yang me-resolve target, akun, PIN/OTP, serial, package, dan test case — lalu mengeksekusi, memulihkan diri saat tool gagal, dan menghasilkan **satu** DOCX. Cakupannya **Web, Android/iOS (APK/IPA, ADB, Appium/XCTest), API, pentest mobile/web/jaringan, dan performa/stabilitas** lewat tool browser Playwright, ADB MuMu/device fisik, Appium, HTTP client, dan tool pentest yang diizinkan.

**Prinsip coverage:** uji seluas mungkin dan dokumentasikan. Setiap tombol, input, tab, validasi, endpoint, port, permission, request/response, dan permukaan jaringan yang bisa diuji harus diuji. Yang tidak bisa diuji **jangan diklaim lolos** — tandai `BLOCKED` di `ai/triage.json` dan Bab Batasan. Temuan keamanan wajib memuat lokasi eksplisit, risk score, dampak bisnis, dan rekomendasi, bukan sekadar V/X.

---

## 0.1 DISIPLIN TERPADU (2026-11-19)

Skill ini **satu file**. Semua disiplin — Intake/RoE, Mobile E2E, Web E2E, API Testing, Security Pentest, Network Assessment, Performance, dan Reporting — dijalankan dari instruksi di bawah. **Semua disiplin tetap masuk SATU laporan DOCX gabungan.**

**Keputusan pelaporan:** jangan membuat `laporan-pentest.docx`, `network-assessment.docx`, atau `performance-baseline.xlsx` terpisah. Satu file `Laporan-[TARGET]-v[VER]-[TANGGAL].docx` berisi functional + security + network + performance + risk register. Source of truth temuan: `ai/triage.json`.

> **Instalasi di laptop baru** ada di `CARA_INSTALL.md` — file pendamping yang dibaca manusia, bukan instruksi untuk agent.

### 0.2 CARA MEMERINTAHKAN — MODE `e2e`

Satu skill, tiga perintah E2E. Ketiganya **wajib** masuk satu `ai/triage.json` dan satu DOCX — bukan laporan per mode.

| Perintah | Eksekusi |
|---|---|
| `e2e web [url]` | Tool browser Playwright langsung (tanpa `npm install` dulu): auth, alur inti, negative/boundary/injection, a11y WCAG 2.2 AA, responsive, console/pageerror = 0. URL dari perintah atau dokumen — jangan mengarang. |
| `e2e mobile [serial\|app]` | ADB MuMu/device fisik: Test Mode, dump XML → tap/text, screenshot, activity, logcat. Serial/package di-auto-resolve dari `mumu-cli info` dan APK. |
| `e2e all` | Jalankan web lalu mobile, gabungkan temuan ke satu triage + satu DOCX. |

Alias yang dikenali: `e2e web`, `e2e mobile`, `jalankan E2E web/mobile`, `run mobile e2e`, `test web <url>`.

**Auto-resolve — user cukup memerintah + menyediakan dokumen pendukung.** User **tidak** perlu mengubah kode atau men-set env manual. Agent mencari sendiri:

| Input | Sumber otomatis (urutan prioritas) |
|---|---|
| `TARGET_URL` | argumen perintah → dokumen pendukung (FSD/PRD/User Guide/Test Scripts/config di workspace) → **tanya sekali** kalau tidak ada sumber |
| `QA_USER` / `QA_PASS` / `QA_TEST_MODE_PIN` / OTP test | file lokal `.env.qa` atau `qa-credentials.local.json` di workspace → jangan diminta di chat. **Semua nilai yang tersedia di artefak ditampilkan apa adanya di laporan internal**; nilai yang tidak ada ditulis `(...)` — tanpa marker `[REDACTED]` |
| serial ADB | `mumu-cli info` → `adb_port` hasil deteksi, bukan hardcode |
| package / APK | argumen → APK di workspace → `pm list packages` / `dumpsys` |
| test case & ekspektasi | dokumen pendukung → generate case otomatis |

**Gate sebelum eksekusi:** target & akun uji berhasil di-resolve; environment UAT/staging (atau ada approval tertulis); data uji bisa di-reset. Kredensial tidak diminta di chat dan tidak ditulis ke log runtime; di laporan internal ditampilkan sesuai aturan tunggal di bawah. RoE dicatat dari dokumen; kalau approval tidak ada, **tanya sekali** sebelum aksi yang mengubah state — jangan mengarang dan jangan berhenti dengan formulir panjang.

**Pelabelan hasil:** setiap case beri `PASS` / `FAIL` / `BLOCKED`. Kalau ada `BLOCKED`, **jangan** klaim "E2E penuh lolos" — tulis di Bab Batasan. Checklist testability: auth deterministik, akun uji + OTP test, data bisa di-reset, selector stabil (`resource-id`/`content-desc`/`data-testid`), network/TLS terkendali, matrix device, dan asersi UI + backend.

### Aturan kredensial — SATU versi (berlaku di seluruh skill)

Identitas, role, sumber akun, metode login, **password, PIN Test Mode, OTP, nomor HP, NIK, token, chat ID, dan Android ID ditampilkan apa adanya** di laporan internal (satu tim/perusahaan) **selama nilainya tersedia di artefak**. Kredensial tetap tidak diminta di chat dan tidak ditulis ke log runtime. Kalau nilai tidak ada, tulis `(...)`; bila alur tidak dijalankan, nyatakan status `BLOCKED`. Jangan mengarang dan jangan memakai marker `[REDACTED]`. Tidak ada aturan lain yang boleh mengubah ini.

### Loop otonom vibe tester

Jalankan tanpa menunggu instruksi per langkah:

1. **Resolve** — baca perintah + dokumen + `.env.qa`; tentukan target, akun, serial, package, test case. Kalau ada yang benar-benar tidak ada, tanya **sekali**.
2. **Execute** — jalankan mode yang diminta; tiap case diberi `PASS` / `FAIL` / `BLOCKED` dengan bukti nyata.
3. **Recover** — kalau tool/ADB/browser gagal, pakai fallback yang tercantum di skill (mis. A0 langkah 3b). Jangan berhenti hanya karena koneksi putus; coba pulihkan dulu.
4. **Triage** — tulis semua temuan ke `ai/triage.json` (satu source of truth), termasuk `BLOCKED`.
5. **Report** — hasilkan satu DOCX: ringkasan, temuan, risk register, daftar test case, batasan, bukti.
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

## 1. PRINSIP UTAMA: EXHAUSTIVE & GRANULAR TESTING (PENGUJIAN TANPA CELAH)

1. **Target Interactivity Coverage** (yang tidak bisa diuji → `BLOCKED`, bukan dilewati):
   - **Semua Tombol Wajib Diklik**: Tombol primer, sekunder, tombol ikon kecil (+, -, edit, delete, view, download, export, import, print, close, cancel, refresh, collapse, expand).
   - **Semua Input Wajib Diuji**: Textbox, password, number, date picker, range month, dropdown single/multi select, radio button, checkbox, textarea, file upload.
   - **Semua Tab & Accordion Wajib Dibuka**: Setiap sub-tab dan hidden panel wajib dicek konten dan fungsinya.
2. **Uji Validasi Form & Keamanan (Security & Injection Probe)**:
   - Blank submission (klik submit saat form kosong, periksa apakah pesan error spesifik per field).
   - Boundary limits (karakter 0, 1, max, max+1, angka minus, desimal, format email tanpa domain/tanpa `@`, nomor telepon berisi teks).
   - Anti-duplikasi / primary key bentrok.
   - Masking & regex input constraint.
   - **Automated Security/Injection Probe**: Uji otomatis input payload XSS (`<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`), SQL Injection (`' OR '1'='1`, `'; DROP TABLE--`), dan path traversal (`../../etc/passwd`) pada semua field input/search bar untuk memastikan aplikasi aman dari kerentanan input.
3. **Pengujian Tampilan, Visual Regression & UI/UX**:
   - **Visual Regression Testing (UI Diffing)**: Menyimpan snapshot baseline visual UI dan mendeteksi pergeseran layout, posisi tombol, ukuran elemen, atau font/warna yang rusak antar rilis.
   - Cek console error browser (HTTP 404 pada font, asset gambar pecah, file CSS/JS missing).
   - Tabrakan z-index / modal bertumpuk (backdrop overlay blocking).
   - Responsivitas tabel dan overflow horizontal/vertikal.
   - Konsistensi label vs placeholder vs format data.
4. **Performa & Network Latency Benchmark**:
   - **Automated API & Network Latency Benchmark**: Pantau durasi response time setiap route halaman dan request backend API (beri flag warning jika latency > 2.000 ms).
5. **Keamanan & Resiliensi Sistem (Destructive / Chaos)**:
   - Rapid multi-click / Race condition pada tombol aksi database (Save, Delete, Approve).
   - Manipulasi urutan tanggal (Date Inversion: Date To < Date From).
   - Broken session & privilege escalation (bypass role URL langsung).
6. **Data Lifecycle & Clean Teardown**:
   - **Automated Test Data Teardown/Cleanup**: Identifikasi data dummy/transaksi uji yang dibuat selama sesi testing dan lakukan automated cleanup/rollback agar database target tetap bersih.

---

## 2. DUKUNGAN INPUT PENGUJIAN (MULTI-MODE INGESTION)

Skill ini bekerja adaptif dalam **4 Skenario Input**:

| Mode | Input yang Disediakan User | Peran & Alur Kerja QA |
|---|---|---|
| **Mode 1: Script + FSD/PRD + URL** | Dokumen Spesifikasi + Test Script yang sudah ada + URL | Eksekusi script yang ada, validasi kesesuaian langkah terhadap FSD, tambah negative test case yang belum ter-cover di script, dan laporkan hasil uji. |
| **Mode 2: Spec-Driven (FSD / PRD / User Guide + URL)** | Dokumen spesifikasi + URL web live | Bedah aturan bisnis (business rules), buat test matrix lengkap (Happy & Negative), eksekusi di web, dan lakukan gap analysis (kesesuaian web vs dokumen). |
| **Mode 3: Whitebox (Source Code + URL)** | Folder project source code + URL web live | Analisis arsitektur kode, skema state/context, API endpoint, validasi form, dan eksekusi pengujian live. |
| **Mode 4: Pure Blackbox (Hanya URL Website)** | Hanya URL target (tanpa dokumen/code) | Eksplorasi UI/UX secara mandiri, identifikasi role, form, tombol, dan validasi fungsional menyeluruh. |
| **Mode 5: Mobile Binary (APK/IPA)** | File APK/IPA + akun uji + (opsional) source code | Instal di emulator/simulator/device uji, eksplorasi UI, statis + dinamis analysis, network inspection, dan pentest mobile sesuai bagian 3E. |
| **Mode 6: Network Scope** | Daftar IP/host/CIDR + izin tertulis | Mapping port/layanan, review TLS & konfigurasi, dan risk scoring jaringan sesuai bagian 3G. |

Untuk Mode 5 dan Mode 6, **guardrail bagian 0 wajib dipenuhi sebelum eksekusi**.

---

## 3. PROTOKOL EKSEKUSI MENYELURUH (WEB, ANDROID, iOS, API, & PENTEST)

### A0. Protokol Android via ADB & MuMu Emulator (Mode Terlihat / Live)
1. **Jalankan MuMu dalam mode terlihat**: buka jendela GUI MuMu Player, jangan di-minimize/headless/background saat demo. Set resolusi minimal `1080x1920`, DPI `320`, dan matikan mode silent agar setiap tap/swipe kelihatan.
2. **Aktifkan ADB & temukan port sebenarnya**: di MuMu buka *Settings → ADB* (atau `设置 → ADB`) dan pastikan ADB debugging aktif. **Jangan mengasumsikan port `7555`** — versi MuMu terbaru (mis. MuMu Player 15 / `Netease\MuMuPlayer`) memakai port lain. Tanyakan langsung ke CLI MuMu:
   ```powershell
   & "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" info --vmindex 0
   ```
   Field `adb_port` pada output JSON adalah port yang dipakai (contoh nyata: `16384`). Port lama `7555/7557/7559` hanya berlaku pada MuMu generasi lama. Alternatif lain: `netstat -ano | findstr LISTENING`.
3. **Hubungkan** (pakai `adb.exe` bawaan MuMu agar versi client/server cocok):
   ```powershell
   $adb = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
   & $adb kill-server
   & $adb start-server
   & $adb connect 127.0.0.1:16384
   & $adb devices
   ```
   Status harus `device`. Jika `unauthorized`, klik **Allow** di jendela MuMu. Jika `offline`, ulangi `& $adb disconnect 127.0.0.1:16384` lalu connect lagi. Ganti `16384` dengan `adb_port` dari langkah 2.

   3b. **Fallback saat ADB offline setelah airplane mode / proxy mati.** Jangan langsung menyerah dan jangan klaim skenario offline lolos. Matikan airplane mode lewat MuMu CLI, reset proxy, lalu reconnect:
    ```powershell
    $mumu = "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe"
    & $mumu sh --vmindex 0 --cmd "settings put global airplane_mode_on 0"
    & $mumu sh --vmindex 0 --cmd "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false"
    & $mumu sh --vmindex 0 --cmd "settings put global http_proxy :0"
    & $adb disconnect 127.0.0.1:16384
    & $adb connect 127.0.0.1:16384
    & $adb devices
    ```
    Setelah pulih, lanjut dump/screenshot. Kalau state tidak bisa dikembalikan, tandai `BLOCKED` dan catat di Bab Batasan.
4. **Pasang/verifikasi app**:
   ```powershell
   adb install -r app.apk
   adb shell pm list packages | findstr <nama-package>
   ```
5. **Eksekusi otomatis yang kelihatan**:
   - Pakai Appium `UiAutomator2` dengan `appPackage`/`appActivity` atau path `app`, `noReset: false`, `newCommandTimeout: 120`. Biarkan `appium` dan jendela MuMu tetap foreground saat demo.
   - Alternatif smoke test cepat: `adb shell input tap <x> <y>`, `adb shell input swipe ...`, `adb shell input text ...` — semua aksi langsung terlihat di layar MuMu.
   - Catatan: MuMu adalah emulator Android; skenario iOS tetap memakai simulator Xcode/device asli (bagian 3D).
6. **Rekam bukti**:
   ```powershell
   $adb = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
   $serial = "127.0.0.1:16384"
   & $adb -s $serial shell screenrecord --time-limit 30 /sdcard/test.mp4
   & $adb -s $serial pull /sdcard/test.mp4 hasil-test/evidence/android/<skenario>.mp4
   # PENTING: jangan pakai `>` PowerShell untuk PNG (merusak biner).
   & $adb -s $serial shell screencap -p /sdcard/shot.png
   & $adb -s $serial pull /sdcard/shot.png hasil-test/evidence/android/<id>.png
   & $adb -s $serial logcat -v time > hasil-test/evidence/android/logcat.txt
   ```
   Verifikasi PNG dengan `python -c "print(open(p,'rb').read(8))"` — harus `\x89PNG\r\n\x1a\n`.
   Boleh juga pakai fitur screen recorder bawaan MuMu.
7. **Multi-instance**: ulangi `adb connect 127.0.0.1:<port>` untuk tiap instance, lalu bedakan `udid` dan `systemPort` di capabilities Appium.
8. **Caveat**: jika aplikasi butuh Google Mobile Services/ARM khusus, pastikan versi MuMu yang dipakai mendukungnya; kalau tidak, gunakan perangkat fisik atau emulator lain.

### A0.1. Resep Appium + WebdriverIO yang TERVERIFIKASI (Android/MuMu)
Gunakan ini jika butuh script `.spec.ts` yang benar-benar jalan, bukan sekadar contoh.
Stack terverifikasi: **Appium 4.0.0**, driver **uiautomator2@9.2.2**, **JDK 21**, **Node 20+**, **WebdriverIO 10.x**.
Hasil nyata: `1 passing` — Test Mode → login dari env → Home 4 tab.

1. **Siapkan env & server** (sesuaikan path mesin):
   ```powershell
   $env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
   $env:ANDROID_HOME="$env:LOCALAPPDATA\android-sdk-minimal"
   $env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
   $env:PATH="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
   appium server --port 4723 --base-path /wd/hub
   ```
   SDK minimal cukup berisi `platform-tools\adb.exe` + `AdbWinApi.dll` + `AdbWinUsbApi.dll`
   (salinkan ketiganya dari folder `nx_main` MuMu; tanpa DLL itu Appium tidak melihat device).
2. **Buat spec WDIO** di folder output (`automation/wdio.conf.ts`, `android.spec.ts`, `package.json`), lalu `npm install`.
3. **Jalankan** (baca kredensial dari `.env.qa` / `qa-credentials.local.json`, jangan minta di chat; tampilkan di DOCX sesuai aturan §0.2):
   ```powershell
   $env:QA_NIK='NIK_UJI'
   $env:QA_PASS='password_uji'
   $env:QA_UDID='127.0.0.1:16384'
   npx wdio run wdio.conf.ts
   ```
4. **Jebakan yang sudah diatasi di template** — jangan dihapus:
   - `activateApp()` wajib; tanpa itu Appium bisa membuka home launcher MuMu, bukan aplikasi.
   - Dialog izin/notifikasi bisa muncul **dua kali** (awal & setelah login); loop `tanganiDialogSistem()` sebelum dan sesudah login.
   - Toggle Test Mode harus **idempoten** (`checked === 'true'` → skip). Klik kedua akan mematikan Test Mode.
   - Field PIN dialog dan password login punya `resource-id` sama; **scope ke dialog** dengan XPath atau strict mode WebdriverIO error.
   - Verifikasi NIK terbaca (`getText() === NIK`) sebelum klik login — Menangkap input yang salah tempat.
5. **Bukti**: `saveScreenshot()` dari session WDIO lebih disukai daripada `adb screencap` saat demo, karena screenshot diambil pada momen asersi.

### A. Protokol Khusus Aplikasi Mobile DCT (Asset, Cargo, CDC, FLM, dll):
- **Wajib Masuk ke Test Mode Terlebih Dahulu Sebelum Melakukan Login/Testing**:
  1. Pada halaman login awal aplikasi mobile DCT, klik ikon **titik 3** (di pojok kanan atas).
  2. Klik toggle/switch **Test Mode**.
  3. Masukkan PIN Test Mode (dari env/local file, mis. `QA_TEST_MODE_PIN`) lalu klik **Submit**.
  4. Tekan tombol **Back** untuk kembali ke halaman login.
  5. Pastikan aplikasi berada dalam mode testing sebelum memasukkan kredensial login atau mengeksekusi skenario uji.

### B. Protokol Pengujian API Mobile & Backend (REST/JSON/HTTP):
1. **Ekstraksi Endpoint API**:
   - Analisis bytecode/decompiled DEX APK atau network inspection untuk mengambil Base URL, HTTP Method (GET/POST/PUT/DELETE), path route, query params, headers (misal: `Android-ID`, `Authorization`, `Content-Type`), dan payload schema.
2. **Validasi Request & Response Payload**:
   - Uji Happy Path: Verifikasi status code `200 OK` / `201 Created`, struktur JSON response, dan keakuratan data yang disimpan ke database.
   - Uji Negative & Boundary: Blank payload, invalid data type, missing required fields, boundary values -> pastikan response status `400 Bad Request` / `422 Unprocessable Entity` dengan error message yang informatif.
   - Uji Auth & Security: Request tanpa header token/auth (`401 Unauthorized`), request cross-role/privilege (`403 Forbidden`), SQL Injection & XSS payload injection probe pada field JSON.
3. **Network Latency & Performance Benchmark**:
   - Pantau response time API (flag jika latency > 2.000 ms).
   - Validasi error handling saat timeout / backend offline (tidak boleh return raw 500 stack trace ke client).

### C. Protokol Web & Tool Browser Playwright:
Saat menguji web, pakai tool browser yang tersedia di sesi (lewat Code Mode `tools.playwright.*`, mis. `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_evaluate`, `browser_take_screenshot`, `browser_console_messages`). **Cek katalog tool di sesi** dan gunakan nama yang benar-benar ada — jangan mengarang signature. Tidak perlu `npm install` untuk eksekusi ad-hoc; CLI tetap dipakai kalau user minta suite reproducible.

1. **Inisialisasi & Reset State**: buka `TARGET_URL`, lalu `localStorage.clear()` lewat `browser_evaluate` dan reload.
2. **Snapshot & Element Discovery**: `browser_snapshot` / `browser_evaluate` untuk memindai tombol (`button`, `a`, `input[type=button|submit]`) dan semua input form.
3. **Eksekusi bertahap** — Happy Path → Negative → Chaos/Edge Case, satu per satu tanpa melewatkan elemen.
4. **Screenshot wajib** pada tiap temuan: `browser_take_screenshot` segera saat error/anomali/state ditemukan, simpan ke `pendukung/bukti/<bug-id>.png`.
5. **Console & network**: `browser_console_messages` untuk 404/500/JS exception; catat request/response API yang relevan.
6. **Bukti keputusan**: jangan klaim "membaca screenshot". Dasarkan asersi pada snapshot aksesibilitas, teks DOM, console, dan response JSON.

### D. Protokol Otomasi iOS (Appium / XCUITest)
1. **Prasyarat**: macOS + Xcode (untuk simulator) atau real device dengan provisioning; Appium 4.x dengan driver `XCUITest`, atau XCTest/XCUITest native.
2. **Capabilities minimal**:
   ```json
   {
     "platformName": "iOS",
     "appium:automationName": "XCUITest",
     "appium:deviceName": "iPhone 15 Simulator",
     "appium:app": "/path/to/App.app",
     "appium:udid": "<simulator-or-device-udid>",
     "appium:noReset": false
   }
   ```
3. **Reset state**: uninstall/reinstall aplikasi, lalu reset permission dengan `xcrun simctl privacy <udid> reset all` (simulator) sebelum tiap skenario.
4. **Coverage wajib**: onboarding, login/logout, Face ID/Touch ID & fallback PIN, izin notifikasi/kamera/lokasi, deep link/universal link, foreground-background-foreground, keyboard & autocorrect, safe area/notch, dark mode, orientasi, dan lokalifikasi.
5. **Bukti**: screenshot per langkah ke `hasil-test/evidence/ios/`, log `xcrun simctl spawn booted log stream` atau Appium log ke `hasil-test/evidence/ios/device.log`.
6. **Script hasil**: `hasil-test/tests/ios/<app>.spec.ts` (Appium + WebdriverIO) atau `<App>UITests.swift` untuk XCUITest.
7. **Script iOS dibuat saat eksekusi.** **Jangan klaim tervalidasi** sebelum dijalankan di macOS + Xcode — mesin referensi Windows hanya bisa menyiapkan script, bukan membuktikan eksekusinya.

### E. Protokol Pentest Mobile (Android & iOS)
**Prasyarat: izin tertulis sesuai bagian 0.** Gunakan akun uji, bukan akun produksi.

1. **Static analysis**:
   - Android: dekompilasi APK dengan `apktool`/`jadx`; cek `AndroidManifest.xml` (exported activity/service/receiver/provider, intent-filter, permission), hardcoded secret/API key, certificate pinning, root detection, WebView JS bridge, `allowBackup`.
   - iOS: unpack IPA; cek `Info.plist` (`NSAppTransportSecurity`, `NSAppTransportSecurity` exceptions, URL scheme, `UIFileSharingEnabled`), hardcoded secret, jailbreak detection, Keychain/UserDefaults usage, ATS & certificate pinning.
   - Petakan temuan ke kategori **OWASP MASVS**: storage, crypto, auth, network, platform interaction, code quality, resiliency.
2. **Dynamic analysis**:
   - Storage: SharedPreferences/SQLite/Realm (Android), Keychain/UserDefaults/plist (iOS), Logcat/`log stream`, clipboard, screenshot task-switcher.
   - Network: intercept traffic via proxy hanya dengan consent; uji validasi TLS, certificate pinning, dan fallback HTTP plaintext.
   - Logic: deep link hijack, biometric bypass flow, role/parameter tampering pada request API, WebView bridge abuse.
3. **Output**: setiap temuan masuk `triage.json` dengan lokasi (komponen/field/file), risk score, dan bukti (`security/mobile/*.png|log`).

### F. Protokol Pentest Web (AI-Assisted)
**Prasyarat: scope URL tertulis sesuai bagian 0.**

1. **Recon ringan**: daftar endpoint dari crawling/sitemap, parameter, form, cookie, header respons.
2. **Probe deteksi-safe** (jangan destruktif):
   - Auth/session: akses tanpa token (`401`), cross-role dengan akun uji (`403`), session fixation, logout tidak invalidate token.
   - Injection probe: XSS/SQLi/path traversal/command-like payload non-destruktif pada semua input (lihat bagian 1.2).
   - CSRF token, CORS misconfiguration, security header (CSP, HSTS, X-Frame-Options, X-Content-Type-Options), cookie flag (`HttpOnly`, `Secure`, `SameSite`).
   - File upload (type/size/execution), directory listing, verbose error/stack trace, open redirect.
3. **Tooling**: tool browser Playwright untuk probe UI, `curl`/HTTP client untuk header, OWASP ZAP baseline/active scan **hanya pada scope yang disetujui**.
4. **AI triage**: agent mengelompokkan duplikat, membuang false positive, memberi confidence level, dan menyusun remedasi. Temuan HIGH/CRITICAL wajib divalidasi manual.

### G. Protokol Pentest Jaringan (Authorized Only)
**Prasyarat: daftar IP/host/CIDR + izin tertulis sesuai bagian 0.**

1. **Passive/light recon**: DNS, identifikasi host hidup, banner/service version.
2. **Port & service mapping**: `nmap -sV --top-ports 1000 <scope>` (full port hanya jika disetujui); catat port/admin panel yang terekspos.
3. **TLS review**: versi & cipher (mis. `testssl.sh`/`sslyze`), expired/self-signed cert, HTTP→HTTPS redirect, HSTS.
4. **Konfigurasi**: firewall/ACL, SSH/Telnet/SNMP exposed, default credential **hanya di lab milik sendiri**, jangan brute-force produksi.
5. **Dilarang**: exploit aktif, DoS, pivot ke host di luar scope, atau password spraying tanpa approval tertulis.
6. **Output**: inventory `host:port:service` + risk score per host di `security/network/`.

### H. Lapisan Orkestrasi AI (Wajib untuk Challenge AI Engineer)
Gunakan LLM/agent sebagai **koordinator**, bukan pengganti bukti:

1. **Generate**: buat test matrix (happy/negative/chaos) dari FSD/PRD/user guide; untuk blackbox, generate hypotesis dari UI yang ditemukan.
2. **Execute assist**: sarankan langkah berikutnya, parameter boundary, dan payload probe yang aman sesuai bagian 0.
3. **Triage**: deduplikasi temuan, klasifikasi Functional Bug vs Security Risk vs Network Risk, hitung `Risk = Likelihood × Impact`, beri `confidence`.
4. **Explain**: terjemahkan temuan teknis ke dampak bisnis dan rekomendasi prioritas (short/medium/long term).
5. **Report**: susun ringkasan eksekutif + heatmap + top risks otomatis ke docx/markdown.
6. **Aturan emas**: AI **tidak boleh mengarang bukti**. Setiap risk harus punya path screenshot/log/request-response yang nyata dan entri di `ai/triage.json`.

---

## 4. STANDAR FORMAT TEMUAN BUG & ATRIBUT DEFECT REPORTING

Setiap bug/defect diklasifikasikan dengan tingkat keparahan (*Severity*):

- 🔴 **HIGH / CRITICAL**: Error sistem, crash backend 500, SQLi/XSS vulnerability, data loss, RBAC bypass, secret terekspos, atau layanan jaringan kritis terekspos publik.
- 🟡 **MEDIUM**: Validasi form lolos data invalid, duplikasi record, logic error (date inversion), multi-modal overlay crash, TLS/cookie/header misconfiguration, unhandled yellow screen.
- 🟢 **LOW / UX**: Link/tombol mati, asset font/gambar 404, typo teks, label misleading, kepadatan indikator mandatory.

**Risk scoring (wajib untuk temuan keamanan & pentest):**
- `Likelihood` 1-5 (1 = sulit dieksploitasi, 5 = sangat mudah) × `Impact` 1-5 (1 = minor, 5 = kritis) → `Risk = L × I` (rentang 1-25).
- Mapping: **20-25 = Critical**, **12-19 = High**, **6-11 = Medium**, **1-5 = Low**. Boleh ditambah CVSS v3.1 base score bila tersedia.
- Setiap risk wajib punya **lokasi eksplisit**: endpoint/URL, `host:port`, file kode, komponen APK/IPA, atau layar/elemen.
- `AI Confidence`: `high` / `medium` / `low`. Temuan Critical/High wajib divalidasi manual sebelum ditutup.

### Aturan bukti temuan — temuan sekecil apa pun tidak boleh lolos dari report
**Semua temuan wajib masuk report. Tidak ada yang boleh dibuang, difilter, atau dianggap terlalu sepele untuk ditulis.** Setiap anomali yang teramati selama pengujian harus tercatat sebagai `finding` di `ai/triage.json` dan tampil di DOCX — INFO/LOW/cosmetic/typo/warna/satu tombol/teks meleset tetap wajib lengkap. Untuk **setiap** temuan:

1. **Proses kejadian (reproduksi) eksplisit** — tulis urutan aksi nyata: klik/tap tombol mana,
   isi field apa, scroll ke mana, URL/layar/elemen, dan hasil yang terlihat. Jangan hanya
   menulis "tombol tidak jalan". Contoh: `1. Buka /login; 2. Klik ikon titik-tiga kanan atas;
   3. Ketik PIN di field Password; 4. Klik SUBMIT; 5. Amati IS_SERVER berubah menjadi false.`
2. **Screenshot asli + anotasi merah** — ambil screenshot saat asersi, lalu **lingkari** (default)
   atau **kotakkan merah** area temuan. Simpan file aslinya di `pendukung/bukti/screenshots/`,
   lalu cantumkan anotasinya di `triage.json`:
   ```json
   "shots": [{
     "ref": "pendukung/bukti/screenshots/01_login.png",
     "highlight": {"type": "circle", "x": 0.62, "y": 0.31, "w": 0.18, "h": 0.12},
     "label": "Pesan error di sini"
   }]
   ```
   `x,y,w,h` relatif 0–1 terhadap ukuran gambar (nilai >1 dibaca piksel).
   `type: "box"` untuk kotak; alternatif lingkaran: `{"type":"circle","cx":...,"cy":...,"r":...}`.
3. **Tertanam di DOCX** — generator menyisipkan gambar yang sudah dilingkari merah **tepat di bawah
   temuan yang bersangkutan**. Jika `highlight` kosong, DOCX menandai *"belum dianotasi merah"*
   dan temuan dianggap belum selesai.

Format detail bug wajib memakai template ini:
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

1. **Koneksi dari file kredensial lokal** — prioritas: `QA_CREDENTIALS_FILE` →
   `%USERPROFILE%\.config\opencode\qa-credentials.local.json` → `qa-credentials.local.json` di folder skill.
   Repo menyimpan **`qa-credentials.example.json`** (template kosong, aman di-commit). Setelah clone:
   `copy qa-credentials.example.json qa-credentials.local.json`, lalu isi file `.local.json` —
   nama itu sudah masuk `.gitignore`, jadi password tidak bisa ikut ter-commit. Blok `db` berisi
   `sqlite` / `server` / `database` / `user` / `password` / `auth` / `driver` / `limit`.
   Environment variable (`QA_DB_SQLITE`, `QA_DB_SERVER`, `QA_DB_NAME`, `QA_DB_USER`, `QA_DB_PASS`,
   `QA_DB_AUTH`, ...) tetap lebih prioritas. Kredensial **tidak pernah** ditulis di chat/spec/DOCX.
2. **Jalankan** `python db_verify.py --checks <file-json> --out pendukung/ai/db-verification.json`.
   File checks berisi daftar asersi `SELECT` — lihat docstring di `db_verify.py`.
3. **Read-only keras** — hanya `SELECT` / `WITH` / `PRAGMA`, satu statement per check.
   `db_verify.py` menolak `INSERT`/`UPDATE`/`DELETE`/`DROP` dan multi-statement. Dilarang mengubah data.
4. **Tambahkan bab ke DOCX** — masukkan `"db_verification"` ke `report.chapters` di `triage.json`.
   Generator menyisipkan ringkasan koneksi, tabel query–status, dan baris hasil query.
5. **Aturan temuan tetap berlaku** — bila asersi `FAIL`/`ERROR`, buat temuan dengan langkah reproduksi
   + screenshot lingkaran merah. Bila database tidak terjangkau → `BLOCKED`, jangan diklaim lolos.
6. **Gunakan akun read-only dan staging/UAT dulu.** Data pelanggan yang tampil di hasil query tunduk
   pada aturan pelaporan di bawah — jangan disertakan mentah di laporan yang dibagikan.
7. **Stored procedure — baca definisi, jangan eksekusi.** Untuk SQL Server pakai kunci `sp`:
   - Nama exact: `{"sp":"dbo.ValidateProblem","expect":{"column":"definisi","contains_all":["IF @area","RAISERROR"]}}`
   - Banyak SP: `{"sp":"Valid*","limit":10,"offset":0}` — `*` adalah wildcard nama; `offset`/`limit`
     melakukan paging. Hasil menyimpan `total_matching` supaya jelas ada berapa SP yang cocok.
   - Cari dari pesan notifikasi: `{"sp":"*","definition_contains":"area wajib diisi"}` atau
     `{"sp":"*","definition_all":["IF @status","RAISERROR"]}` — ini melacak notifikasi validasi ke
     prosedur pengirimnya tanpa menjalankan prosedur.
   `db_verify.py` menerjemahkan semuanya menjadi `SELECT` ke `sys.sql_modules`/`sys.objects` dengan
   parameter binding. **`EXEC` tidak didukung** — isi prosedur bisa mengubah data. SQLite tidak punya
   SP; check `sp` di SQLite gagal dengan pesan yang jelas.
8. **Lacak notifikasi → SP tanpa mengisi kredensial.** Bila yang ada hanya teks notifikasi, jalankan
   `python find_notif.py --text "Validasi gagal: area wajib diisi"`. Skrip mencari targetnya sendiri:
   file kredensial → connection string di `appsettings*.json` / `web.config` / `.env` /
   `docker-compose*.yml` di sekitar workspace → instance lokal. Windows Integrated Auth dipakai bila
   tidak ada password, jadi **tidak perlu mengisi kredensial**. Hanya nama server/database yang
   diekstrak dari config — password tidak pernah dibaca, disimpan, atau ditampilkan. Output
   `pendukung/ai/sp-notif-search.json` berisi `database.schema.prosedur` dan baris definisi yang cocok.
   Tetap `SELECT` katalog, tanpa `EXEC`. Bila tidak ada target yang terjangkau → `BLOCKED`, bukan
   ditebak; yang diminta adalah nama instance/akses jaringan, **bukan password**.

### 4.1 Skema `triage.json` (inline — tanpa redaction)

Jangan menyensor nilai di artifact maupun di DOCX. Terapkan aturan tunggal:
- Semua nilai yang tersedia di artefak → ditulis apa adanya di `triage.json` dan laporan.
- Nilai yang tidak ada → tulis `(...)`, bukan `[REDACTED]`.
- Kredensial tidak diminta di chat dan tidak ditulis ke log runtime (aturan §0.2).
- Verifikasi akhir memastikan tidak ada marker `[REDACTED]` di DOCX maupun `pendukung/ai/*`.

Field minimal tiap entri `ai/triage.json`: `id`, `title`, `category` (`Functional Bug` / `Security Risk` / `Network Risk`), `severity`, `location`, `likelihood`, `impact`, `risk_score`, `cvss` (opsional), `actual`, `expected`, `business_impact`, `recommendation`, `evidence[]` (path nyata), `confidence`, `chain`, `status` (`PASS` / `FAIL` / `BLOCKED`).

---

## 5. GENERASI ARTIFAK OUTPUT PENGUJIAN

Di akhir pengujian hasilkan **satu folder target** berisi **tepat satu `.docx`** di root dan satu folder `pendukung/`. Jangan membuat laporan per disiplin, `risk-register.xlsx`, atau `<NAMA>_RISK_REPORT.docx` terpisah — semuanya disisipkan ke DOCX.

```
hasil-test-<target>/
  Laporan-<TARGET>-v<VER>-<TANGGAL>.docx   ← satu-satunya file di root
  pendukung/
    ai/triage.json          ← source of truth temuan
    ai/audit-log.jsonl      ← jejak eksekusi
    ai/generated-cases.md   ← daftar test case (juga disisipkan di DOCX)
    bukti/                  ← screenshot, video, dump XML, logcat, request/response
    automation/             ← spec Playwright/WDIO (opsional)
    build_final_report.py / verify_final.py  ← generator + verifier (opsional)
```

Isi wajib DOCX: halaman judul & meta (target, tanggal, scope, status QA), ringkasan eksekutif + metrik, metodologi, lingkungan pengujian (**termasuk akun uji sesuai aturan §0.2**), temuan gabungan (lokasi, `L × I`, CVSS, dampak bisnis, rekomendasi, bukti), hasil functional/web/mobile/API/security/network/performance, **risk register sebagai tabel**, **daftar test case sebagai lampiran**, rekomendasi prioritas, batasan & status `BLOCKED`, **bab Kesimpulan & Rekomendasi Akhir** (status akhir, rekomendasi rilis, distribusi temuan, simpulan utama, dan catatan tambahan dari `conclusion` di triage), lampiran bukti. DOCX hanya mencatat hasil uji — **jangan sisipkan catatan pengembangan skill, status tool, atau referensi `SKILL.md`**.

Generator: `python-docx` untuk teks/tabel/gambar. `openpyxl` **hanya dipakai kalau user eksplisit meminta pengisian Excel terpisah** (default tidak). Verifikasi akhir: struktur bab lengkap, satu `.docx`, tidak ada marker `[REDACTED]`, dan seluruh nilai tersedia tampil sesuai aturan §0.2.

### 5.1 Generator kanonik — satu untuk semua target

Jangan menulis ulang script DOCX per target. Pakai generator di folder skill:

```bash
python <folder skill>/build_report.py --root hasil-test-<target>
python <folder skill>/build_report.py --root hasil-test-<target> --verify
```

- `report_kit.py` berisi styling, tabel, gambar tertanam, parser `generated-cases.md`, inventaris bukti, dan verifier. Kit ini buta terhadap web/mobile/API dan tidak melakukan redaction.
- Target menentukan isi lewat blok `report` di `ai/triage.json`: `profile` (`web`/`mobile`/`api`/`all`), `output`, `header`/`title`/`subtitle`, `chapters`, dan blok tambahan (`table`, `paragraph`, `bullets`, `heading`, `image`, `flow_table`, `perf_table`, `page_break`).
- Alur eksplorasi tiap aplikasi tetap berbeda; yang distandardisasi hanya kulit laporan. Bab disusun dari `report.chapters`, sehingga target baru tidak memerlukan script baru.
- `--profile` mengoverride profil; `--output` hanya untuk staging saat file asli terkunci (misalnya masih dibuka Word). Setelah file ditutup, salin hasil staging ke nama final dan jalankan ulang `--verify`.

---

## 6. TEMPLATE GENERATOR DOKUMEN WORD (.docx) BERGAMBAR

Gunakan Python (`python-docx`) untuk menyusun dokumen Word dengan gambar tertanam:

```python
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Iterasi setiap bug dan embed gambarnya
for bug in bugs:
    p = doc.add_paragraph()
    r = p.add_run(f"[{bug['severity']}] {bug['id']}: {bug['title']}\n")
    r.font.bold = True
    p.add_run(f"• Lokasi: {bug['location']}\n")
    p.add_run(f"• Deskripsi Masalah: {bug['desc']}\n")
    p.add_run(f"• Rekomendasi Solusi: {bug['recommendation']}\n")
    
    if os.path.exists(bug['img_path']):
        doc.add_picture(bug['img_path'], width=Inches(5.5))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = cap.add_run(f"Gambar Bukti: {bug['id']} - {bug['title']}")
        r_cap.font.size = Pt(8.5)
        r_cap.font.italic = True

doc.save(f"hasil-test-<target>/Laporan-<TARGET>-v<VER>-<TANGGAL>.docx")
```

Contoh ringkas menyisipkan risk register ke DOCX yang sama (bukan file terpisah):

```python
from docx.shared import RGBColor

t = doc.add_table(rows=1, cols=5)
for i, h in enumerate(['ID', 'Lokasi', 'Risk Score', 'Severity', 'Bukti']):
    t.rows[0].cells[i].text = h
for risk in triage:
    row = t.add_row().cells
    score = risk['likelihood'] * risk['impact']
    for i, v in enumerate([risk['id'], risk['location'], score,
                           risk['severity'], risk['evidence']]):
        row[i].text = str(v)
    if score >= 12:
        row[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xB0, 0, 0)
```

---

## 7. RIWAYAT PERUBAHAN

Riwayat lengkap ada di `git log` repository. Ringkasan terbaru:

- **Menjadi vibe tester**: loop otonom `resolve → execute → recover → triage → report → stop`.
- Fallback ADB offline (airplane mode) tertanam langsung di A0 langkah 3b.
- Aturan kredensial disatukan jadi satu versi; kontradiksi dihapus.
- Output dipaksa satu DOCX; risk register & daftar test case disisipkan, bukan file terpisah.
- Nama tool browser Playwright disesuaikan dengan tool Code Mode.
- Redaction + skema `triage.json` tersedia inline (tidak bergantung helper yang dihapus).
- File inti: `SKILL.md` (instruksi agent), `CARA_INSTALL.md` (panduan manusia), `report_kit.py` + `build_report.py` (generator kanonik).
- Auto-resolve input dari perintah + dokumen pendukung; user tidak perlu set env.
- Routing perintah `e2e web` / `e2e mobile` / `e2e all`.
- Modul terpadu quality/security/network/performance dalam satu laporan DOCX.
- Generator DOCX kanonik: satu `report_kit.py` + `build_report.py` untuk semua target; bab diambil dari blok `report` di `triage.json`, bukan script per target.
- Mode 4 (pure blackbox web) terbukti di Wisesa; alur eksplorasi tiap target tetap beda, yang distandardisasi hanya kulit laporan.
- Regresi DCT + Wisesa: isi bab berbeda, format identik, verifier `CLEAN`.
