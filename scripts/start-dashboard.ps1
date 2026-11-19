# Start the bot dashboard on 127.0.0.1:6190 (ASCII only)
$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_common.ps1')
Repair-Env

if (Test-Port 6190) {
    Write-Host 'dashboard already running on 6190'
    exit 0
}

Start-Hidden -FilePath $BotPython `
    -ArgumentList @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '6190') `
    -WorkingDirectory 'D:\QQNTBOT\dashboard' | Out-Null

if (Wait-Port 6190 30) {
    Write-Host 'dashboard ready: http://127.0.0.1:6190'
    exit 0
}
Write-Host 'WARN: dashboard did not start'
exit 1
