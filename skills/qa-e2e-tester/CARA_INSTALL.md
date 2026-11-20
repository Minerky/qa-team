# Panduan Instalasi Skill `qa-e2e-tester` di Laptop / Komputer Baru

Panduan ini digunakan untuk memasang skill **`qa-e2e-tester`** pada instalasi OpenCode di laptop baru, termasuk konfigurasi otomasi Android lewat **MuMu Emulator** supaya testing bisa dilihat langsung berjalan.

---

## 1. Prasyarat Sistem

Pastikan perangkat baru sudah terpasang:

- **Git**: [Download Git](https://git-scm.com/)
- **Python 3.10+**: [Download Python](https://www.python.org/)
- **OpenCode CLI**: terpasang dan bisa dijalankan (`opencode --version`)
- **Untuk otomasi Android dengan MuMu**:
  - MuMu Player: [https://www.mumuplayer.com/](https://www.mumuplayer.com/)
  - ADB / Android Platform-Tools: [https://developer.android.com/studio/releases/platform-tools](https://developer.android.com/studio/releases/platform-tools)
  - Node.js 20 LTS atau lebih baru (terverifikasi: Node 26): [https://nodejs.org/](https://nodejs.org/)
  - Appium **4.x** + driver `UiAutomator2` **9.x** (terverifikasi: 4.0.0 / 9.2.2)
  - Java **JDK 21** (Eclipse Temurin; terverifikasi 21.0.13). JDK 17 tidak lagi dipakai di mesin referensi.
  - Android SDK minimal dengan `ANDROID_HOME` ter-set, berisi `platform-tools\adb.exe` + `AdbWinApi.dll` + `AdbWinUsbApi.dll` (salin 3 file itu dari folder `nx_main` MuMu — tanpa DLL, Appium gagal mendeteksi device)
- **Untuk iOS**: macOS + Xcode. **MuMu tidak bisa menjalankan iOS**, jadi pakai simulator Xcode atau perangkat asli.

---

## 2. Instalasi Skill

### Opsi A — Salin folder dari laptop lama (PALING AMAN, disarankan)

Karena skill ini sudah dimodifikasi lokal (iOS, AI pentest, risk report, MuMu), cara paling aman adalah menyalin seluruh folder:

```powershell
# Dari laptop lama, salin folder ini:
C:\Users\<NAMA_YOU>\.config\opencode\skills\qa-e2e-tester

# Ke laptop baru di lokasi yang sama:
C:\Users\<NAMA_BARU>\.config\opencode\skills\qa-e2e-tester
```

Folder tersebut cukup berisi `SKILL.md` dan `CARA_INSTALL.md`. Setelah disalin, lanjut ke **bagian 4 (Konfigurasi MuMu)**.

### Opsi B — Clone dari GitHub + terapkan patch lokal

```powershell
# 1. Pastikan folder skills ada
New-Item -ItemType Directory -Force -Path "$HOME\.config\opencode\skills"

# 2. Clone repository
git clone https://github.com/Minerky/qa-e2e-tester.git "$HOME\.config\opencode\skills\qa-e2e-tester"

# 3. Dependensi Python untuk testing & pelaporan
python -m pip install playwright openpyxl python-docx pillow

# 4. Browser Chromium untuk Playwright
python -m playwright install chromium
```

Repository GitHub sudah berisi versi terbaru — tidak perlu patch atau salinan folder tambahan.

### macOS / Linux (Terminal)

```bash
mkdir -p "$HOME/.config/opencode/skills"
git clone https://github.com/Minerky/qa-e2e-tester.git "$HOME/.config/opencode/skills/qa-e2e-tester"
pip3 install playwright openpyxl python-docx pillow
playwright install chromium
```

---

## 3. Verifikasi Pemasangan

1. Buka OpenCode:
   ```bash
   opencode
   ```
2. Skill `qa-e2e-tester` terdeteksi otomatis. Jika belum, jalankan `/reload`.
3. Coba instruksi:
   - *"Jalankan E2E web https://... berdasarkan FSD ini."*
   - *"Jalankan smoke test APK di MuMu 127.0.0.1:16384 dengan jendela terlihat, rekam videonya."* (ganti dengan `adb_port` mesinmu)
   - *"Pentest staging ini dan buatkan risk-register.xlsx + RISK_REPORT.docx."*

---

## 4. Konfigurasi Mobile Android (MuMu Emulator) — Windows

### 4.1 Install tooling

```powershell
winget install Google.AndroidSDKPlatformTools
winget install OpenJS.NodeJS.LTS
winget install EclipseAdoptium.Temurin.21.JDK

npm install -g appium
appium driver install uiautomator2
appium driver doctor uiautomator2
```

Set `JAVA_HOME`, `ANDROID_HOME`, dan `ANDROID_SDK_ROOT` (sesuaikan path di mesin kamu):

```powershell
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
setx ANDROID_HOME "$env:LOCALAPPDATA\android-sdk-minimal"
setx ANDROID_SDK_ROOT "$env:LOCALAPPDATA\android-sdk-minimal"
```

> Di mesin referensi, SDK sengaja minimal: hanya `platform-tools\adb.exe` + `AdbWinApi.dll` + `AdbWinUsbApi.dll` yang disalin dari `C:\Program Files\Netease\MuMuPlayer\nx_main\`. Ini cukup untuk Appium UiAutomator2. Tanpa dua DLL itu, `adb devices` bisa kosong walaupun MuMu sudah connect.

Jika `ANDROID_HOME` belum ada, install **Android Studio → SDK Manager → Android SDK Command Line Tools**, lalu:

```powershell
sdkmanager "platform-tools"
```

### 4.2 Siapkan MuMu

1. Install MuMu Player dari [https://www.mumuplayer.com/](https://www.mumuplayer.com/).
2. Buka **Settings → ADB** dan aktifkan ADB debugging.
3. Set resolusi `1080x1920`, DPI `320`.
4. Biarkan jendela MuMu **terbuka dan terlihat** saat demo; jangan di-minimize atau mode headless.

### 4.3 Hubungkan ADB

**Jangan langsung pakai `7555`.** Tanyakan port sebenarnya ke CLI MuMu:

```powershell
& "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" info --vmindex 0
```

Lihat field `adb_port` pada output JSON (contoh nyata di laptop ini: `16384`). MuMu generasi lama memakai `7555/7557/7559`, tetapi MuMu Player 15 tidak.

```powershell
$adb = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
& $adb kill-server
& $adb start-server
& $adb connect 127.0.0.1:16384
& $adb devices
& $adb -s 127.0.0.1:16384 shell getprop ro.product.model
```

- Ganti `16384` dengan `adb_port` dari langkah di atas.
- Status harus `device`.
- `unauthorized` → klik **Allow** di jendela MuMu.
- `offline` → jalankan `& $adb disconnect 127.0.0.1:16384`, lalu connect lagi.
- Pakai `adb.exe` bawaan MuMu agar versi client/server cocok.

### 4.4 Jalankan Appium

```powershell
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot'
$env:ANDROID_HOME="$env:LOCALAPPDATA\android-sdk-minimal"
$env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
$env:PATH="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
appium server --port 4723 --base-path /wd/hub
```

Cek siap: `Invoke-RestMethod http://127.0.0.1:4723/wd/hub/status` → `"ready": true`.

Contoh capability (detail lengkap ada di `SKILL.md` bagian 3A0):

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:udid": "127.0.0.1:16384",
  "appium:app": "C:\\path\\ke\\app.apk",
  "appium:noReset": false,
  "appium:newCommandTimeout": 120
}
```

Smoke test cepat tanpa Appium (aksi langsung kelihatan di layar MuMu):

```powershell
adb install -r app.apk
adb shell input tap 540 1200
adb shell input swipe 540 1600 540 400
adb shell input text "halo"
```

### 4.4b Runner WebdriverIO (script `.spec.ts` yang siap jalan)

Buat file `wdio.conf.ts`, `android_mumu.spec.ts`, dan `package.json` di folder output (mis. `hasil-test-<app>/automation/`), lalu:

```powershell
$out="hasil-test-<app>\automation"
cd $out
npm install
```

Isi konfigurasi mengikuti petunjuk di `SKILL.md` bagian 3A0/3A.

Jalankan dengan kredensial dari environment — **jangan pernah menulis NIK/password ke file, spec, atau laporan**:

```powershell
$env:QA_NIK='NIK_UJI'
$env:QA_PASS='password_uji'
$env:QA_UDID='127.0.0.1:16384'   # gunakan adb_port dari bagian 4.3
npx wdio run wdio.conf.ts
```

Hasil yang diharapkan: `1 passing`. Jika gagal, baca catatan jebakan di `SKILL.md` bagian 3A0.1 (`activateApp`, dialog izin, toggle idempoten, PIN yang scope ke dialog).

### 4.5 Rekam bukti otomasi

```powershell
$adb = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
$serial = "127.0.0.1:16384"
& $adb -s $serial shell screenrecord --time-limit 30 /sdcard/test.mp4
& $adb -s $serial pull /sdcard/test.mp4 hasil-test/evidence/android/demo.mp4
# PENTING: jangan pakai `>` PowerShell untuk PNG (merusak biner)
& $adb -s $serial shell screencap -p /sdcard/shot.png
& $adb -s $serial pull /sdcard/shot.png hasil-test/evidence/android/step-01.png
& $adb -s $serial logcat -v time > hasil-test/evidence/android/logcat.txt
```

Bisa juga pakai fitur screen recorder bawaan MuMu.

### 4.6 Catatan macOS / Linux

MuMu terutama untuk Windows. Di macOS/Linux, gunakan emulator Android Studio atau perangkat fisik, lalu koneksikan dengan ADB seperti biasa. Untuk iOS, wajib macOS + Xcode (lihat `SKILL.md` bagian 3D).

---

## 5. Cara Update Skill ke Versi Terbaru

Jika repository GitHub dapat pembaruan:

```bash
cd ~/.config/opencode/skills/qa-e2e-tester
git pull --rebase origin main
```

Gunakan `--rebase` agar riwayat tetap linier. Jika ada perubahan lokal, commit dulu atau simpan cadangan sebelum pull — jangan mengandalkan patch.

---

## 6. Ringkasan Perintah Cepat (Laptop Baru, Windows)

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.config\opencode\skills"
Copy-Item -Recurse "D:\backup\qa-e2e-tester" "$HOME\.config\opencode\skills\qa-e2e-tester"

python -m pip install playwright openpyxl python-docx pillow
python -m playwright install chromium

winget install Google.AndroidSDKPlatformTools
winget install OpenJS.NodeJS.LTS
winget install EclipseAdoptium.Temurin.21.JDK
npm install -g appium
appium driver install uiautomator2

# JANGAN pakai 7555 — temukan port asli dulu (contoh: 16384)
& "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" info --vmindex 0
& "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe" connect 127.0.0.1:<adb_port>
& "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe" devices

opencode
```
