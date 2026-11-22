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
# Always started regardless of mode: judge (8082), embedding (8097), caption
# cache (8084), STT whisper on NPU (8096) and SearXNG in Docker (9000) - the
# bot loses voice input / web search when any of them is missing.
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

Write-Host '=== version guard ==='
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

Write-Host '=== mode ==='
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
    Write-Host '=== local models: skipped (third-party mode) ==='
} else {
    Write-Host '=== local models: chat / ocr / VL ==='
    Start-ScriptService -Port 8080 -Label 'chat model' -ScriptPath 'D:\LLM\scripts\start-router.ps1' -Timeout 180 | Out-Null
    Start-ScriptService -Port 8083 -Label 'ocr'        -ScriptPath 'D:\QQNTBOT\scripts\start-ocr.ps1'  -Timeout 150 | Out-Null
    Start-ScriptService -Port 8085 -Label 'local VL'   -ScriptPath 'D:\QQNTBOT\scripts\start-vl.ps1'   -Timeout 240 | Out-Null
}

Write-Host '=== judge (8082) + embedding (8097) + caption cache (8084) ==='
Start-ScriptService -Port 8082 -Label 'judge' -ScriptPath 'D:\QQNTBOT\scripts\start-judge.ps1' -Timeout 120 | Out-Null
Start-PythonService -Port 8097 -Label 'embedding' `
    -Python 'D:\LLM\tts\venv\Scripts\python.exe' `
    -Arguments @('D:\LLM\scripts\embed-npu-server.py') `
    -OutLog 'D:\LLM\logs\embed.out' -ErrLog 'D:\LLM\logs\embed.err' -Timeout 90 | Out-Null
Start-PythonService -Port 8084 -Label 'caption cache' -Python $BotPython `
    -Arguments @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8084') `
    -WorkingDirectory 'D:\QQNTBOT\caption_proxy' -Timeout 40 | Out-Null

Write-Host '=== AstrBot (6185) ==='
Start-PythonService -Port 6185 -Label 'astrbot' -Python $BotPython `
    -Arguments @('main.py') -WorkingDirectory 'D:\QQNTBOT\apps\AstrBot' -Timeout 120 | Out-Null

Write-Host '=== QQ + NapCat ==='
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

Write-Host '=== dashboard (6190) ==='
Start-ScriptService -Port 6190 -Label 'dashboard' -ScriptPath 'D:\QQNTBOT\scripts\start-dashboard.ps1' -Timeout 40 | Out-Null
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:6190' }

Write-Host '=== stt (8096) + searxng (9000) ==='
# 语音识别：OpenVINO Whisper on NPU，AstrBot 的 stt-local provider 指向这里。
# 首次启动要编译模型（约 45-60 秒），之后走缓存；慢了就会让语音消息转写失败。
# 用 cmd 包一层只为拿重定向：WMI 分离启动本身不能重定向，而 whisper 的
# 加载进度和报错全在 stdout，没有日志就等于没法排查。
if (Test-Port 8096) {
    Write-Host '      stt already up (8096)'
} elseif (-not (Test-Path 'D:\LLM\tts\venv\Scripts\python.exe')) {
    Write-Host '      WARN: stt python missing under D:\LLM\tts\venv' -ForegroundColor Yellow
} else {
    $sttCmd = '"D:\LLM\tts\venv\Scripts\python.exe" "D:\LLM\scripts\stt-npu-server.py" ' +
        '>> "D:\LLM\logs\stt-npu.out" 2>> "D:\LLM\logs\stt-npu.err"'
    if ($global:BotDetach) {
        Start-Detached -FilePath 'cmd.exe' -ArgumentList @('/c', $sttCmd) | Out-Null
    } else {
        Start-Hidden -FilePath 'cmd.exe' -ArgumentList @('/c', $sttCmd) | Out-Null
    }
    if (Wait-Port 8096 180) { Write-Host '      stt (whisper/NPU) ready (8096)' }
    else { Write-Host '      WARN: stt not up in 180s, see D:\LLM\logs\stt-npu.err' -ForegroundColor Yellow }
}

# 搜索：SearXNG 在 Docker 里（容器 restart=unless-stopped，但 Docker Desktop
# 没起来时容器不会自己出现），端口没通就按容器名拉起来。
if (Test-Port 9000) {
    Write-Host '      searxng already up (9000)'
} elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    $names = @(& docker ps -a --format '{{.Names}}' 2>$null |
        ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($names -contains 'searxng') {
        & docker start searxng 2>&1 | Out-Null
        if (Wait-Port 9000 45) { Write-Host '      searxng ready (9000)' }
        else { Write-Host '      WARN: searxng did not come up - is Docker Desktop running?' -ForegroundColor Yellow }
    } else {
        Write-Host '      WARN: no searxng container found (create it once with docker run)' -ForegroundColor Yellow
    }
} else {
    Write-Host '      WARN: docker not found, searxng skipped' -ForegroundColor Yellow
}

# 外部看门狗：AstrBot 挂了也能经 NapCat HTTP(6198) 私信报信（无端口，静默常驻）
Start-Process -WindowStyle Hidden -FilePath $BotPython `
    -ArgumentList @('D:\QQNTBOT\scripts\watchdog.py') `
    -RedirectStandardOutput 'D:\QQNTBOT\_backup\watchdog.out' `
    -RedirectStandardError 'D:\QQNTBOT\_backup\watchdog.err'

Write-Host '=== summary ==='
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
    @{ Port = 8096; Label = 'stt        whisper (NPU)' },
    @{ Port = 8097; Label = 'embedding  (RAG)' },
    @{ Port = 9000; Label = 'searxng    web search (docker)' }
)
Write-Host ''
Write-Host "mode: $(if ($thirdMode) { 'third-party' } else { 'local' })   launch: $(if ($global:BotDetach) { 'detached (survives terminal close)' } else { 'attached' })"
Write-Host "memory: D:\QQNTBOT\data\memory.db"
