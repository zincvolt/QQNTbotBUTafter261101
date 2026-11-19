# Install LiteLoader entry into whichever QQNT version is current (run as admin)
# Writes LiteLoader.js + backs up package.json; drops dbghelp.dll if present.
$ErrorActionPreference = 'Stop'
$root = 'C:\Program Files\Tencent\QQNT'
$log  = 'D:\QQNTBOT\_backup\lite_install.txt'

# resolve current version dir from versions\config.json
$cfg = Get-Content (Join-Path $root 'versions\config.json') -Raw | ConvertFrom-Json
$cur = $cfg.curVersion
$ver = Join-Path $root "versions\$cur"
if (-not (Test-Path $ver)) { throw "version dir not found: $ver" }

$app = Join-Path $ver 'resources\app'
$pj  = Join-Path $app 'package.json'
$bak = "D:\QQNTBOT\_backup\app-package.json.$cur.original"

if (-not (Test-Path $bak)) { Copy-Item $pj $bak -Force }

# entry file
'require(String.raw`D:\QQNTBOT\apps\LiteLoader`)' |
  Set-Content -Path (Join-Path $app 'LiteLoader.js') -Encoding UTF8

# point main at it
$json = Get-Content $pj -Raw
if ($json -notmatch 'LiteLoader\.js') {
  $json = $json -replace '("main"\s*:\s*")[^"]*(")', '${1}./LiteLoader.js${2}'
  [System.IO.File]::WriteAllText($pj, $json, (New-Object System.Text.UTF8Encoding $false))
}

# dbghelp shim next to QQ.exe (and next to QQNT.dll for good measure)
$dll = 'D:\QQNTBOT\_downloads\dbghelp_x64.dll'
$placed = @()
if (Test-Path $dll) {
    Copy-Item $dll (Join-Path $root 'dbghelp.dll') -Force
    $placed += (Join-Path $root 'dbghelp.dll')
    Copy-Item $dll (Join-Path $ver 'dbghelp.dll') -Force
    $placed += (Join-Path $ver 'dbghelp.dll')
}

@(
  "installed_at : $(Get-Date -Format s)",
  "version      : $cur",
  "app          : $app",
  "main         : $(((Get-Content $pj -Raw | ConvertFrom-Json).main))",
  "backup       : $bak",
  "dbghelp      : " + ($placed -join ' ; ')
) | Out-File -Encoding utf8 $log
Write-Host "done: $log"
