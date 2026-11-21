# QA Team

Satu repo untuk tim QA & security OpenCode: **5 agent + 6 skill**. Clone repo ini, jalankan `setup.ps1`, maka tim langsung siap dipanggil di chat OpenCode.

Tim ini menghasilkan laporan audit-ready (DOCX) dengan bukti sungguhan — screenshot beranotasi merah, video asli, dan Bab **Kesimpulan** yang wajib ada.

> **Baru clone?** Ikuti [PANDUAN-LENGKAP.md](PANDUAN-LENGKAP.md) — satu panduan untuk Python/Playwright, kredensial & DB, AVD/MuMu/Appium, watch mode, bug hunt, dan generator DOCX. Cek hasil pasang dengan `powershell -ExecutionPolicy Bypass -File .\verify_setup.ps1`.

## Isi repo

```
qa-team/
├── agents/                          ← 5 agent OpenCode (file .md = ID agent)
│   ├── qa-lead.md                   koordinator, primary agent
│   ├── qa-web-engineer.md           E2E web (Playwright, watch mode, a11y)
│   ├── qa-mobile-engineer.md        E2E Android (AVD/ADB, Test Mode, video)
│   ├── bug-hunter.md                pentest berotorisasi
│   └── sp-specialist.md             notifikasi → stored procedure
├── skills/                          ← 6 skill (nama folder = ID skill)
│   ├── qa-e2e-tester/               CORE: aturan bersama + generator DOCX
│   ├── qa-web-e2e/                  protokol eksekusi web
│   ├── qa-mobile-e2e/               protokol eksekusi Android
│   ├── firerpa-eval/                referensi evaluasi/training FIRERPA lamda
│   ├── bug-hunter/                  WAF/API/mobile testing, CVSS, kill chain
│   └── sp-tracer/                   pelacakan SP lewat SELECT katalog
├── qa-credentials.example.json      template DB kosong, aman di-commit (satu-satunya)
├── setup.ps1                        installer agent + skill ke ~/.config/opencode
├── verify_setup.ps1                 preflight: Python, modul, agent, skill, ADB
├── PANDUAN-LENGKAP.md               panduan clone → pakai (web, mobile, DB, bug hunt)
└── .gitignore                       menjaga kredensial & output tidak ter-commit
```

Skrip yang sama tidak disimpan berulang: `build_report.py`, `db_verify.py`, dan `find_notif.py` hanya satu salinan di `skills/qa-e2e-tester/`. `setup.ps1` yang menyalinnya ke folder skill `bug-hunter` dan `sp-tracer` saat instalasi, karena tiap skill memanggil skrip dengan nama relatif di foldernya sendiri. `report_kit.py` sengaja tetap dua versi — implementasi bug-hunter bukan substitusi CORE.

Pemisahan E2E: **`qa-e2e-tester` tetap satu core** untuk aturan bersama (intake, kredensial, guardrail, format temuan, anotasi merah, verifikasi DB, generator DOCX). Protokol teknisnya dipisah menjadi `qa-web-e2e` dan `qa-mobile-e2e`. Dengan begitu, aturan tidak diduplikasi dan tidak bisa beda antar platform.

## Tim

| Agent | Peran | Dipanggil untuk |
|---|---|---|
| `@qa-lead` | Koordinator (`primary`) | Membagi tugas ke 4 spesialis, lalu menggabungkan hasilnya jadi satu laporan |
| `@qa-web-engineer` | Web QA (`subagent`) | E2E web, Playwright, `--watch`, aksesibilitas, responsif, console, API web, DOCX QA |
| `@qa-mobile-engineer` | Mobile QA (`subagent`) | E2E Android, AVD/ADB, Test Mode DCT, Appium, video asli, logcat, DOCX QA |
| `@bug-hunter` | Bug hunter (`subagent`) | Pentest berotorisasi, risk register, CVSS, kill chain, DOCX bug hunt |
| `@sp-specialist` | SP (`subagent`) | Lacak pesan validasi ke stored procedure, baca definisi tanpa `EXEC` |

`@qa-engineer` sudah **tidak dipakai** — perannya dibagi ke dua spesialis E2E. `setup.ps1` akan menghapus salinan lama itu otomatis. Setiap spesialis hanya boleh memakai skillnya sendiri dan tidak bisa memanggil subagent lain. `@qa-lead` yang mengatur delegasi.

## Pasang di laptop Windows

```powershell
git clone https://github.com/Minerky/qa-team.git
cd qa-team
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
powershell -ExecutionPolicy Bypass -File .\verify_setup.ps1
```

Lalu di chat OpenCode:

```
@qa-lead
```

`setup.ps1` menyalin `agents\*.md` ke `~/.config/opencode/agents/`, menyalin `skills\<id>\` ke `~/.config/opencode/skills/<id>/`, menghapus `qa-engineer.md` lama, dan membuat `~/.config/opencode/qa-credentials.local.json` **bila belum ada**. File kredensial lokal itu sengaja di luar repo.

Verifikasi cepat setelah `opencode reload` (kadang perlu dicek ulang sekali karena API bisa kosong sesaat):

```
opencode api get /api/agent     → qa-lead, qa-web-engineer, qa-mobile-engineer, bug-hunter, sp-specialist
opencode api get /api/skill     → qa-e2e-tester, qa-web-e2e, qa-mobile-e2e, firerpa-eval, bug-hunter, sp-tracer
```

### Dependensi Python

```powershell
python -m pip install python-docx pillow pyodbc playwright openpyxl
python -m playwright install chromium
```

Android: **AVD resmi Android Studio sebagai default automasi**. MuMu dipakai hanya untuk demo visual lama, perangkat fisik untuk UAT akhir. iOS/IPA **tidak didukung** dan akan dilaporkan `BLOCKED`.

## Cara kasih kerjaan

Koordinator (disarankan):

```
@qa-lead
Jalankan E2E dan hunt staging ini. Kalau ada notifikasi validasi,
suruh sp-specialist lacak SP-nya. Gabungkan buktinya ke satu laporan.
```

`e2e all` menjalankan web + mobile paralel, lalu lead menggabungkannya jadi **satu** `triage.json` dan **satu** DOCX:

```
@qa-lead
e2e all https://staging.contoh.com — sertakan video dari login sampai selesai
```

Langsung ke spesialis:

```
@qa-web-engineer e2e web https://staging.contoh.com --watch — sertakan aksesibilitas
@qa-mobile-engineer e2e mobile — test APK di hasil-test/app.apk, rekam videonya
@bug-hunt hunt --watch 30 https://staging.contoh.com/
@sp-specialist cari notifikasi: "Validasi gagal: area wajib diisi"
```

Input yang sebaiknya disertakan untuk bug hunt: **otorisasi tertulis**, target (URL/APK), environment (staging/UAT/produksi), dan akun uji. Tanpa otorisasi → `BLOCKED`, bukan dimulai sedikit saja.

Mode `--watch` membuka browser Playwright yang terlihat, `watch-dashboard.html`, dan diff engine untuk memantau perubahan.

## Evaluasi referensi FIRERPA / lamda

`@qa-lead` memuat skill `firerpa-eval` untuk **training & evaluasi**. Isinya: pemetaan kapabilitas dari dokumentasi publik GitHub (`github.com/firerpa/lamda`, MIT), gap analysis terhadap qa-team, checklist pilot, dan hasil pilot yang sudah dijalankan.

Status terkini: **DIPELAJARI · TERINSTALL DI LAB (v10.12) · PILOT TERBATAS PASS**. Instalasi memakai artifact rilis resmi yang diverifikasi SHA-256; pilot dilakukan di lab terpisah, non-root, tanpa MITM/Frida/proxy/klik/login. Bukti: `~/.config/opencode/firerpa-lab/` (`pilot-result.json`, `pilot-app-result.json`, `pilot-hierarchy.xml`, 2 screenshot asli).

```
@qa-lead
Rangkum hasil pilot FIRERPA/lamda untuk training tim —
 sebutkan cakupan yang sudah diuji dan yang masih BLOCKED.
```

Pilot memakai **MuMu** karena binary AVD tidak tersedia di mesin ini; ini dicatat sebagai penyimpangan, bukan pengganti kebijakan `AVD = automation`. Kalau diminta MITM/Frida/root/device farm atau pemakaian produksi, lead menjawab `BLOCKED` sampai ada approval tertulis formal, pilot ulang di AVD, dan pembandingan dengan Appium. Tidak ada klaim benchmark atau angka efisiensi. Evaluasi ini masuk slide training PPTX, bukan `triage.json` E2E.

## Kredensial & keamanan

- Isi `~/.config/opencode/qa-credentials.local.json` (salinan dari template). **Jangan pernah isi password di `qa-credentials.example.json`.**
- Password **tidak pernah diminta di chat**, tidak ditulis ke spec, dan tidak masuk DOCX.
- Prioritas kredensial: `QA_CREDENTIALS_FILE` → `~/.config/opencode/qa-credentials.local.json` → file `.local.json` di folder skill. Environment `QA_DB_*` dapat meng-override.
- SQL Server: isi `server` + `database`. Contoh `HOST\\SQLEXPRESS` (backslash dobel di JSON). Pakai `auth: "windows"` bila tanpa password. Di mesin dengan ODBC legacy, isi `driver: "SQL Server"`.
- SQLite: isi `sqlite` dengan path file `.db`; koneksi SQL Server diabaikan.
- Dari file konfigurasi aplikasi, `find_notif.py` hanya mengambil **nama server dan database** — password tidak dibaca, disimpan, atau ditampilkan.

Contoh menjalankan pelacakan langsung lewat terminal:

```powershell
python "%USERPROFILE%\.config\opencode\skills\sp-tracer\find_notif.py" --text "Validasi gagal: area wajib diisi"
```

Opsi: `--text` (wajib), `--server`, `--database`, `--windows`, `--limit`, `--out`, `--no-discover`.

## Aturan yang dipegang tim

1. **Satu DOCX final** per laporan, termasuk `e2e all`. Draft HackerOne/Bugcrowd masuk appendix di dalam DOCX, bukan file `.md` terpisah.
2. **Bab Kesimpulan wajib** di laporan QA maupun bug hunt.
3. **Temuan sekecil apa pun tidak boleh lolos** — termasuk typo, tooltip salah, dan race condition tombol.
4. Setiap temuan punya urutan klik/tap eksplisit dan screenshot dengan **lingkaran/border merah + label**, tertanam di DOCX.
5. Uji sungguhan, bukti sungguhan. Video mobile asli dari login sampai test selesai **tidak dihapus**.
6. Database **read-only**: hanya `SELECT` / `WITH` / `PRAGMA`, satu statement. DML/DDL/`EXEC` ditolak.
7. Definisi SP dibaca lewat `SELECT` katalog (`sys.sql_modules` / `sys.objects`). **`EXEC` sengaja tidak didukung** karena isi prosedur bisa mengubah data.
8. Bug hunt: staging/UAT dulu; dilarang eksploitasi destruktif; **berhenti otomatis** bila ada risiko perubahan permanen pada data produksi.
9. Hasil `FAIL` / `ERROR` / DB tidak terjangkau dilaporkan apa adanya sebagai temuan atau `BLOCKED` — tidak dibungkus "aman".
10. Presentasi manajer memakai bahasa profesional (quality & evidence automation). **Dilarang mengarang angka efisiensi.**
11. Aturan inti ada di `qa-e2e-tester`; skill domain tidak boleh mengubahnya.
12. `firerpa-eval` adalah evaluasi + pilot terbatas di lab: tidak menjalankan MITM/Frida/root, tidak mengklaim benchmark, dan tidak menggantikan guardrail. Hasil pilot tidak masuk `triage.json` E2E.

## Artefak yang dihasilkan

| Artefak | Isi |
|---|---|
| `*.docx` | Laporan final: ringkasan, risk register, temuan + bukti, Kesimpulan, appendix draft |
| `*.mp4` | Rekaman asli alur uji mobile bila diminta |
| `watch-dashboard.html` | Dashboard live saat `--watch` |
| `triage.web.json` / `triage.mobile.json` | Temuan per domain saat `e2e all`, digabung lead |
| `sp-notif-search.json` | Hasil pelacakan notifikasi → SP (path absolut dikembalikan ke lead) |
| `db-verification.json` | Hasil verifikasi DB read-only bila alur uji menyentuh DB |

PPTX manajer bila diminta: satu file dengan DOCX tertanam dan video bukti asli.

## Update

```powershell
cd qa-team
git pull
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
powershell -ExecutionPolicy Bypass -File .\verify_setup.ps1
```

## Catatan penting

- **Nama folder skill adalah ID skill.** Jangan ubah `qa-e2e-tester`, `qa-web-e2e`, `qa-mobile-e2e`, `firerpa-eval`, `bug-hunter`, `sp-tracer`.
- **Setiap `.md` di root `agents/` menjadi agent.** Jangan menaruh `README.md` di folder itu.
- `sp-tracer` adalah nama folder/skill; repositori lamanya bernama `sp-tracking`.
- DB belum terjangkau → `sp-specialist` akan menjawab `BLOCKED` dan meminta **nama instance / akses jaringan**, bukan password.
- Repo lama `Minerky/qa-e2e-tester`, `Minerky/bug-hunter`, dan `Minerky/sp-tracking` sudah tidak dipakai; isinya lengkap di sini.
