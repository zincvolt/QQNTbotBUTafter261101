# Start the bot dashboard on 127.0.0.1:6190 (ASCII only)
#
#   powershell -ExecutionPolicy Bypass -File scripts\start-dashboard.ps1
#   ... -NoDetach   keep uvicorn inside this shell (default is detached)
#
# Detached by default: the uvicorn child is created through WMI, so closing the
# terminal window does not kill the dashboard.
param([switch]$NoDetach)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_common.ps1')
Repair-Env
$global:BotDetach = -not $NoDetach

if (Test-Port 6190) {
    Write-Host 'dashboard already running on 6190'
    exit 0
}

$uvicornArgs = @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '6190')
if ($global:BotDetach) {
    Start-Detached -FilePath $BotPython -ArgumentList $uvicornArgs `
        -WorkingDirectory 'D:\QQNTBOT\dashboard' | Out-Null
} else {
    Start-Hidden -FilePath $BotPython -ArgumentList $uvicornArgs `
        -WorkingDirectory 'D:\QQNTBOT\dashboard' | Out-Null
}

if (Wait-Port 6190 30) {
    Write-Host 'dashboard ready: http://127.0.0.1:6190'
    exit 0
}
Write-Host 'WARN: dashboard did not start'
exit 1
