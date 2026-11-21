---
name: qa-mobile-e2e
description: Protokol eksekusi QA E2E khusus Android mobile — AVD resmi sebagai default automasi, MuMu untuk demo visual lama, perangkat fisik untuk UAT, Test Mode DCT, Appium/UiAutomator2, ADB, video bukti asli, logcat, dan pentest mobile. Harus dipasangkan dengan core qa-e2e-tester. iOS/IPA BLOCKED. Trigger: e2e mobile, test apk, jalankan E2E mobile.
---

# Mobile QA — protokol eksekusi (`qa-mobile-e2e`)

**Muat dulu skill `qa-e2e-tester` (CORE).** Skill ini hanya menambah cara eksekusi di perangkat Android. Aturan inti — intake, kredensial, guardrail, format temuan, anotasi merah, satu DOCX, Bab Kesimpulan — tetap mengikuti CORE dan **menang** bila bertentangan.

Target: APK / aplikasi Android yang sudah terpasang. Serial dan package di-resolve sungguhan, jangan hardcode. **iOS / IPA `BLOCKED`** — butuh macOS + Xcode; nyatakan jelas, jangan dipaksa, jangan klaim tervalidasi.

## Ringkasan 1 menit

| | |
|---|---|
| **Peran** | Cara eksekusi di Android — aturan pelaporan tetap milik CORE |
| **Target default** | AVD resmi Android Studio (automation); MuMu hanya demo; fisik untuk UAT |
| **Output** | `triage.mobile.json` (ID `MOB-`), **video MP4 asli**, screenshot, logcat, dump XML |
| **Batasan** | Test Mode DCT dulu untuk aplikasi DCT; video login→selesai tidak dihapus; iOS `BLOCKED` |

**Peta isi:** 1. Lingkungan Android — 2. Pasang & siapkan app — 3. Eksekusi terlihat — 4. Coverage khusus mobile — 5. Bukti & video — 6. Pelaporan & batasan

---

## 1. Pilih lingkungan Android

Prioritas berikut dipakai untuk menentukan target eksekusi:

| Prioritas | Lingkungan | Dipakai untuk | Catatan |
|---|---|---|---|
| 1 | **AVD resmi Android Studio** | **Automation & regression — default** | Gratis, ADB `emulator-5554`, CLI/headless, snapshot, `-wipe-data`. Butuh VT-x/AMD-V + WHPX/HAEVM di Windows |
| 2 | **MuMu Player** | Demo visual & bukti video lama | Emulator gaming; port ADB non-standar dan bisa putus. Bukan target CI/regresi deterministik |
| 3 | **Perangkat fisik** | UAT akhir | Paling faithful untuk GMS, push, sensor, biometrik, kamera |
| — | Genymotion Desktop | Tidak dipakai untuk automation | Vendor sendiri menyatakan "not suitable for automated testing"; SaaS/PaaS bisa dievaluasi dengan approval |

Simpan keputusan ini di Bab Lingkungan laporan. Kalau yang dipakai MuMu, nyatakan sebagai lingkungan demo, bukan fondasi CI.

### 1.1 AVD — jalur default

```powershell
emulator -accel-check                     # wajib: hypervisor aktif
emulator -list-avds
emulator -avd Pixel8_API_34 -no-boot-anim # tambah -no-window untuk CI
adb devices                               # harus ada emulator-5554
```

- Profil disarankan: **Pixel**, API 34/35, `x86_64`, variant `google_apis` (atau `google_play` bila aplikasi bergantung Play Store/FCM).
- Isolasi test: `-wipe-data` untuk kondisi awal; snapshot untuk boot cepat. Jangan pakai snapshot kotor untuk asersi penting.
- Untuk parallel: bedakan `udid` dan `appium:systemPort` (mis. 8200, 8201).

### 1.2 MuMu — jalur demo

1. Buka jendela GUI MuMu, **terlihat**, resolusi minimal `1080x1920`, DPI `320`. Jangan headless saat demo.
2. Aktifkan ADB debugging. **Jangan asumsikan port 7555** — tanya CLI:
   ```powershell
   & "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" info --vmindex 0
   ```
   Pakai field `adb_port` dari output JSON (contoh nyata: `16384`).
3. Hubungkan dengan `adb.exe` bawaan MuMu agar versi client/server cocok:
   ```powershell
   $adb = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
   & $adb kill-server
   & $adb start-server
   & $adb connect 127.0.0.1:<adb_port>
   & $adb devices
   ```
   `unauthorized` → klik Allow. `offline` → disconnect lalu connect ulang.
4. **Fallback ADB offline** (setelah airplane mode/proxy mati): matikan airplane mode lewat `mumu-cli sh --cmd "settings put global airplane_mode_on 0"`, broadcast `AIRPLANE_MODE state false`, reset proxy `settings put global http_proxy :0`, lalu reconnect. Kalau tidak pulih → `BLOCKED`, jangan klaim skenario offline lolos.
5. Caveat: GMS/ARM khusus bisa tidak didukung → pindah ke perangkat fisik, tandai `BLOCKED` bila tidak tersedia.

---

## 2. Pasang & siapkan aplikasi

```powershell
adb install -r app.apk
adb shell pm list packages | findstr <nama-package>
adb shell dumpsys activity activities | findstr mResumedActivity
```

Catat `appPackage` dan `appActivity` hasil deteksi, bukan tebakan.

### 2.1 Test Mode DCT — wajib lebih dulu

Untuk aplikasi DCT (Asset, Cargo, CDC, FLM, dll):

1. Di halaman login, klik ikon **titik 3** di pojok kanan atas.
2. Klik toggle/switch **Test Mode**.
3. Masukkan PIN Test Mode dari env/local file (`QA_TEST_MODE_PIN`) lalu klik **Submit**.
4. Tekan **Back** kembali ke halaman login.
5. Pastikan mode testing aktif sebelum memasukkan kredensial login atau menjalankan skenario.

Kredensial/NIK/PIN dari `qa-credentials.local.json` / environment. **Jangan minta di chat**, jangan tulis ke spec, log, atau DOCX. Tampilkan apa adanya di laporan internal sesuai aturan CORE; nilai tidak ada → `(...)`.

---

## 3. Eksekusi otomatis yang terlihat

### 3.1 Appium + WebdriverIO — resep terverifikasi

Stack terverifikasi: **Appium 4.0.0**, `uiautomator2@9.2.2`, **JDK 21**, **Node 20+**, **WebdriverIO 10.x**. Hasil nyata sebelumnya: `1 passing` (Test Mode → login → Home 4 tab).

```powershell
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
$env:ANDROID_HOME="$env:LOCALAPPDATA\android-sdk-minimal"
$env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
$env:PATH="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
appium server --port 4723 --base-path /wd/hub
```

SDK minimal cukup berisi `platform-tools\adb.exe` + `AdbWinApi.dll` + `AdbWinUsbApi.dll` (salinkan dari folder `nx_main` MuMu bila perlu; tanpa DLL itu Appium tidak melihat device).

Capabilities inti: `platformName: Android`, `appium:automationName: UiAutomator2`, `appium:udid: <serial>`, `appium:app: <path.apk>` atau `appPackage`/`appActivity`, `appium:noReset: false`, `appium:newCommandTimeout: 120`.

**Jebakan yang sudah diatasi — jangan dihapus:**
- `activateApp()` wajib; tanpa itu Appium bisa membuka home launcher, bukan aplikasi.
- Dialog izin/notifikasi bisa muncul **dua kali** (awal & setelah login); loop `tanganiDialogSistem()` sebelum dan sesudah login.
- Toggle Test Mode harus **idempoten** (`checked === 'true'` → skip). Klik kedua akan mematikan Test Mode.
- Field PIN dialog dan password login bisa punya `resource-id` sama; **scope ke dialog** dengan XPath atau strict mode WebdriverIO.
- Verifikasi NIK terbaca (`getText() === NIK`) sebelum klik login.

### 3.2 ADB langsung — smoke cepat

```powershell
adb shell input tap <x> <y>
adb shell input swipe <x1> <y1> <x2> <y2>
adb shell input text <teks>
```

Semua aksi langsung terlihat di layar. Cocok untuk demo, tapi tetap sertakan asersi nyata (teks/UI dump), bukan sekadar "terlihat jalan".

---

## 4. Coverage khusus mobile

Selain matrix umum di CORE, uji:

- Onboarding, login/logout, session expired, dan multi-role.
- Izin: notifikasi, kamera, lokasi, storage — izinkan dan tolak, cek graceful degradation.
- Deep link / universal link, foreground → background → foreground, rotate orientation.
- Biometrik & fallback PIN bila ada.
- Safe area/notch, keyboard muncul, teks panjang, lokalisasi bahasa.
- UI dump XML → cek `resource-id`/`content-desc`; **semua** tombol dan field tersentuh, termasuk tab tersembunyi.
- Storage: SharedPreferences/SQLite/Realm — apakah credential/token tersimpan plaintext (lapor sebagai temuan bila ya, sesuai izin).
- Logcat: exception, stack trace, dan pesan sensitif.
- Network inspection (proxy/MITM) **hanya dengan consent tertulis**; uji validasi TLS, certificate pinning, dan fallback HTTP plaintext. Jangan pasang MITM di produksi.
- API mobile: header (`Authorization`, `Android-ID`), status `200/201/400/401/403/422`, latency > 2.000 ms, error handling tanpa stack trace mentah.
- Pemetaan temuan ke **OWASP MASVS** (storage, crypto, auth, network, platform interaction, code quality, resiliency).

---

## 5. Bukti & video

1. **Screenshot tiap temuan**, segera saat asersi. `saveScreenshot()` dari session WDIO lebih disukai daripada `adb screencap` karena diambil tepat pada momen asersi. Simpan asli di `pendukung/bukti/mobile/<id>.png`.
   ```powershell
   adb -s <serial> shell screencap -p /sdcard/shot.png
   adb -s <serial> pull /sdcard/shot.png pendukung/bukti/mobile/<id>.png
   ```
   **Jangan pakai `>` PowerShell untuk PNG** (merusak biner). Verifikasi header `\x89PNG\r\n\x1a\n`.
2. **Video asli dari login sampai seluruh test selesai** bila diminta — bukan gambar diam, dan **jangan dihapus** setelah laporan jadi.
   ```powershell
   adb -s <serial> shell screenrecord --time-limit 180 /sdcard/test.mp4
   adb -s <serial> pull /sdcard/test.mp4 pendukung/bukti/mobile/e2e-lengkap.mp4
   ```
   Boleh memakai screen recorder bawaan MuMu bila itu lingkungan yang dipakai.
3. Logcat dan dump XML ikut disimpan: `pendukung/bukti/mobile/logcat.txt`, `pendukung/bukti/mobile/ui.xml`.
4. Cantumkan anotasi memakai schema CORE: `shots: [{ref, highlight:{type:"circle"|"box", ...}, label}]`. Koordinat relatif 0–1. Tanpa `highlight`, temuan dianggap belum selesai.
5. `location` memakai format `Layar/Activity + resource-id`, mis. `HomeActivity · btn_submit`.

---

## 6. Pelaporan & batasan

- Untuk `e2e all`: tulis `pendukung/ai/triage.mobile.json`, ID diawali `MOB-`, bukti/video di `pendukung/bukti/mobile/`. **Jangan generate DOCX** — `@qa-lead` yang menggabungkan.
- Untuk `e2e mobile` saja: tulis `pendukung/ai/triage.json` dengan `report.profile = "mobile"`, lalu jalankan generator CORE satu kali dan verifikasi.
- Android yang tidak bisa di-resolve, GMS tidak didukung, ADB offline permanen, atau iOS → `BLOCKED` dengan alasan teknis dan input yang dibutuhkan.
- Web/URL-only → bukan scope skill ini; kembalikan ke `@qa-lead` untuk `@qa-web-engineer`.
- Jangan membuat DOCX terpisah untuk pentest mobile, network, performa, atau API — semuanya masuk satu laporan.
