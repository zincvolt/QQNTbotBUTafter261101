from pathlib import Path
p = Path(r"D:\QQNTBOT\scripts\qq-login.ps1")
s = p.read_text(encoding="utf-8-sig")
# 刷新时用新文件名，避免图片被查看器占用
s = s.replace('''        & $py $tmpPy $url $qrPng
        Write-Host "二维码已刷新，重新打开: $qrPng"
        Start-Process $qrPng''',
'''        $stamp = Get-Date -Format 'HHmmss'
        $qrPng = "D:\\QQNTBOT\\login-qr-$stamp.png"
        & $py $tmpPy $url $qrPng
        Write-Host "二维码已刷新，重新打开: $qrPng"
        Start-Process $qrPng''')
p.write_text(s, encoding="utf-8-sig")
print("刷新改用新文件名")
