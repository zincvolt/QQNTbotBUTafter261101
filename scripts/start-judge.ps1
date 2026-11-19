# Start the tiny judge model (ASCII only)
# Qwen3-1.7B on CPU: ~0.4s per verdict, ~1.8GB RSS, never touches the 9B slot.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')
Repair-Env

$exe   = 'D:\LLM\llama.cpp\b12274\llama-server.exe'
$model = 'D:\LLM\models\Qwen3-1.7B-Q8_0.gguf'
$out   = 'D:\QQNTBOT\_backup\judge.out'
$err   = 'D:\QQNTBOT\_backup\judge.err'

if (Get-NetTCPConnection -State Listen -LocalPort 8082 -ErrorAction SilentlyContinue) {
    Write-Host 'judge already running on 8082'
    exit 0
}

Start-Process -WindowStyle Hidden -FilePath $exe -ArgumentList @(
    '-m', $model,
    '--host', '127.0.0.1',
    '--port', '8082',
    '-c', '2048',
    '-t', '4',
    '--parallel', '1',
    '-ngl', '0',
    '--jinja',
    '--api-key', 'sk-judge-local'
) -RedirectStandardOutput $out -RedirectStandardError $err

for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -State Listen -LocalPort 8082 -ErrorAction SilentlyContinue) {
        Write-Host 'judge ready on 8082 (Qwen3-1.7B)'
        exit 0
    }
}
Write-Host 'WARN: judge did not start, see judge.err'
