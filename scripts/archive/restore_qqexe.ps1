# Restore the original signed QQ.exe, keep dbghelp.dll (run as admin)
$ErrorActionPreference = 'Stop'
$bak = 'D:\QQNTBOT\_backup\QQ.exe.original'
$dst = 'C:\Program Files\Tencent\QQNT\QQ.exe'
$log = 'D:\QQNTBOT\_backup\restore_result.txt'

Copy-Item $bak $dst -Force
@(
  "restored_at : $(Get-Date -Format s)",
  "version     : $((Get-Item $dst).VersionInfo.FileVersion)",
  "signature   : $((Get-AuthenticodeSignature $dst).Status)",
  "dbghelp     : $(Test-Path 'C:\Program Files\Tencent\QQNT\dbghelp.dll')"
) | Out-File -Encoding utf8 $log
Write-Host "done"
