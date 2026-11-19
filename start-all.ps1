# Start the whole QQ bot stack (ASCII only, PowerShell 5.1 safe)
# Order: router -> judge -> OCR -> AstrBot -> QQ(NapCat) -> dashboard
$ErrorActionPreference = 'Continue'

$QQNT   = 'C:\Program Files\Tencent\QQNT'
$EXPECT = '9.9.25-42905'          # patched QQ.exe + dbghelp only match this build

function Test-Port([int]$p) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue)
}
function Wait-Port([int]$p, [int]$seconds) {
    for ($i = 0; $i -lt $seconds; $i++) {
        if (Test-Port $p) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

Write-Host '=== 0/7 version guard ==='
$cfg = Get-Content (Join-Path $QQNT 'versions\config.json') -Raw | ConvertFrom-Json
if ($cfg.curVersion -ne $EXPECT) {
    Write-Host "WARN: QQNT is $($cfg.curVersion), expected $EXPECT." -ForegroundColor Yellow
    Write-Host '      The patched QQ.exe / dbghelp only work on the pinned build.' -ForegroundColor Yellow
    Write-Host '      QQ probably auto-updated. Reinstall 9.9.25 and rerun install_napcat_entry.ps1.' -ForegroundColor Yellow
} else {
    Write-Host "      QQNT $($cfg.curVersion) OK"
}

Write-Host '=== 1/7 llama.cpp router (chat model) ==='
if (Test-Port 8080) {
    Write-Host '      already up'
} else {
    Start-Process -WindowStyle Hidden -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\LLM\scripts\start-router.ps1')
    if (Wait-Port 8080 120) { Write-Host '      ready' } else { Write-Host '      WARN: not ready yet' }
}

Write-Host '=== 2/7 tiny judge model (CPU) ==='
if (Test-Port 8082) {
    Write-Host '      already up'
} else {
    Start-Process -WindowStyle Hidden -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\QQNTBOT\scripts\start-judge.ps1')
    if (Wait-Port 8082 90) { Write-Host '      ready' } else { Write-Host '      WARN: not ready (group auto-reply falls back to probability)' }
}

Write-Host '=== 3/7 OCR server + caption cache + local VL (image reading) ==='
if (Test-Port 8083) {
    Write-Host '      ocr already up'
} else {
    Start-Process -WindowStyle Hidden -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\QQNTBOT\scripts\start-ocr.ps1')
    if (Wait-Port 8083 120) { Write-Host '      ocr ready' } else { Write-Host '      WARN: OCR not up, images will be ignored' }
}
if (Test-Port 8085) {
    Write-Host '      local VL already up'
} else {
    Start-Process -WindowStyle Hidden -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\QQNTBOT\scripts\start-vl.ps1')
    if (Wait-Port 8085 180) { Write-Host '      local VL ready' } else { Write-Host '      WARN: VL not up, local image reading unavailable' }
}
if (Test-Port 8084) {
    Write-Host '      caption cache already up'
} else {
    Start-Process -WindowStyle Hidden -WorkingDirectory 'D:\QQNTBOT\caption_proxy' `
        -FilePath 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe' `
        -ArgumentList @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8084')
    if (Wait-Port 8084 40) { Write-Host '      caption cache ready' } else { Write-Host '      WARN: caption cache not up' }
}

Write-Host '=== 4/7 AstrBot ==='
if (Test-Port 6185) {
    Write-Host '      already up'
} else {
    Start-Process -WindowStyle Hidden -WorkingDirectory 'D:\QQNTBOT\apps\AstrBot' `
        -FilePath 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe' -ArgumentList 'main.py'
    if (Wait-Port 6185 120) { Write-Host '      ready' } else { Write-Host '      WARN: not ready yet' }
}

Write-Host '=== 5/7 QQ + NapCat ==='
if (Get-Process QQ -ErrorAction SilentlyContinue) {
    Write-Host '      QQ already running'
} else {
    Start-Process -FilePath (Join-Path $QQNT 'QQ.exe') -WorkingDirectory $QQNT
    if (Wait-Port 6099 120) { Write-Host '      NapCat webui ready' } else { Write-Host '      WARN: 6099 not up' }

    # 实时二维码服务：从 NapCat API 现取现画，不会过期
    Start-Sleep -Seconds 6
    if (-not (Test-Port 6191)) {
        Start-Process -WindowStyle Hidden -FilePath 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe' `
            -ArgumentList @('D:\QQNTBOT\scripts\qq_qr_server.py') `
            -RedirectStandardOutput 'D:\QQNTBOT\_backup\qr.out' `
            -RedirectStandardError 'D:\QQNTBOT\_backup\qr.err'
        Start-Sleep -Seconds 3
    }
    Write-Host '      QR page: http://127.0.0.1:6191/ （需要扫码时打开）'
    Start-Process 'http://127.0.0.1:6191/'
}

Write-Host '=== 6/7 dashboard ==='
if (Test-Port 6190) {
    Write-Host '      already up'
} else {
    Start-Process -WindowStyle Hidden -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\QQNTBOT\scripts\start-dashboard.ps1')
    if (Wait-Port 6190 40) { Write-Host '      ready' } else { Write-Host '      WARN: dashboard not up' }
}
Start-Process 'http://127.0.0.1:6190'
Write-Host '      dashboard opened in browser'

Write-Host ''
Write-Host 'stack is up:'
Write-Host '  dashboard http://127.0.0.1:6190'
Write-Host '  model     http://127.0.0.1:8080'
Write-Host '  judge     http://127.0.0.1:8082'
Write-Host '  ocr       http://127.0.0.1:8083'
Write-Host '  astrbot   http://127.0.0.1:6185  (astrbot / qqbot2026)'
Write-Host '  napcat    http://127.0.0.1:6099'
Write-Host '  memory    D:\QQNTBOT\data\memory.db'
