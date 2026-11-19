# Stop the QQ bot stack (ASCII only, PowerShell 5.1 safe)
#
#   powershell -ExecutionPolicy Bypass -File stop-all.ps1
#   powershell -ExecutionPolicy Bypass -File stop-all.ps1 -KeepQQ      # keep QQ + NapCat
#   powershell -ExecutionPolicy Bypass -File stop-all.ps1 -KeepModels  # keep 8080/8083/8085/8097
#
# Everything is located by the port it listens on. Command-line matching is not
# used any more: AstrBot is started by uv and only shows "python.exe main.py", so
# regex detection silently misses it.
param(
    [switch]$KeepQQ,
    [switch]$KeepModels
)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot 'scripts\_common.ps1')
Repair-Env

if ($KeepQQ) {
    Write-Host '=== QQ + NapCat: kept ==='
} else {
    Write-Host '=== QQ + NapCat ==='
    $qq = @(Get-Process QQ -ErrorAction SilentlyContinue)
    if ($qq.Count -gt 0) {
        foreach ($p in $qq) {
            Write-Host "  QQ pid $($p.Id)"
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
        $released = $false
        for ($i = 0; $i -lt 40; $i++) {
            if (-not (Test-Port 6099)) { $released = $true; break }
            Start-Sleep -Milliseconds 300
        }
        if ($released) { Write-Host '      6099 released' } else { Write-Host '      WARN: NapCat still listening' -ForegroundColor Yellow }
    } else {
        Write-Host '      not running'
    }
}

Write-Host '=== AstrBot (6185 / 6199) ==='
if (Test-Port 6185) { Stop-Port 6185 'astrbot' | Out-Null } else { Write-Host '      not running' }

Write-Host '=== dashboard (6190) + QR page (6191) ==='
foreach ($svc in @(@{ Port = 6190; Label = 'dashboard' }, @{ Port = 6191; Label = 'qr page' })) {
    if (Test-Port $svc.Port) { Stop-Port $svc.Port $svc.Label | Out-Null }
    else { Write-Host ("      {0} not running" -f $svc.Label) }
}

Write-Host '=== caption cache (8084) + judge (8082) ==='
foreach ($svc in @(@{ Port = 8084; Label = 'caption' }, @{ Port = 8082; Label = 'judge' })) {
    if (Test-Port $svc.Port) { Stop-Port $svc.Port $svc.Label | Out-Null }
    else { Write-Host ("      {0} not running" -f $svc.Label) }
}

if ($KeepModels) {
    Write-Host '=== local models: kept ==='
} else {
    Write-Host '=== local models (8080 / 8083 / 8085 / 8097) ==='
    foreach ($svc in @(
            @{ Port = 8080; Label = 'chat model' },
            @{ Port = 8083; Label = 'ocr' },
            @{ Port = 8085; Label = 'local VL' },
            @{ Port = 8097; Label = 'embedding' })) {
        if (Test-Port $svc.Port) { Stop-Port $svc.Port $svc.Label | Out-Null }
        else { Write-Host ("      {0} not running" -f $svc.Label) }
    }
    Write-Host '=== leftover llama-server children ==='
    $left = @(Get-Process llama-server -ErrorAction SilentlyContinue)
    if ($left.Count -gt 0) {
        foreach ($p in $left) {
            Write-Host "  llama-server pid $($p.Id)"
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host '      none'
    }
}

# Anything started from the AstrBot venv that no longer owns a port (crashed
# workers, orphaned uvicorn reloads).
Write-Host '=== leftover AstrBot python processes ==='
$orphans = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath -like '*QQNTBOT\apps\AstrBot\.venv*' })
if ($orphans.Count -gt 0) {
    foreach ($p in $orphans) {
        Write-Host "  python pid $($p.ProcessId)"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host '      none'
}

Start-Sleep -Seconds 1
Write-Host '=== result ==='
$ports = @(@{ Port = 8080; Label = 'chat model' }, @{ Port = 8082; Label = 'judge' },
    @{ Port = 8083; Label = 'ocr' }, @{ Port = 8084; Label = 'caption cache' },
    @{ Port = 8085; Label = 'local VL' }, @{ Port = 8097; Label = 'embedding' },
    @{ Port = 6185; Label = 'astrbot' }, @{ Port = 6190; Label = 'dashboard' },
    @{ Port = 6191; Label = 'qr page' }, @{ Port = 6099; Label = 'napcat (kept)' })
Show-Status $ports

# Only ports we actually asked to stop count as failures.
$mustBeDown = @($ports | Where-Object {
        if ($KeepQQ -and $_.Port -eq 6099) { return $false }
        if ($KeepModels -and ($_.Port -in @(8080, 8083, 8085, 8097))) { return $false }
        return $true
    })
$still = @($mustBeDown | Where-Object { Test-Port $_.Port })
if ($still.Count -gt 0) {
    Write-Host '      waiting for sockets to close ...'
    Start-Sleep -Seconds 3
    $still = @($still | Where-Object { Test-Port $_.Port })
}
if ($still.Count -gt 0) {
    Write-Host ''
    Write-Host ("WARN: still listening: {0}" -f (($still | ForEach-Object { $_.Port }) -join ', ')) -ForegroundColor Yellow
    Write-Host '      Either the process needs administrator rights, or something restarted it' -ForegroundColor Yellow
    Write-Host '      right after the stop (check for a second start-all / supervisor).' -ForegroundColor Yellow
    exit 1
}
Write-Host ''
Write-Host 'stopped.'
exit 0
