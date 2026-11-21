# Peta Tim QA — baca ini dulu (3 menit)

Ini **etalase tim**. Kalau kamu baru clone repo ini, mulai dari sini sebelum membaca aturan teknis yang panjang.

Singkatnya: **5 agent (mekanik) + 6 skill (buku panduan) → 1 buku catatan (`triage.json`) → 1 laporan Word.**

---

## 1. Peta satu layar

```mermaid
flowchart LR
    U[User / Manager] --> L[@qa-lead<br/>primary]
    L --> W[@qa-web-engineer]
    L --> M[@qa-mobile-engineer]
    L --> B[@bug-hunter]
    L --> S[@sp-specialist]

    W --> CORE[qa-e2e-tester<br/>CORE]
    M --> CORE
    W --> DW[qa-web-e2e]
    M --> DM[qa-mobile-e2e]
    B --> SB[skill bug-hunter]
    S --> SS[sp-tracer]
    L --> EV[firerpa-eval<br/>evaluasi saja]

    W --> T[triage.web.json]
    M --> T2[triage.mobile.json]
    B --> T3[findings]
    S --> T4[db-verification.json]

    T --> MERGE[lead menggabungkan<br/>triage.json]
    T2 --> MERGE
    T3 --> MERGE
    T4 --> MERGE
    MERGE --> G[build_report.py]
    G --> DOCX[1 DOCX + Bab Kesimpulan]
```

Versi tanpa gambar:

```
@qa-lead  →  web │ mobile │ security │ database  →  triage.json  →  build_report.py  →  1 DOCX
```

---

## 2. Siapa melakukan apa

| Agent | Mode | Skill yang dimuat | Output khas | Tidak boleh |
|---|---|---|---|---|
| **`@qa-lead`** | `primary` | `qa-e2e-tester` (saat menggabung), `firerpa-eval` | Membagi kerja, menggabungkan hasil, **satu DOCX final** | Mengerjakan E2E/pentest sendiri; memanggil agent di luar 4 spesialis |
| **`@qa-web-engineer`** | `subagent` | `qa-e2e-tester` + `qa-web-e2e` | `triage.web.json`, screenshot, watch dashboard | Android/iOS; membuat DOCX sendiri saat `e2e all` |
| **`@qa-mobile-engineer`** | `subagent` | `qa-e2e-tester` + `qa-mobile-e2e` | `triage.mobile.json`, video MP4 asli, logcat | iOS/IPA (`BLOCKED`); hardcode serial/package |
| **`@bug-hunter`** | `subagent` | `bug-hunter` | Temuan + CVSS + kill chain, draft HackerOne di appendix | Mulai tanpa izin tertulis; eksploitasi destruktif |
| **`@sp-specialist`** | `subagent` | `sp-tracer` | Nama SP + nomor baris definisi + field wajib | `EXEC`, DML/DDL; menebak SP kalau DB tak terjangkau |

> **Pihak eksternal:** Product/Owner (pemilik FSD) dan Dev (penerima tiket) memang ikut dicatat di RACI, tapi **bukan karyawan tim QA**. Lihat [SOP-QA.md](SOP-QA.md) §2.

---

## 3. Skill itu buku panduan apa saja?

| Skill | Peran | Dipasangkan dengan | Dipakai untuk |
|---|---|---|---|
| `qa-e2e-tester` | **CORE** — aturan bersama | `qa-web-e2e` **atau** `qa-mobile-e2e` | Intake, kredensial lokal, guardrail, format temuan, anotasi merah, DB read-only, generator DOCX, Bab Kesimpulan |
| `qa-web-e2e` | Protokol web | CORE | Playwright, browser terlihat/`--watch`, a11y WCAG 2.2 AA, responsif, console/API |
| `qa-mobile-e2e` | Protokol Android | CORE | AVD/ADB, MuMu (demo), Test Mode DCT, Appium, video asli, logcat |
| `bug-hunter` | Protokol keamanan | Berdiri sendiri | WAF, JWT/OAuth, blind vuln, kill chain, CVSS, satu DOCX bug hunt |
| `sp-tracer` | Protokol database | Berdiri sendiri | Lacak notifikasi → stored procedure lewat `SELECT` katalog |
| `firerpa-eval` | Referensi evaluasi | Berdiri sendiri | Pemetaan kapabilitas + pilot terbatas FIRERPA/lamda. **Bukan alur QA reguler** |

Aturan CORE **selalu menang** kalau skill domain bertentangan.

---

## 4. Alur satu perintah

1. **User memberi perintah** ke `@qa-lead`, misalnya `e2e all https://staging.contoh.com`.
2. **Lead cek kelengkapan**: target, environment, akun uji, dokumen induk (FSD/Blueprint/SIT), dan izin tertulis kalau ada pentest.
3. **Lead mendelegasikan** ke spesialis yang tepat — paralel kalau `e2e all`.
4. **Tiap spesialis menguji sungguhan**, menulis temuan ke `triage*.json`, menyimpan bukti (screenshot berlingkaran merah, video asli).
5. **Lead menggabungkan** menjadi satu `triage.json`, lalu menjalankan **satu kali** `build_report.py` + `--verify`.
6. **Manusia menandatangani** lewat `governance.signoff`. Tanpa itu, DOCX terbaca **menunggu sign-off**.

---

## 5. Aturan emas

1. **Satu DOCX** per laporan — bukan satu DOCX per disiplin.
2. **Bab Kesimpulan & Rekomendasi Akhir wajib** ada.
3. **Temuan sekecil apa pun masuk**, termasuk INFO/LOW/typo.
4. **Bukti harus nyata**: klik/tap berurutan + screenshot merah berlabel; video mobile dari login sampai selesai tidak dihapus.
5. **`BLOCKED` lebih jujur daripada "lolos"** tanpa bukti.
6. **FSD/Blueprint/SIT adalah hakim bersama** — tidak ada ekspektasi hasil karangan sendiri.
7. **Kredensial tidak pernah diketik di chat**; pakai file lokal. DB hanya `SELECT`/`WITH`/`PRAGMA`, satu statement.
8. **Manusia yang bertanggung jawab**; agent hanya membantu.

---

## 6. Peta dokumen

| Dokumen | Isi |
|---|---|
| [README.md](../README.md) | Etalase repo + cara pasang cepat |
| **Peta ini** | Peta tim, routing, jalur belajar |
| [PANDUAN-LENGKAP.md](PANDUAN-LENGKAP.md) | Clone → pakai: Python/Playwright, DB, AVD/MuMu, watch mode, bug hunt, generator |
| [SOP-QA.md](SOP-QA.md) | RACI, otorisasi, DoR/DoD, SLA, sign-off, retensi |
| [authorization.md](../templates/authorization.md) | Form izin tertulis untuk pentest |
| [qa-credentials.example.json](../config/qa-credentials.example.json) | Template kredensial kosong (jangan diisi password) |
| [scripts/setup.ps1](../scripts/setup.ps1) | Installer agent + skill |
| [scripts/verify_setup.ps1](../scripts/verify_setup.ps1) | Preflight installation |

---

## 7. Jalur belajar 15 menit

1. Baca **Peta ini** (selesai — 3 menit).
2. Baca [README.md](../README.md) bagian *Cara kasih kerjaan* (2 menit).
3. Baca [SOP-QA.md](SOP-QA.md) §1–§2 — siapa berwenang, siapa mengerjakan (3 menit).
4. Baca [qa-e2e-tester/SKILL.md](../skills/qa-e2e-tester/SKILL.md) bagian *Ringkasan 1 menit* + *Guardrail* (3 menit).
5. Baca satu skill domain sesuai kerjaanmu: [web](../skills/qa-web-e2e/SKILL.md) atau [mobile](../skills/qa-mobile-e2e/SKILL.md) (4 menit).
6. Baru masuk [PANDUAN-LENGKAP.md](PANDUAN-LENGKAP.md) kalau sudah mau praktek.

---

## 8. Istilah singkat

| Istilah | Arti warungnya |
|---|---|
| **Agent** | Mekanik yang menjalankan kerjaan |
| **Skill** | Buku panduan yang dibaca mekanik |
| **Core** | Buku aturan utama yang menang kalau ada beda pendapat |
| **`triage.json`** | Buku catatan temuan — satu-satunya sumber kebenaran |
| **`build_report.py`** | Mesin cetak yang mengubah catatan jadi DOCX |
| **`BLOCKED`** | Tidak jalan karena syarat kurang — bukan berarti lolos |
| **Sign-off** | Tanda tangan manusia supaya laporan sah |
