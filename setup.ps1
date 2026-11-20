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

# 2. Skill: nama folder = ID skill, jangan diubah
foreach ($id in 'qa-e2e-tester', 'bug-hunter', 'sp-tracer') {
    $src = Join-Path (Join-Path $repo 'skills') $id
    $dst = Join-Path $skillsDst $id
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Get-ChildItem $src -Force |
        Where-Object { $_.Name -notin '.git', '__pycache__' } |
        Copy-Item -Destination $dst -Recurse -Force
}

# 3. Template kredensial (hanya dibuat bila belum ada)
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
