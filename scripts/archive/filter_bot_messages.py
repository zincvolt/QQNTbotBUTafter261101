from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '''        uid = str(umo) or "unknown"''',
    '''        uid = str(umo) or "unknown"
        if uid == "1474388967":  # 机器人自己说的话不进记忆
            continue''',
)
p.write_text(s, encoding="utf-8")
print("bot filtered")
