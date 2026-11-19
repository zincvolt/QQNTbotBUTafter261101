# Start the bot dashboard on 127.0.0.1:6190 (ASCII only)
$ErrorActionPreference = 'Stop'

if (Get-NetTCPConnection -State Listen -LocalPort 6190 -ErrorAction SilentlyContinue) {
    Write-Host 'dashboard already running on 6190'
    exit 0
}

$python = 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe'
$dir    = 'D:\QQNTBOT\dashboard'

Start-Process -WindowStyle Hidden -FilePath $python `
    -ArgumentList @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '6190') `
    -WorkingDirectory $dir

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -State Listen -LocalPort 6190 -ErrorAction SilentlyContinue) {
        Write-Host 'dashboard ready: http://127.0.0.1:6190'
        exit 0
    }
}
Write-Host 'WARN: dashboard did not start'
