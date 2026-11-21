# Preflight instalasi QA Team.
# Hanya mengecek keberadaan/versi. TIDAK pernah membaca atau menampilkan isi kredensial.
$ErrorActionPreference = 'Continue'

$oc = Join-Path $env:USERPROFILE '.config\opencode'
$expectedAgents = @('qa-lead', 'qa-web-engineer', 'qa-mobile-engineer', 'bug-hunter', 'sp-specialist')
$expectedSkills = @('qa-e2e-tester', 'qa-web-e2e', 'qa-mobile-e2e', 'firerpa-eval', 'bug-hunter', 'sp-tracer')
$modules = [ordered]@{
    docx      = 'python-docx'
    PIL       = 'pillow'
    pyodbc    = 'pyodbc'
    playwright = 'playwright'
    openpyxl  = 'openpyxl'
}

function Show-Line([string]$status, [string]$label, [string]$detail) {
    '{0,-6} {1,-26} {2}' -f $status, $label, $detail
}

Write-Host ''
Write-Host '=== QA TEAM - PREFLIGHT ==='
Write-Host ''

# 1. OpenCode CLI
$ocCmd = Get-Command opencode -ErrorAction SilentlyContinue
if ($ocCmd) { Show-Line '[OK]' 'opencode CLI' $ocCmd.Source }
else { Show-Line '[WARN]' 'opencode CLI' 'tidak ditemukan di PATH' }

# 2. Python
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Show-Line '[WARN]' 'python' 'tidak ditemukan di PATH'
} else {
    $ver = & python -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
    if ($LASTEXITCODE -eq 0 -and [double]$ver -ge 3.10) {
        Show-Line '[OK]' 'python' "v$ver"
    } else {
        Show-Line '[WARN]' 'python' "v$ver - butuh 3.10+"
    }
}

# 3. Modul Python
foreach ($name in $modules.Keys) {
    $null = & python -c "import $name" 2>$null
    if ($LASTEXITCODE -eq 0) { Show-Line '[OK]' $modules[$name] 'terpasang' }
    else { Show-Line '[WARN]' $modules[$name] 'belum terpasang' }
}

# 4. Chromium Playwright
$pwRoot = Join-Path $env:LOCALAPPDATA 'ms-playwright'
$chromium = @()
if (Test-Path $pwRoot) {
    $chromium = @(Get-ChildItem $pwRoot -Directory -Filter 'chromium-*' -ErrorAction SilentlyContinue)
}
if ($chromium.Count -gt 0) { Show-Line '[OK]' 'playwright chromium' "$($chromium.Count) installment ditemukan" }
else { Show-Line '[WARN]' 'playwright chromium' 'jalankan: python -m playwright install chromium' }

# 5. Agent terpasang
$agentsOk = 0
foreach ($a in $expectedAgents) {
    if (Test-Path (Join-Path $oc "agents\$a.md")) { $agentsOk++ }
    else { Show-Line '[WARN]' "agent $a" 'belum ada - jalankan setup.ps1' }
}
if ($agentsOk -eq $expectedAgents.Count) { Show-Line '[OK]' 'agent' "$agentsOk/$($expectedAgents.Count) terpasang" }

# 6. Skill terpasang
$skillsOk = 0
foreach ($s in $expectedSkills) {
    if (Test-Path (Join-Path $oc "skills\$s\SKILL.md")) { $skillsOk++ }
    else { Show-Line '[WARN]' "skill $s" 'belum ada - jalankan setup.ps1' }
}
if ($skillsOk -eq $expectedSkills.Count) { Show-Line '[OK]' 'skill' "$skillsOk/$($expectedSkills.Count) terpasang" }

# 6b. Skrip bersama hasil salinan setup.ps1 (repo menyimpan satu salinan saja)
$scriptMap = [ordered]@{
    'qa-e2e-tester' = @('build_report.py', 'report_kit.py', 'db_verify.py', 'find_notif.py', 'qa-credentials.example.json')
    'bug-hunter'    = @('build_report.py', 'report_kit.py', 'db_verify.py', 'find_notif.py', 'qa-credentials.example.json')
    'sp-tracer'     = @('db_verify.py', 'find_notif.py', 'qa-credentials.example.json')
}
$scriptOk = 0
$scriptTotal = 0
foreach ($s in $scriptMap.Keys) {
    foreach ($f in $scriptMap[$s]) {
        $scriptTotal++
        if (Test-Path (Join-Path $oc "skills\$s\$f")) { $scriptOk++ }
        else { Show-Line '[WARN]' "skill $s / $f" 'belum ada - jalankan setup.ps1 ulang' }
    }
}
if ($scriptOk -eq $scriptTotal) { Show-Line '[OK]' 'skrip skill' "$scriptOk/$scriptTotal tersedia" }

# 7. File kredensial lokal (isi TIDAK dibaca)
$cred = Join-Path $oc 'qa-credentials.local.json'
if (Test-Path $cred) { Show-Line '[OK]' 'qa-credentials.local.json' 'ada (isi tidak dicek)' }
else { Show-Line '[WARN]' 'qa-credentials.local.json' 'belum ada - jalankan setup.ps1' }

# 8. ADB / device
$adb = ''
if ($env:ANDROID_HOME -and (Test-Path (Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe'))) {
    $adb = Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe'
}
$mumuAdb = 'C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe'
if (-not $adb -and (Test-Path $mumuAdb)) { $adb = $mumuAdb }
if ($adb) {
    $out = & $adb devices 2>$null
    $devices = @($out | Where-Object { $_ -match '\tdevice\s*$' })
    if ($devices.Count -gt 0) { Show-Line '[OK]' 'adb devices' ($devices -join '; ') }
    else { Show-Line '[INFO]' 'adb devices' "adb ada, belum ada device - siapkan AVD/MuMu ($adb)" }
} else {
    Show-Line '[INFO]' 'adb' 'tidak ditemukan - perlu untuk E2E mobile'
}

Write-Host ''
Write-Host '=== LANGKAH BERIKUTNYA ==='
Write-Host '1. opencode reload, lalu cek dari folder workspace:'
Write-Host '   opencode api get /api/agent'
Write-Host '   opencode api get /api/skill'
Write-Host '2. Isi %USERPROFILE%\.config\opencode\qa-credentials.local.json bila mau pakai DB'
Write-Host '   (jangan pernah isi password di chat atau di qa-credentials.example.json)'
Write-Host '3. Siapkan .env.qa di workspace untuk target/akun uji web & mobile'
Write-Host '4. Baca PANDUAN-LENGKAP.md untuk prosedur web, mobile, DB, dan bug hunt'
Write-Host ''
