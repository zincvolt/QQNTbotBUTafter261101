# Replace QQ.exe with the patched launcher and drop dbghelp.dll (run as admin)
$ErrorActionPreference = 'Stop'
$src    = 'D:\QQNTBOT\_downloads\QQ.exe'
$dll    = 'D:\QQNTBOT\_downloads\dbghelp_x64.dll'
$dstDir = 'C:\Program Files\Tencent\QQNT'
$dst    = Join-Path $dstDir 'QQ.exe'
$log    = 'D:\QQNTBOT\_backup\install_result.txt'

Copy-Item $dst 'D:\QQNTBOT\_backup\QQ.exe.before-replace' -Force
Copy-Item $src $dst -Force
Copy-Item $dll (Join-Path $dstDir 'dbghelp.dll') -Force

$i = Get-Item $dst
$sig = (Get-AuthenticodeSignature $dst).Status
@(
  "installed_at : $(Get-Date -Format s)",
  "target       : $dst",
  "size         : $($i.Length)",
  "version      : $($i.VersionInfo.FileVersion)",
  "signature    : $sig",
  "dbghelp      : $((Get-Item (Join-Path $dstDir 'dbghelp.dll')).Length) bytes"
) | Out-File -Encoding utf8 $log

Write-Host "done, see $log"
