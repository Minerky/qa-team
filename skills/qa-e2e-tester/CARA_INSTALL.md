# Panduan instalasi — tim QA (`qa-team`)

Panduan ini untuk manusia. Instruksi agent ada di `SKILL.md` masing-masing skill.

## 1. Struktur baru (sejak 2026-11-21)

```
qa-team/
├── setup.ps1
├── agents/  qa-lead, qa-web-engineer, qa-mobile-engineer, bug-hunter, sp-specialist
└── skills/  qa-e2e-tester (CORE), qa-web-e2e, qa-mobile-e2e, bug-hunter, sp-tracer
```

`qa-e2e-tester` **bukan lagi skill mandiri untuk eksekusi web/mobile**. Ia berisi aturan bersama dan generator DOCX. Eksekusi web ada di `qa-web-e2e`, eksekusi Android ada di `qa-mobile-e2e`. Agent `qa-engineer` lama sudah diganti dua spesialis.

## 2. Pasang / update (Windows)

```powershell
git clone https://github.com/Minerky/qa-team.git
cd qa-team
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
```

`setup.ps1` menyalin semua agent dan kelima skill ke `~/.config/opencode/`, menghapus `qa-engineer.md` lama, dan membuat `~/.config/opencode/qa-credentials.local.json` bila belum ada. Jangan mengisi password di `qa-credentials.example.json` — template itu aman di-commit.

Verifikasi:

```
opencode api get /api/agent     → 5 agent
opencode api get /api/skill     → 5 skill
```

## 3. Dependensi

```powershell
python -m pip install python-docx pillow pyodbc playwright openpyxl
python -m playwright install chromium
```

Web: tool Playwright tersedia di sesi OpenCode lewat Code Mode; tidak perlu `npm install` untuk eksekusi ad-hoc.

Android: **AVD resmi Android Studio adalah default automasi**. Siapkan virtualisasi (VT-x/AMD-V + WHPX/HAEVM), lalu:

```powershell
emulator -accel-check
emulator -list-avds
emulator -avd Pixel8_API_34 -no-boot-anim
adb devices        # emulator-5554
```

Tooling Appium bila dipakai: Node 20+, Appium 4.x, driver `uiautomator2` 9.x, JDK 21, WebdriverIO 10.x.

MuMu Player masih bisa dipakai untuk demo visual lama. Port ADB-nya bukan selalu `7555` — tanyakan:

```powershell
& "C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" info --vmindex 0
```

Pakai field `adb_port` dari output, lalu connect dengan `adb.exe` bawaan MuMu. MuMu **bukan** target CI/regresi deterministik; Genymotion Desktop juga tidak disarankan untuk automation (vendor menyatakan hal yang sama). Perangkat fisik dipakai untuk UAT akhir.

iOS/IPA tetap **`BLOCKED`** — butuh macOS + Xcode.

## 4. Cara memanggil

```
@qa-lead e2e web https://staging.contoh.com --watch
@qa-lead e2e mobile --rekam
@qa-lead e2e all https://staging.contoh.com
```

Atau langsung ke `@qa-web-engineer` / `@qa-mobile-engineer`. Untuk `e2e all`, lead yang menggabungkan `triage.web.json` + `triage.mobile.json` menjadi satu DOCX.

## 5. Aturan yang tidak berubah

Satu DOCX final · Bab Kesimpulan wajib · temuan sekecil apa pun wajib masuk · urutan klik/tap eksplisit + screenshot lingkaran merah berlabel · kredensial tidak pernah di chat · DB read-only (`SELECT`/`WITH`/`PRAGMA`) · `EXEC` ditolak · video asli tidak dihapus.

Detail lengkap ada di `README.md` repo dan di `SKILL.md` tiap skill.
