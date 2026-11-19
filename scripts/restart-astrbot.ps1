# Restart only the AstrBot main process (keeps QQ, judge and dashboard alive)
$ErrorActionPreference = 'Continue'

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -match 'AstrBot' -and $_.CommandLine -match 'main\.py' } |
    ForEach-Object {
        Write-Host "  stopping AstrBot pid $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Seconds 2

Start-Process -WindowStyle Hidden `
    -WorkingDirectory 'D:\QQNTBOT\apps\AstrBot' `
    -FilePath 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe' `
    -ArgumentList 'main.py'

for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -State Listen -LocalPort 6185 -ErrorAction SilentlyContinue) {
        Write-Host 'AstrBot restarted'
        exit 0
    }
}
Write-Host 'WARN: AstrBot did not come back'
