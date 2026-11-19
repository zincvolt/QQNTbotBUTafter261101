# Use ONLY the patched QQ.exe: remove dbghelp shims, install patched exe (run as admin)
$ErrorActionPreference = 'Stop'
$root = 'C:\Program Files\Tencent\QQNT'
$ver  = Join-Path $root 'versions\9.9.33-52230'
$log  = 'D:\QQNTBOT\_backup\patched_only.txt'

# 1. remove dbghelp shims (both locations)
foreach ($p in @((Join-Path $root 'dbghelp.dll'), (Join-Path $ver 'dbghelp.dll'))) {
    if (Test-Path $p) { Remove-Item $p -Force }
}

# 2. install patched exe
Copy-Item 'D:\QQNTBOT\_downloads\QQ.exe' (Join-Path $root 'QQ.exe') -Force

@(
  "installed_at : $(Get-Date -Format s)",
  "qq.exe ver   : $((Get-Item (Join-Path $root 'QQ.exe')).VersionInfo.FileVersion)",
  "qq.exe sig   : $((Get-AuthenticodeSignature (Join-Path $root 'QQ.exe')).Status)",
  "dbghelp root : $(Test-Path (Join-Path $root 'dbghelp.dll'))",
  "dbghelp ver  : $(Test-Path (Join-Path $ver 'dbghelp.dll'))",
  "app main     : $((Get-Content (Join-Path $ver 'resources\app\package.json') -Raw | ConvertFrom-Json).main)"
) | Out-File -Encoding utf8 $log
Write-Host "done"
