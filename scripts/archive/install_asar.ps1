# Drop the shadow app.asar into QQNT version resources (run as admin)
$ErrorActionPreference = 'Stop'
$src  = 'D:\QQNTBOT\build\asar-shim\app.asar'
$res  = 'C:\Program Files\Tencent\QQNT\versions\9.9.33-52230\resources'
$dst  = Join-Path $res 'app.asar'
$log  = 'D:\QQNTBOT\_backup\asar_install.txt'

Copy-Item $src $dst -Force
@(
  "installed_at : $(Get-Date -Format s)",
  "target       : $dst",
  "size         : $((Get-Item $dst).Length)",
  "resources    : " + ((Get-ChildItem $res | Select-Object -ExpandProperty Name) -join ', ')
) | Out-File -Encoding utf8 $log
Write-Host "done"
