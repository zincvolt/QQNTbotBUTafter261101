# Restart only the AstrBot main process (keeps QQ, judge and dashboard alive).
# ~10 s, QQ never disconnects.
#
#   powershell -ExecutionPolicy Bypass -File scripts\restart-astrbot.ps1
#   ... -NoDetach    keep AstrBot inside this shell (default is detached)
#
# The process is located by the port it listens on (6185), not by its command
# line: an AstrBot started through uv only shows "python.exe main.py", so the old
# regex match missed it and the restart silently did nothing.
param([switch]$NoDetach)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_common.ps1')
Repair-Env
$global:BotDetach = -not $NoDetach

if (Test-Port 6185) {
    Stop-Port 6185 'astrbot' | Out-Null
} else {
    Write-Host 'AstrBot was not running, starting it'
}

Start-Sleep -Seconds 1

if ($global:BotDetach) {
    Start-Detached -FilePath $BotPython -ArgumentList @('main.py') `
        -WorkingDirectory 'D:\QQNTBOT\apps\AstrBot' | Out-Null
} else {
    Start-Hidden -FilePath $BotPython -ArgumentList @('main.py') `
        -WorkingDirectory 'D:\QQNTBOT\apps\AstrBot' | Out-Null
}

if (Wait-Port 6185 90) {
    Write-Host 'AstrBot restarted on 6185'
    exit 0
}

Write-Host 'WARN: AstrBot did not come back, last log lines:' -ForegroundColor Yellow
$log = Get-ChildItem 'D:\QQNTBOT\apps\AstrBot\data\logs' -Filter '*.log' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($log) {
    Write-Host ("  ({0})" -f $log.Name)
    Get-Content $log.FullName -Tail 20
}
exit 1
