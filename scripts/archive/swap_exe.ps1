$ErrorActionPreference='Stop'
Copy-Item 'D:\QQNTBOT\_downloads\QQ.exe' 'C:\Program Files\Tencent\QQNT\QQ.exe' -Force
@(
  "at      : $(Get-Date -Format s)",
  "version : $((Get-Item 'C:\Program Files\Tencent\QQNT\QQ.exe').VersionInfo.FileVersion)",
  "sig     : $((Get-AuthenticodeSignature 'C:\Program Files\Tencent\QQNT\QQ.exe').Status)",
  "dbghelp : $(Test-Path 'C:\Program Files\Tencent\QQNT\dbghelp.dll')"
) | Out-File -Encoding utf8 'D:\QQNTBOT\_backup\exe_swap.txt'
