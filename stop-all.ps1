# Stop the QQ bot stack (ASCII only)
$ErrorActionPreference = 'Continue'

Write-Host '=== stopping QQ + NapCat ==='
Get-Process QQ -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  QQ pid $($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Write-Host '=== stopping AstrBot ==='
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like '*QQNTBOT\apps\AstrBot*' } |
    ForEach-Object {
        Write-Host "  python pid $($_.Id)"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

Write-Host '=== stopping dashboard ==='
$dash = Get-NetTCPConnection -State Listen -LocalPort 6190 -ErrorAction SilentlyContinue
foreach ($c in $dash) {
    Write-Host "  dashboard pid $($c.OwningProcess)"
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host '=== stopping llama.cpp router (also unloads the model) ==='
Get-Process llama-server -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  llama-server pid $($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2
foreach ($p in 8080, 6185, 6199, 6099, 6190, 8082, 8083, 8084) {
    $state = if (Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue) { 'still up' } else { 'down' }
    Write-Host ("  port {0,-5} {1}" -f $p, $state)
}
Write-Host 'stopped.'

