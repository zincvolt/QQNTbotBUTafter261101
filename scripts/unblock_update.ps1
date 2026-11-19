# Remove the QQNTBOT hosts pin (run as admin)
$ErrorActionPreference = 'Stop'
$hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
$bak   = 'D:\QQNTBOT\_backup\hosts.before-qqntbot'

if (Test-Path $bak) {
    Copy-Item $bak $hosts -Force
    Write-Host "restored from $bak"
} else {
    $content = Get-Content $hosts | Where-Object { $_ -notmatch 'QQNTBOT pin 9\.9\.25' -and $_ -notmatch '^127\.0\.0\.1 (dldir1|dldir1v6|qqdl)\.' }
    Set-Content -Path $hosts -Value $content -Encoding ASCII
    Write-Host 'cleaned entries'
}
