# Start the bot dashboard (ASCII only)
# Paths are configurable: QQNTBOT_ROOT / QQNTBOT_PYTHON / QQNTBOT_DASH_PORT
$ErrorActionPreference = 'Stop'

# This script lives in <root>\scripts, so the project root is its parent.
$root   = if ($env:QQNTBOT_ROOT) { $env:QQNTBOT_ROOT } else { Split-Path -Parent $PSScriptRoot }
$port   = if ($env:QQNTBOT_DASH_PORT) { [int]$env:QQNTBOT_DASH_PORT } else { 6190 }
$python = if ($env:QQNTBOT_PYTHON) { $env:QQNTBOT_PYTHON } else { Join-Path $root 'apps\AstrBot\.venv\Scripts\python.exe' }
$dir    = Join-Path $root 'dashboard'

if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    Write-Host "dashboard already running on $port"
    exit 0
}

if (-not (Test-Path $python)) {
    Write-Host "WARN: python not found: $python"
    Write-Host "Set QQNTBOT_PYTHON to a Python that has dashboard\requirements.txt installed."
    exit 1
}
if (-not (Test-Path (Join-Path $dir 'app.py'))) {
    Write-Host "WARN: dashboard not found: $dir"
    exit 1
}

Start-Process -WindowStyle Hidden -FilePath $python `
    -ArgumentList @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', "$port") `
    -WorkingDirectory $dir

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        Write-Host "dashboard ready: http://127.0.0.1:$port"
        exit 0
    }
}
Write-Host 'WARN: dashboard did not start'
