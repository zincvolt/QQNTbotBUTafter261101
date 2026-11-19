from pathlib import Path
p = Path(r"D:\QQNTBOT\start-all.ps1")
s = p.read_text(encoding="utf-8-sig")
old = '''    # 需要重新扫码时自动把二维码页面弹出来
    Start-Sleep -Seconds 10
    $qr = 'D:\\QQNTBOT\\apps\\NapCat\\cache\\qrcode.png'
    if (Test-Path $qr) {
        $age = ((Get-Date) - (Get-Item $qr).LastWriteTime).TotalSeconds
        if ($age -lt 180) {
            Write-Host '      login required -> opening QR window'
            Start-Process 'D:\\QQNTBOT\\登录二维码.html'
        } else {
            Write-Host '      already logged in'
        }
    }'''
new = '''    # 实时二维码服务：从 NapCat API 现取现画，不会过期
    Start-Sleep -Seconds 6
    if (-not (Test-Port 6191)) {
        Start-Process -WindowStyle Hidden -FilePath 'D:\\QQNTBOT\\apps\\AstrBot\\.venv\\Scripts\\python.exe' `
            -ArgumentList @('D:\\QQNTBOT\\scripts\\qq_qr_server.py') `
            -RedirectStandardOutput 'D:\\QQNTBOT\\_backup\\qr.out' `
            -RedirectStandardError 'D:\\QQNTBOT\\_backup\\qr.err'
        Start-Sleep -Seconds 3
    }
    Write-Host '      QR page: http://127.0.0.1:6191/ （需要扫码时打开）'
    Start-Process 'http://127.0.0.1:6191/\''''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8-sig")
    print("start-all 第 5 步改成实时二维码页")
else:
    print("MISS")
