$ErrorActionPreference='Stop'
$src='C:\Program Files\Tencent\QQNT\dbghelp.dll'
$verDir='C:\Program Files\Tencent\QQNT\versions\9.9.33-52230'
Copy-Item $src (Join-Path $verDir 'dbghelp.dll') -Force
"copied to version dir: $(Test-Path (Join-Path $verDir 'dbghelp.dll'))" | Out-File -Encoding utf8 'D:\QQNTBOT\_backup\dll_copy.txt'
