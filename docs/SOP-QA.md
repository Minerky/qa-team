# SOP QA Engineering — `qa-team`

Dokumen ini mengatur **orang, proses, dan kewenangan** di sekitar tooling QA. Aturan teknis eksekusi ada di `PANDUAN-LENGKAP.md` dan `SKILL.md` masing-masing; SOP ini mengatur siapa yang memutuskan dan kapan sesuatu dianggap selesai.

> Status: **usulan standar tim** — angka SLA dan matriks RACI di bawah perlu disahkan oleh manajer sebelum dipakai sebagai kebijakan resmi. Setelah disahkan, ubah status menjadi `BERLAKU` dan cantumkan tanggal pengesahan di bawah.

**Pengesahan:**  Disetujui oleh: `(...)` · Tanggal: `(...)` · Berlaku sampai: `(...)`

---

## 1. Prinsip

1. Agent membantu; **manusia yang bertanggung jawab**. Validasi manual wajib untuk temuan CRITICAL/HIGH.
2. Satu laporan DOCX per perintah — bukan DOCX per disiplin. `triage.json` adalah satu-satunya sumber kebenaran.
3. `BLOCKED` lebih jujur daripada "lolos" tanpa bukti. Tidak ada klaim efisiensi atau angka yang tidak berasal dari data.
4. Tidak ada aksi yang mengubah data tanpa izin tertulis dan jalur rollback.
5. Semua temuan masuk laporan, termasuk INFO/LOW/typo.

---

## 2. Struktur & RACI

| Kegiatan | QA Manager | QA Lead | Web/Mobile Engineer | Bug Hunter | SP Specialist | QA Ops | SDET | Product/Owner (eksternal) | Eng/Dev (eksternal) |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Menetapkan scope & otorisasi | **A** | R | C | C | C | C | C | **R** | I |
| Menyusun test plan & case | I | **A/R** | R | C | C | C | R | C | I |
| Eksekusi E2E web/mobile | I | A | **R** | I | I | C | R | I | I |
| Eksekusi pentest | I | A | C | **R** | C | C | C | I | I |
| Pelacakan notifikasi → SP | I | C | I | I | **A/R** | R | I | I | C |
| Validasi manual CRITICAL/HIGH | **A** | R | C | R | I | I | I | C | C |
| Triage & prioritas temuan | I | **A/R** | R | R | C | I | C | C | C |
| Perbaikan (eksternal) & retest (QA) | I | **A/R** | R | R | I | C | R | I | R |
| Sign-off rilis | **A/R** | C | I | I | I | I | I | C | I |
| Retensi & akses bukti | **A** | R | I | I | I | R | C | I | I |
| Menjaga env & data uji (DoR) | I | C | I | I | I | **A/R** | C | I | I |
| Memelihara harness otomasi | I | C | C | I | I | C | **A/R** | I | I |

`R` = pelaksana · `A` = akuntabel (satu pemilik) · `C` = dikonsultasi · `I` = diberi tahu.

**Product/Owner dan Eng/Dev adalah pihak eksternal** — bukan karyawan QA. Kolom keduanya tetap ada di RACI karena laporan wajib mencatat siapa yang dikonsultasi/diberi tahu, bukan karena mereka bagian dari struktur tim. QA Manager boleh merangkap sebagai penandatangan otorisasi pentest.

**Pemilik saat ini:** QA Manager `(...)` · QA Lead `(...)` · Web `(...)` · Mobile `(...)` · Security `(...)` · DB/SP `(...)` · QA Ops `(...)` · SDET `(...)`. Isi sebelum dipakai; kosong = `BLOCKED` untuk sign-off.

---

## 3. Otorisasi (wajib sebelum pentest / aksi yang mengubah state)

- Pakai `templates/authorization.md`. Salin ke workspace per project, isi, lalu simpan bersama bukti.
- Minimal berisi: target & scope, environment, penanggung jawab, metode yang diizinkan, yang dilarang, jendela waktu, backup/rollback, dan kontak eskalasi.
- **Tanpa otorisasi tertulis → `BLOCKED`.** Jangan menjalankan scan atau exploit.
- Produksi hanya dengan approval eksplisit dari owner + QA Manager, dan hanya probe deteksi-safe kecuali ada backup/rollback terverifikasi.
- Referensi otorisasi dicatat di `triage.json` → `governance.authorization.ref` agar muncul di DOCX.

---

## 4. Definition of Ready & Done

**Siap diuji (DoR):**
- Target/URL/APK dan environment jelas (staging/UAT atau ada approval).
- Akun uji + OTP/PIN test tersedia di file lokal, bukan di chat.
- Data uji bisa di-reset; selector stabil (`resource-id`/`data-testid`).
- Otorisasi tertulis ada bila scope menyentuh keamanan atau perubahan state.

**Selesai (DoD):**
- Semua case berstatus `PASS` / `FAIL` / `BLOCKED`; tidak ada yang dilewati diam-diam.
- Setiap temuan punya langkah klik/tap berurutan, lokasi eksplisit, screenshot asli **+ lingkaran/kotak merah berlabel**, dan entri `triage.json`.
- Video asli mobile (login → selesai) tidak dihapus.
- Risk score `L × I` + confidence terisi; CRITICAL/HIGH divalidasi manual oleh QA Manager/Lead.
- Satu DOCX dihasilkan oleh `build_report.py` dan lulus `--verify` (termasuk Bab Kesimpulan).
- Temuan sudah punya **owner, tiket, status defect, dan SLA** di `triage.json`.
- Cleanup/rollback data uji dilaporkan `VERIFIED` atau `PARTIAL` — bukan dianggap selesai tanpa bukti.

---

## 5. Severity, SLA, dan siklus temuan

Target berikut adalah **default usulan**; sesuaikan dengan kesepakatan tim setelah disahkan.

| Severity | Respons | Target perbaikan | Retest |
|---|---|---|---|
| CRITICAL | 1 hari kerja | 3 hari kerja | Maks. 1 hari kerja setelah fix |
| HIGH | 2 hari kerja | 7 hari kerja | Maks. 2 hari kerja |
| MEDIUM | 3 hari kerja | 30 hari kerja | Sprint berikutnya |
| LOW / INFO | 5 hari kerja | Sprint berikutnya / backlog | Saat regresi berikutnya |

**Siklus status defect:** `OPEN` → `ASSIGNED` → `IN_PROGRESS` → `FIXED` → `RETEST_PASS` / `REOPEN` → `CLOSED`.

- Perubahan status wajib dicatat di `defect_status` + tanggal di `sla_due`.
- `REOPEN` wajib mencantumkan `retest_of` (ID temuan sebelumnya) dan alasan.
- `BLOCKED` bukan `CLOSED`. Tetap masuk laporan dengan alasan teknis.
- Lewat SLA → eskalasi ke QA Manager otomatis; dicatat di `governance.notes`.

---

## 6. Traceability — FSD / Blueprint / SIT sebagai pusat

**Semua disiplin berpadu pada satu dokumen induk.** Tidak ada agent yang boleh menyusun ekspektasi atau test case "dari ide sendiri" lalu mengklaimnya sebagai hasil pengujian sesuai spesifikasi.

### 6.1 Dokumen induk (wajib ditetapkan sebelum eksekusi)

Satu di antara ini harus dipakai sebagai acuan utama, dengan urutan prioritas:

1. **FSD** / PRD — aturan bisnis & ekspektasi perilaku.
2. **Blueprint** — desain alur, layar, API, dan struktur data.
3. **SIT / test script** — skenario integrasi & ekspektasi resmi dari tim.
4. User guide / konfigurasi aplikasi — hanya bila tiga di atas tidak ada, dan harus dicatat sebagai acuan pengganti.

Catat di `triage.json`:

```json
"spec": {
  "primary_doc": "FSD Wisesa v2.3",
  "version": "2.3",
  "path": "dokumen/FSD-Wisesa-v2.3.pdf",
  "refs": ["REQ-9", "REQ-12"],
  "blackbox_only": false
}
```

Kalau tidak ada dokumen sama sekali → `blackbox_only: true`, dan **semua asersi "sesuai spesifikasi" dinyatakan `BLOCKED`** — bukan lolos, bukan gagal. Tanya sekali ke user, jangan mengarang.

### 6.2 Rantai bukti

```
Requirement (FSD/Blueprint/SIT)  →  test case ID (generated-cases.md)  →  finding ID (triage.json)  →  ticket
```

- Tiap test case wajib mencantumkan `source`: nama dokumen + pasal/halaman/ID requirement.
- Tiap finding wajib mengisi `requirement` (ID dari dokumen induk) dan `spec_status`:
  - `CONFORM` — sesuai dokumen;
  - `DEVIATION` — menyimpang dari dokumen (ini yang jadi temuan);
  - `UNVERIFIED` — belum bisa dibandingkan karena dokumen tidak ada.
- Eksplorasi blackbox tetap **boleh** untuk memburu celah, tapi temuannya diberi label **hipotesis/observasi**, bukan "pelanggaran FSD", sampai dicocokkan ke dokumen induk.
- `@qa-lead` **menolak menggabungkan** hasil spesialis yang tidak mencantumkan `spec.primary_doc` dan `source` test case.

`build_report.py` menyisipkan dokumen induk di Bab Kesimpulan dan `source`/`spec_status` di Bab Temuan. Field pendukung: `ticket`, `owner`, `requirement`.

---

## 7. Sign-off rilis

1. QA Lead mengisi `governance.signoff` di `triage.json`: `decision`, `approved_by`, `date`.
2. Rekomendasi otomatis dari generator:
   - ada CRITICAL → **rilis ditolak**;
   - ada HIGH → **perbaikan wajib sebelum rilis**;
   - ada MEDIUM → **perbaikan dijadwalkan**;
   - tidak ada temuan kritis → **hasil memuaskan**.
3. QA Manager menandatangani keputusan akhir. Tanpa `approved_by`, status dibaca **menunggu sign-off**, bukan "disetujui".
4. DOCX final adalah versi yang diverifikasi (`--verify`). Perubahan setelah verifikasi → build ulang + verify ulang.

---

## 8. Retensi & klasifikasi bukti

- Screenshot, video, log, dan DOCX mengandung data aplikasi → perlakukan sebagai **internal/rahasia**.
- Simpan di folder hasil per target; jangan commit (sudah ada di `.gitignore`).
- Kredensial tidak pernah masuk chat, spec, log runtime, DOCX, atau JSON hasil.
- **Usulan retensi:** 90 hari untuk UAT, 12 bulan untuk rilis/audit. Setelah itu arsipkan atau hapus sesuai kebijakan perusahaan.
- Akses bukti hanya untuk tim yang terlibat + auditor yang berwenang.

---

## 9. Metrik dari data nyata

Ambil langsung dari `triage.json` — jangan mengarang angka dan jangan mengklaim peningkatan efisiensi tanpa pembanding:

- `pass/fail/blocked` dari `summary.case_counts`;
- distribusi severity dari `summary.by_severity`;
- `open`, `overdue`, `reopen` dari field `defect_status`, `sla_due`, `retest_of`;
- tren dari beberapa rilis, baru ditampilkan setelah minimal 2–3 siklus data nyata.

Laporan manajemen (`build_pptx.py`) memakai angka yang sudah terverifikasi di DOCX, bukan estimate.

---

## 10. Eskalasi

| Kondisi | Eskalasi ke | Batas waktu |
|---|---|---|
| Otorisasi tidak jelas / target produksi berisiko | QA Manager + Owner | Segera, sebelum aksi |
| Temuan CRITICAL | QA Manager + Eng lead | 1 hari kerja |
| SLA terlewat | QA Manager | Hari itu juga |
| ADB/browser/DB gagal berulang | QA Lead | Setelah 2 kali recovery |
| Perubahan permanen pada data produksi terdeteksi | **Stop**, QA Manager + Owner | Segera |

---

## 11. Hubungan dengan tooling

| Kebutuhan | File |
|---|---|
| Peta tim & jalur belajar | `docs/PETA-TIM.md` |
| Panduan clone → pakai | `docs/PANDUAN-LENGKAP.md` |
| Template otorisasi | `templates/authorization.md` |
| Skema & contoh field `triage.json` | `docs/SOP-QA.md` §4–§7 + `skills/qa-e2e-tester/SKILL.md` |
| Generator DOCX + verifier | `skills/qa-e2e-tester/build_report.py`, `report_kit.py` |
| Instalasi & preflight | `scripts/setup.ps1`, `scripts/verify_setup.ps1` |
