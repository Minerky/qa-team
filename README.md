# QA Team

Satu repo untuk tim QA & security OpenCode: **4 agent + 3 skill**. Clone repo ini, jalankan `setup.ps1`, maka tim langsung siap dipanggil di chat OpenCode.

Tim ini menghasilkan laporan audit-ready (DOCX) dengan bukti sungguhan — screenshot beranotasi merah, video asli, dan Bab **Kesimpulan** yang wajib ada.

## Isi repo

```
qa-team/
├── agents/                          ← 4 agent OpenCode (file .md = ID agent)
│   ├── qa-lead.md                   koordinator, primary agent
│   ├── qa-engineer.md               QA E2E web + Android
│   ├── bug-hunter.md                pentest berotorisasi
│   └── sp-specialist.md             notifikasi → stored procedure
├── skills/                          ← 3 skill (nama folder = ID skill)
│   ├── qa-e2e-tester/               Playwright, ADB, video, DOCX QA
│   ├── bug-hunter/                  WAF/API/mobile testing, CVSS, kill chain, DOCX
│   └── sp-tracer/                   pelacakan SP lewat SELECT katalog
├── qa-credentials.example.json      template DB kosong, aman di-commit
├── setup.ps1                        installer agent + skill ke ~/.config/opencode
└── Panduan.txt                      catatan singkat (cadangan README ini)
```

## Tim

| Agent | Peran | Dipanggil untuk |
|---|---|---|
| `@qa-lead` | Koordinator (`primary`) | Membagi tugas ke spesialis, lalu menggabungkan hasilnya jadi satu laporan |
| `@qa-engineer` | QA (`subagent`) | E2E web & Android APK, smoke test, bukti visual, video, DOCX QA |
| `@bug-hunter` | Bug hunter (`subagent`) | Pentest berotorisasi, risk register, CVSS, kill chain, DOCX bug hunt |
| `@sp-specialist` | SP (`subagent`) | Lacak pesan validasi ke stored procedure, baca definisi tanpa `EXEC` |

Setiap spesialis hanya boleh memakai skillnya sendiri dan tidak bisa memanggil subagent lain. `@qa-lead` yang mengatur delegasi.

## Pasang di laptop Windows

```powershell
git clone https://github.com/Minerky/qa-team.git
cd qa-team
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
```

Lalu di chat OpenCode:

```
@qa-lead
```

`setup.ps1` menyalin `agents\*.md` ke `~/.config/opencode/agents/`, menyalin `skills\<id>\` ke `~/.config/opencode/skills/<id>/`, dan membuat `~/.config/opencode/qa-credentials.local.json` **bila belum ada**. File kredensial lokal itu sengaja di luar repo.

Verifikasi cepat setelah `opencode reload` (kadang perlu dicek ulang sekali karena API bisa kosong sesaat):

```
opencode api get /api/agent     → qa-lead, qa-engineer, bug-hunter, sp-specialist
opencode api get /api/skill     → qa-e2e-tester, bug-hunter, sp-tracer
```

### Dependensi Python

```powershell
python -m pip install python-docx pillow pyodbc playwright openpyxl
python -m playwright install chromium
```

Android: emulator MuMu atau perangkat lewat ADB. iOS/IPA **tidak didukung** dan akan dilaporkan `BLOCKED`.

## Cara kasih kerjaan

Koordinator (disarankan):

```
@qa-lead
Jalankan E2E dan hunt staging ini. Kalau ada notifikasi validasi,
suruh sp-specialist lacak SP-nya. Gabungkan buktinya ke satu laporan.
```

Langsung ke spesialis:

```
@qa-engineer e2e web https://staging.contoh.com — sertakan video dari login sampai selesai
@bug-hunt hunt --watch 30 https://staging.contoh.com/
@sp-specialist cari notifikasi: "Validasi gagal: area wajib diisi"
```

Input yang sebaiknya disertakan untuk bug hunt: **otorisasi tertulis**, target (URL/APK), environment (staging/UAT/produksi), dan akun uji. Tanpa otorisasi → `BLOCKED`, bukan dimulai sedikit saja.

Mode `--watch` membuka browser Playwright yang terlihat, `watch-dashboard.html`, dan diff engine untuk memantau perubahan.

## Kredensial & keamanan

- Isi `~/.config/opencode/qa-credentials.local.json` (salinan dari template). **Jangan pernah isi password di `qa-credentials.example.json`.**
- Password **tidak pernah diminta di chat**, tidak ditulis ke spec, dan tidak masuk DOCX.
- Prioritas kredensial: `QA_CREDENTIALS_FILE` → `~/.config/opencode/qa-credentials.local.json` → file `.local.json` di folder skill. Environment `QA_DB_*` dapat meng-override.
- SQL Server: isi `server` + `database`. Contoh `HOST\\SQLEXPRESS` (backslash dobel di JSON). Pakai `auth: "windows"` bila tanpa password. Di mesin dengan ODBC legacy, isi `driver: "SQL Server"`.
- SQLite: isi `sqlite` dengan path file `.db`; koneksi SQL Server diabaikan.
- Dari file konfigurasi aplikasi, `find_notif.py` hanya mengambil **nama server dan database** — password tidak dibaca, disimpan, atau ditampilkan.

Contoh menjalankan pelacakan langsung lewat terminal:

```powershell
python C:\Users\Harrys\.config\opencode\skills\sp-tracer\find_notif.py --text "Validasi gagal: area wajib diisi"
```

Opsi: `--text` (wajib), `--server`, `--database`, `--windows`, `--limit`, `--out`, `--no-discover`.

## Aturan yang dipegang tim

1. **Satu DOCX final** per laporan. Draft HackerOne/Bugcrowd masuk appendix di dalam DOCX, bukan file `.md` terpisah.
2. **Bab Kesimpulan wajib** di laporan QA maupun bug hunt.
3. **Temuan sekecil apa pun tidak boleh lolos** — termasuk typo, tooltip salah, dan race condition tombol.
4. Setiap temuan punya urutan klik/tap eksplisit dan screenshot dengan **lingkaran/border merah + label**, tertanam di DOCX.
5. Uji sungguhan, bukti sungguhan. Video asli dari login sampai test selesai bila diminta.
6. Database **read-only**: hanya `SELECT` / `WITH` / `PRAGMA`, satu statement. DML/DDL/`EXEC` ditolak.
7. Definisi SP dibaca lewat `SELECT` katalog (`sys.sql_modules` / `sys.objects`). **`EXEC` sengaja tidak didukung** karena isi prosedur bisa mengubah data.
8. Bug hunt: staging/UAT dulu; dilarang eksploitasi destruktif; **berhenti otomatis** bila ada risiko perubahan permanen pada data produksi.
9. Hasil `FAIL` / `ERROR` / DB tidak terjangkau dilaporkan apa adanya sebagai temuan atau `BLOCKED` — tidak dibungkus "aman".
10. Presentasi manajer memakai bahasa profesional (quality & evidence automation). **Dilarang mengarang angka efisiensi.**

## Artefak yang dihasilkan

| Artefak | Isi |
|---|---|
| `*.docx` | Laporan final: ringkasan, risk register, temuan + bukti, Kesimpulan, appendix draft |
| `*.mp4` | Rekaman asli alur uji bila diminta |
| `watch-dashboard.html` | Dashboard live saat `--watch` |
| `sp-notif-search.json` | Hasil pelacakan notifikasi → SP (path absolut dikembalikan ke lead) |
| `db-verification.json` | Hasil verifikasi DB read-only bila alur uji menyentuh DB |

PPTX manajer bila diminta: satu file dengan DOCX tertanam dan video bukti asli.

## Update

```powershell
cd qa-team
git pull
powershell -ExecutionPolicy Bypass -File .\setup.ps1
opencode reload
```

## Catatan penting

- **Nama folder skill adalah ID skill.** Jangan ubah `qa-e2e-tester`, `bug-hunter`, `sp-tracer`.
- **Setiap `.md` di root `agents/` menjadi agent.** Jangan menaruh `README.md` di folder itu.
- `sp-tracer` adalah nama folder/skill; repositori lamanya bernama `sp-tracking`.
- DB belum terjangkau → `sp-specialist` akan menjawab `BLOCKED` dan meminta **nama instance / akses jaringan**, bukan password.
- Repo lama `Minerky/qa-e2e-tester`, `Minerky/bug-hunter`, dan `Minerky/sp-tracking` sudah tidak dipakai; isinya lengkap di sini.
