# Revert QQNT to stock: restore package.json, drop our files (run as admin)
$ErrorActionPreference = 'Stop'
$root = 'C:\Program Files\Tencent\QQNT'
$log  = 'D:\QQNTBOT\_backup\revert.txt'

$cfg = Get-Content (Join-Path $root 'versions\config.json') -Raw | ConvertFrom-Json
$cur = $cfg.curVersion
$ver = Join-Path $root "versions\$cur"
$app = Join-Path $ver 'resources\app'

$bak = "D:\QQNTBOT\_backup\app-package.json.$cur.original"
if (Test-Path $bak) { Copy-Item $bak (Join-Path $app 'package.json') -Force }

foreach ($f in @((Join-Path $app 'LiteLoader.js'),
                 (Join-Path $root 'dbghelp.dll'),
                 (Join-Path $ver 'dbghelp.dll'),
                 (Join-Path $ver 'resources\app.asar'))) {
    if (Test-Path $f) { Remove-Item $f -Force }
}

if (Test-Path 'D:\QQNTBOT\_backup\QQ.exe.original') {
    Copy-Item 'D:\QQNTBOT\_backup\QQ.exe.original' (Join-Path $root 'QQ.exe') -Force
}

@(
  "reverted_at : $(Get-Date -Format s)",
  "version     : $cur",
  "main        : $(((Get-Content (Join-Path $app 'package.json') -Raw | ConvertFrom-Json).main))",
  "qq.exe sig  : $((Get-AuthenticodeSignature (Join-Path $root 'QQ.exe')).Status)"
) | Out-File -Encoding utf8 $log
Write-Host "done"
