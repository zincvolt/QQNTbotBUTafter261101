# Start the whole QQ bot stack (ASCII only, PowerShell 5.1 safe)
#
#   powershell -ExecutionPolicy Bypass -File start-all.ps1
#   powershell -ExecutionPolicy Bypass -File start-all.ps1 -ThirdParty   # skip 8080/8083/8085
#   powershell -ExecutionPolicy Bypass -File start-all.ps1 -Local        # force local models
#   powershell -ExecutionPolicy Bypass -File start-all.ps1 -NoBrowser    # do not open pages
#   powershell -ExecutionPolicy Bypass -File start-all.ps1 -NoDetach     # keep children in this shell
#
# Mode is read from AstrBot agent_runner.config.model.provider_id (the only
# source of truth). Third-party mode does not start the 9B / OCR / VL servers,
# which saves ~14 GB of RAM. Nothing is ever stopped here, only started.
#
# By default every service is launched through WMI, so it does NOT belong to the
# job object of this shell: closing the terminal window leaves the bot running.
# Use -NoDetach if WMI is unavailable on the machine.
param(
    [switch]$Local,
    [switch]$ThirdParty,
    [switch]$NoBrowser,
    [switch]$NoDetach
)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot 'scripts\_common.ps1')
Repair-Env
$global:BotDetach = -not $NoDetach

$QQNT   = 'C:\Program Files\Tencent\QQNT'
$EXPECT = '9.9.25-42905'          # patched QQ.exe + dbghelp only match this build

Write-Host '=== 0/7 version guard ==='
$cfgPath = Join-Path $QQNT 'versions\config.json'
if (Test-Path $cfgPath) {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
    if ($cfg.curVersion -ne $EXPECT) {
        Write-Host "WARN: QQNT is $($cfg.curVersion), expected $EXPECT." -ForegroundColor Yellow
        Write-Host '      The patched QQ.exe / dbghelp only work on the pinned build.' -ForegroundColor Yellow
        Write-Host '      QQ probably auto-updated. Reinstall 9.9.25 and rerun install_napcat_entry.ps1.' -ForegroundColor Yellow
    } else {
        Write-Host "      QQNT $($cfg.curVersion) OK"
    }
} else {
    Write-Host "WARN: $cfgPath not found, skipping the version guard" -ForegroundColor Yellow
}

Write-Host '=== 1/7 mode ==='
$provider   = Get-ProviderId
$thirdMode  = Test-ThirdPartyAstrBot $provider
if ($Local) { $thirdMode = $false }
if ($ThirdParty) { $thirdMode = $true }
if (-not $provider) {
    Write-Host '      WARN: provider_id not readable, assuming local mode' -ForegroundColor Yellow
}
if ($thirdMode) {
    Write-Host "      provider=$provider -> third-party: 8080/8083/8085 will NOT start"
    if ($provider -and -not (Test-ThirdPartyAstrBot $provider)) {
        Write-Host '      NOTE: AstrBot still points at a local provider and was started on request.' -ForegroundColor Yellow
        Write-Host '            To really run third-party, switch the model in QQ first (docs\THIRD-PARTY-API.md).' -ForegroundColor Yellow
    }
} else {
    Write-Host "      provider=$provider -> local: 8080/8083/8085 will start (~14 GB)"
    if ($provider -and (Test-ThirdPartyAstrBot $provider)) {
        Write-Host '      NOTE: AstrBot points at a third-party provider, so the local models are unused.' -ForegroundColor Yellow
        Write-Host '            Switch back in QQ first, or start with -ThirdParty to skip them.' -ForegroundColor Yellow
    }
}

if ($thirdMode) {
    Write-Host '=== 2/7 local models: skipped (third-party mode) ==='
} else {
    Write-Host '=== 2/7 local models: chat / ocr / VL ==='
    Start-ScriptService -Port 8080 -Label 'chat model' -ScriptPath 'D:\LLM\scripts\start-router.ps1' -Timeout 180 | Out-Null
    Start-ScriptService -Port 8083 -Label 'ocr'        -ScriptPath 'D:\QQNTBOT\scripts\start-ocr.ps1'  -Timeout 150 | Out-Null
    Start-ScriptService -Port 8085 -Label 'local VL'   -ScriptPath 'D:\QQNTBOT\scripts\start-vl.ps1'   -Timeout 240 | Out-Null
}

Write-Host '=== 3/7 judge (8082) + embedding (8097) + caption cache (8084) ==='
Start-ScriptService -Port 8082 -Label 'judge' -ScriptPath 'D:\QQNTBOT\scripts\start-judge.ps1' -Timeout 120 | Out-Null
Start-PythonService -Port 8097 -Label 'embedding' `
    -Python 'D:\LLM\tts\venv\Scripts\python.exe' `
    -Arguments @('D:\LLM\scripts\embed-npu-server.py') `
    -OutLog 'D:\LLM\logs\embed.out' -ErrLog 'D:\LLM\logs\embed.err' -Timeout 90 | Out-Null
Start-PythonService -Port 8084 -Label 'caption cache' -Python $BotPython `
    -Arguments @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8084') `
    -WorkingDirectory 'D:\QQNTBOT\caption_proxy' -Timeout 40 | Out-Null

Write-Host '=== 4/7 AstrBot (6185) ==='
Start-PythonService -Port 6185 -Label 'astrbot' -Python $BotPython `
    -Arguments @('main.py') -WorkingDirectory 'D:\QQNTBOT\apps\AstrBot' -Timeout 120 | Out-Null

Write-Host '=== 5/7 QQ + NapCat ==='
if (Get-Process QQ -ErrorAction SilentlyContinue) {
    Write-Host '      QQ already running'
} else {
    if (Test-Path (Join-Path $QQNT 'QQ.exe')) {
        if ($global:BotDetach) {
            Start-Detached -FilePath (Join-Path $QQNT 'QQ.exe') -WorkingDirectory $QQNT | Out-Null
        } else {
            Start-Hidden -FilePath (Join-Path $QQNT 'QQ.exe') -WorkingDirectory $QQNT | Out-Null
        }
        if (Wait-Port 6099 120) { Write-Host '      NapCat webui ready' } else { Write-Host '      WARN: 6099 not up' -ForegroundColor Yellow }
    } else {
        Write-Host "      WARN: QQ.exe missing under $QQNT" -ForegroundColor Yellow
    }
}
# Live QR page: renders the current NapCat login QR on demand, never stale.
Start-PythonService -Port 6191 -Label 'QR page' -Python $BotPython `
    -Arguments @('D:\QQNTBOT\scripts\qq_qr_server.py') `
    -OutLog 'D:\QQNTBOT\_backup\qr.out' -ErrLog 'D:\QQNTBOT\_backup\qr.err' -Timeout 20 | Out-Null
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:6191/' }

Write-Host '=== 6/7 dashboard (6190) ==='
Start-ScriptService -Port 6190 -Label 'dashboard' -ScriptPath 'D:\QQNTBOT\scripts\start-dashboard.ps1' -Timeout 40 | Out-Null
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:6190' }

# 外部看门狗：AstrBot 挂了也能经 NapCat HTTP(6198) 私信报信（无端口，静默常驻）
Start-Process -WindowStyle Hidden -FilePath $BotPython `
    -ArgumentList @('D:\QQNTBOT\scripts\watchdog.py') `
    -RedirectStandardOutput 'D:\QQNTBOT\_backup\watchdog.out' `
    -RedirectStandardError 'D:\QQNTBOT\_backup\watchdog.err'

Write-Host '=== 7/7 summary ==='
Show-Status @(
    @{ Port = 6190; Label = 'dashboard  http://127.0.0.1:6190' },
    @{ Port = 6185; Label = 'astrbot    http://127.0.0.1:6185  (astrbot / qqbot2026)' },
    @{ Port = 6199; Label = 'onebot ws  ws://127.0.0.1:6199' },
    @{ Port = 6099; Label = 'napcat     http://127.0.0.1:6099' },
    @{ Port = 6191; Label = 'QR page    http://127.0.0.1:6191' },
    @{ Port = 8080; Label = 'chat model (local mode only)' },
    @{ Port = 8082; Label = 'judge' },
    @{ Port = 8083; Label = 'ocr      (local mode only)' },
    @{ Port = 8084; Label = 'caption cache' },
    @{ Port = 8085; Label = 'local VL (local mode only)' },
    @{ Port = 8097; Label = 'embedding  (RAG)' }
)
Write-Host ''
Write-Host "mode: $(if ($thirdMode) { 'third-party' } else { 'local' })   launch: $(if ($global:BotDetach) { 'detached (survives terminal close)' } else { 'attached' })"
Write-Host "memory: D:\QQNTBOT\data\memory.db"
