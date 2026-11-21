# Panduan Penggunaan & Instalasi `bug-hunter`

Skill ini adalah **Autonomous Bug Hunter & Vulnerability Assessor** untuk Web dan Android APK yang berjalan langsung di Antigravity / Opencode.

Setup lengkap tim (Python, Playwright, AVD/MuMu, kredensial DB, dan preflight) ada di `PANDUAN-LENGKAP.md` di root repo.

---

## 1. Persyaratan Lingkungan

- **Python 3.10+** dengan modul `python-docx`:
  ```bash
  pip install python-docx
  ```
- **Playwright** (untuk target Web):
  Tersedia langsung melalui tool browser Playwright bawaan Antigravity / Code Mode.
- **ADB & MuMu Player** (untuk target Android APK):
  - MuMu Player aktif (default ADB port `127.0.0.1:16384` atau terdeteksi lewat `mumu-cli`).
  - ADB tersedia di PATH sistem.

---

## 2. Cara Menjalankan

Cukup berikan perintah di chat:

### A. Target Web
```bash
hunt web https://target-domain.com/
```
Atau cukup:
```bash
hunt https://target-domain.com/
```

### B. Target Android APK
```bash
hunt apk app-release.apk
```
Atau langsung ke package yang sudah terinstal di emulator:
```bash
hunt apk com.target.app
```

### C. Target Hybrid (Web + APK)
```bash
hunt all https://target-domain.com/ app-release.apk
```

---

## 3. Fitur Utama

1. **Recon Otomatis**:
   - Pemetaan endpoint, analisa header keamanan, dan secret scan di JS / APK strings.
2. **Asesmen Kerentanan Non-Destruktif**:
   - Deteksi celah akses kontrol, miskonfigurasi keamanan, dan kebocoran informasi sensitif.
3. **Chaos & Monkey Testing Otomatis**:
   - Fuzzing input batas ekstrem dan stres UI acak via Monkey testing.
4. **Pembersihan Jejak Terverifikasi (Auto-Cleanup)**:
   - Pembersihan otomatis cookies, local storage, data dummy, dan file temporer device pasca pengujian. Status dilaporkan sebagai `VERIFIED` atau `PARTIAL`.
5. **Satu Laporan Terpadu (.docx)**:
   - Laporan siap submit dengan tabel PoC langkah-demi-langkah, skor CVSS v3.1, dan screenshot bukti visual tertanam.
   - Mengikuti **Zero Redaction Policy**: data riil yang ada di artefak tampil apa adanya, data yang tidak ada ditulis `(...)`.
