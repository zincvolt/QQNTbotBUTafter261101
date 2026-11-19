# Block the QQNT installer CDNs so the pinned build cannot be replaced (run as admin)
$ErrorActionPreference = 'Stop'
$hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
$bak   = 'D:\QQNTBOT\_backup\hosts.before-qqntbot'
$mark  = '# QQNTBOT pin 9.9.25'
$list  = @('dldir1.qq.com', 'dldir1v6.qq.com', 'qqdl.gtimg.cn')

if (-not (Test-Path $bak)) { Copy-Item $hosts $bak -Force }

$content = Get-Content -Path $hosts -Raw
if ($content -notmatch [regex]::Escape($mark)) {
    Add-Content -Path $hosts -Value '' -Encoding ASCII
    Add-Content -Path $hosts -Value $mark -Encoding ASCII
    foreach ($d in $list) {
        Add-Content -Path $hosts -Value "127.0.0.1 $d" -Encoding ASCII
    }
}

@(
  "blocked_at : $(Get-Date -Format s)",
  "backup     : $bak",
  "entries    : $($list -join ', ')"
) | Out-File -Encoding utf8 'D:\QQNTBOT\_backup\hosts_block.txt'
Write-Host 'done'
