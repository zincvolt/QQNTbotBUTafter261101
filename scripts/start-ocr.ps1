# Start the OCR model as a dedicated long-running server (ASCII only)
# Runs on 127.0.0.1:8083 so the chat router never evicts the 9B to read an image.
$ErrorActionPreference = 'Stop'

$exe    = 'D:\LLM\llama.cpp\b12274\llama-server.exe'
$model  = 'D:\LLM\models\PaddleOCR-VL-1.6.gguf'
$mmproj = 'D:\LLM\models\PaddleOCR-VL-1.6-mmproj.gguf'
$out    = 'D:\QQNTBOT\_backup\ocr.out'
$err    = 'D:\QQNTBOT\_backup\ocr.err'

if (Get-NetTCPConnection -State Listen -LocalPort 8083 -ErrorAction SilentlyContinue) {
    Write-Host 'ocr already running on 8083'
    exit 0
}

Start-Process -WindowStyle Hidden -FilePath $exe -ArgumentList @(
    '-m', $model,
    '--mmproj', $mmproj,
    '--host', '127.0.0.1',
    '--port', '8083',
    '-c', '4096',
    '-ngl', '999',
    '--parallel', '1',
    '--api-key', 'sk-ocr-local'
) -RedirectStandardOutput $out -RedirectStandardError $err

for ($i = 0; $i -lt 120; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -State Listen -LocalPort 8083 -ErrorAction SilentlyContinue) {
        Write-Host 'ocr ready on 8083'
        exit 0
    }
}
Write-Host 'WARN: ocr did not start, see ocr.err'
