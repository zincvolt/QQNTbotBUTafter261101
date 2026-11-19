# QQ login helper: pull the live QR from NapCat and show it as a picture.
# Reads the webui token from NapCat config, logs in, then polls login status.

$ErrorActionPreference = 'Continue'

$cfgPath = 'D:\QQNTBOT\apps\NapCat\config\webui.json'
$py      = 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe'
$qrPng   = 'D:\QQNTBOT\login-qr.png'

$cfg   = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
$token = $cfg.token
$port  = $cfg.port

# NapCat 的密码哈希是 sha256(token + ".napcat")
$sha  = [System.Security.Cryptography.SHA256]::Create()
$hash = [System.BitConverter]::ToString(
    $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($token + '.napcat'))
).Replace('-', '').ToLower()

$login = Invoke-WebRequest "http://127.0.0.1:$port/api/auth/login" -Method POST `
    -ContentType 'application/json' -Body (@{ hash = $hash } | ConvertTo-Json) `
    -UseBasicParsing -TimeoutSec 10
$cred = ($login.Content | ConvertFrom-Json).data.Credential
if (-not $cred) { Write-Host 'WARN: webui 登录失败，检查 token'; exit 1 }

$headers = @{ Authorization = "Bearer $cred"; 'Content-Type' = 'application/json' }

function Get-Status {
    $r = Invoke-WebRequest "http://127.0.0.1:$port/api/QQLogin/CheckLoginStatus" -Method POST `
        -Headers $headers -Body '{}' -UseBasicParsing -TimeoutSec 10
    return ($r.Content | ConvertFrom-Json).data
}

$status = Get-Status
Write-Host "当前状态: isLogin=$($status.isLogin) phase=$($status.loginPhase)"

if ($status.isLogin) {
    $info = Invoke-WebRequest "http://127.0.0.1:$port/api/QQLogin/GetQQLoginInfo" -Method POST `
        -Headers $headers -Body '{}' -UseBasicParsing -TimeoutSec 10
    Write-Host "已登录: $($info.Content)"
    exit 0
}

$url = $status.qrcodeurl
if (-not $url) { Write-Host 'WARN: 没拿到二维码链接'; exit 1 }
Write-Host "二维码链接: $url"

# 用 python 生成二维码 PNG
$pyCode = @"
import qrcode, sys
img = qrcode.make(sys.argv[1])
img = img.resize((520, 520))
img.save(sys.argv[2])
print('qr saved')
"@
$tmpPy = Join-Path $env:TEMP 'make_qr.py'
$pyCode | Out-File -Encoding utf8 $tmpPy
& $py $tmpPy $url $qrPng

if (Test-Path $qrPng) {
    Write-Host "二维码已保存: $qrPng （请用手机 QQ 扫这个窗口里的图）"
    Start-Process $qrPng
} else {
    Write-Host 'WARN: 二维码生成失败'
}

# 轮询 150 秒，扫码后自动提示
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 5
    $s = Get-Status
    if ($s.isLogin) {
        Write-Host "登录成功！phase=$($s.loginPhase)"
        exit 0
    }
    Write-Host "  等待扫码... phase=$($s.loginPhase) error=$($s.loginError)"
    if ($s.loginPhase -in @('waiting_qrcode') -and $s.qrcodeurl -and $s.qrcodeurl -ne $url) {
        $url = $s.qrcodeurl
        $stamp = Get-Date -Format 'HHmmss'
        $qrPng = "D:\QQNTBOT\login-qr-$stamp.png"
        & $py $tmpPy $url $qrPng
        Write-Host "二维码已刷新，重新打开: $qrPng"
        Start-Process $qrPng
    }
}
Write-Host 'WARN: 150 秒内没有完成扫码，重新运行本脚本可刷新二维码'
