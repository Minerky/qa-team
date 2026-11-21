# Pasang agent + skill QA dari repo ini ke instalasi OpenCode lokal.
# Jalankan dari mana saja:  powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$oc = Join-Path $env:USERPROFILE '.config\opencode'
$agentsDst = Join-Path $oc 'agents'
$skillsDst = Join-Path $oc 'skills'

New-Item -ItemType Directory -Force -Path $agentsDst, $skillsDst | Out-Null

# 1. Agent: file .md harus langsung di root folder agents
Get-ChildItem (Join-Path $repo 'agents') -Filter *.md | ForEach-Object {
    Copy-Item $_.FullName -Destination (Join-Path $agentsDst $_.Name) -Force
}

# 1b. Agent lama yang sudah diganti dua spesialis E2E. Hapus hanya nama ini.
$retiredAgent = Join-Path $agentsDst 'qa-engineer.md'
if (Test-Path $retiredAgent) {
    Remove-Item $retiredAgent -Force
    Write-Host "Dihapus (digantikan): $retiredAgent"
}

# 2. Skill: nama folder = ID skill, jangan diubah
# Skrip yang dipakai bersama disimpan SATU kali di repo:
#   - skills/qa-e2e-tester/  -> build_report.py, db_verify.py, find_notif.py
#   - root repo              -> qa-credentials.example.json
# Di sini skrip itu disalin ke folder skill pemakainya karena SKILL.md
# memanggilnya dengan nama relatif di dalam folder skill itu sendiri.
$core = Join-Path (Join-Path $repo 'skills') 'qa-e2e-tester'
$credTemplate = Join-Path $repo 'qa-credentials.example.json'

foreach ($id in 'qa-e2e-tester', 'qa-web-e2e', 'qa-mobile-e2e', 'firerpa-eval', 'bug-hunter', 'sp-tracer') {
    $src = Join-Path (Join-Path $repo 'skills') $id
    $dst = Join-Path $skillsDst $id
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Get-ChildItem $src -Force |
        Where-Object { $_.Name -notin '.git', '__pycache__' } |
        Copy-Item -Destination $dst -Recurse -Force

    # Salinan lama dari file yang sudah dihapus di repo - buang dari instalasi.
    foreach ($retired in 'CARA_INSTALL.md', '.gitignore') {
        $old = Join-Path $dst $retired
        if (Test-Path $old) { Remove-Item $old -Force }
    }

    $fromCore = @()
    if ($id -eq 'bug-hunter') { $fromCore = @('build_report.py', 'db_verify.py', 'find_notif.py') }
    elseif ($id -eq 'sp-tracer') { $fromCore = @('db_verify.py', 'find_notif.py') }
    foreach ($f in $fromCore) {
        Copy-Item (Join-Path $core $f) -Destination (Join-Path $dst $f) -Force
    }

    if ($id -in 'qa-e2e-tester', 'bug-hunter', 'sp-tracer') {
        Copy-Item $credTemplate -Destination (Join-Path $dst 'qa-credentials.example.json') -Force
    }
}

# 3. Dokumen tata kelola ikut terpasang supaya bisa dibaca agent dari ~/.config/opencode
Copy-Item (Join-Path $repo 'SOP-QA.md') -Destination (Join-Path $oc 'SOP-QA.md') -Force
$tplDst = Join-Path $oc 'templates'
New-Item -ItemType Directory -Force -Path $tplDst | Out-Null
Copy-Item (Join-Path $repo 'templates\authorization.md') -Destination $tplDst -Force

# 4. Template kredensial (hanya dibuat bila belum ada)
$example = Join-Path $repo 'qa-credentials.example.json'
$local = Join-Path $oc 'qa-credentials.local.json'
if (-not (Test-Path $local)) {
    Copy-Item $example $local
    Write-Host "Dibuat: $local"
    Write-Host "Isi blok 'db' sebelum memakai koneksi database."
}

Write-Host ''
Write-Host 'SELESAI. Agent dan skill sudah terpasang.'
Write-Host 'Jalankan: opencode reload'
Write-Host 'Lalu panggil: @qa-lead'
