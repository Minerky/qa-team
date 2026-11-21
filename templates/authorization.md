# Otorisasi Pengujian — SALIN & ISI

> Salin file ini ke folder workspace per project, mis. `authorization-Wisesa-2026-11.md`.
> Isi semua `(...)`. **Kosong = `BLOCKED`** — jangan jalankan pengujian keamanan atau aksi yang mengubah state.
> Jangan taruh password di sini. File ini boleh di-commit bila tidak berisi rahasia.

---

## 1. Identitas

| Field | Nilai |
|---|---|
| Nama pengujian / project | `(...)` |
| Referensi otorisasi (nomor tiket/email/DO) | `(...)` |
| Tanggal dibuat | `(...)` |
| Berlaku sampai | `(...)` |

## 2. Target & scope

| Field | Nilai |
|---|---|
| URL / host / IP / CIDR | `(...)` |
| APK / package / activity | `(...)` |
| Database / instance yang boleh dibaca | `(...)` |
| Environment | `staging` / `UAT` / `produksi` — **(...)…** |
| Fitur / modul yang diuji | `(...)` |
| Akun uji & role (tanpa password) | `(...)` |

**Di luar scope (dilarang disentuh):** `(...)`

## 3. Penanggung jawab

| Peran | Nama | Tanda tangan / persetujuan |
|---|---|---|
| Owner sistem / product | `(...)` | `(...)` |
| QA Manager | `(...)` | `(...)` |
| QA Lead (pelaksana) | `(...)` | `(...)` |
| Eng / ops (rollback) | `(...)` | `(...)` |

## 4. Metode yang diizinkan

- [ ] Probe pasif / ringan (header, DNS, banner, fingerprint)
- [ ] E2E fungsional web / mobile (staging/UAT)
- [ ] Verifikasi database **read-only** (`SELECT` / `WITH` / `PRAGMA`, satu statement)
- [ ] Baca definisi stored procedure lewat katalog — **tanpa `EXEC`**
- [ ] Payload injeksi non-destruktif (XSS/SQLi/path traversal detection-only)
- [ ] OWASP ZAP baseline pada scope yang disetujui
- [ ] MITM / proxy pada UAT (butuh persetujuan terpisah + backup)
- [ ] Frida / root / device farm (butuh persetujuan terpisah)

**Yang dilarang:** exploit destruktif, DDoS, defacement, penghapusan data produksi, pivot ke host di luar scope, password spraying, eksploitasi aktif tanpa backup/rollback.

## 5. Jendela & kontrol

| Field | Nilai |
|---|---|
| Jendela waktu eksekusi | `(...)` |
| Backup / rollback tersedia | `YA` / `TIDAK` — bukti: `(...)` |
| Data uji bisa di-reset | `YA` / `TIDAK` — caranya: `(...)` |
| Cleanup yang disetujui | `(...)` |

## 6. Eskalasi

| Kondisi | Kontak | Waktu respons |
|---|---|---|
| Temuan CRITICAL | `(...)` | 1 hari kerja |
| Risiko perubahan permanen produksi | `(...)` | **Stop** + lapor segera |
| SLA terlewat | `(...)` | Hari itu juga |

## 7. Catatan di laporan

Masukkan referensi dokumen ini ke `triage.json`:

```json
"governance": {
  "authorization": {
    "ref": "<nomor dari field 1>",
    "scope": "<ringkasan field 2>",
    "approved_by": "<nama penandatangan>",
    "date": "<tanggal>",
    "valid_until": "<tanggal>"
  }
}
```

Generator akan menampilkannya di Bab **Kesimpulan & Rekomendasi Akhir**.
