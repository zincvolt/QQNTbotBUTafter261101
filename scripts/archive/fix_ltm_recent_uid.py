from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '"SELECT id, created_at, user_id, sender_name, content "',
    '"SELECT id, created_at, sender_id, sender_name, content "',
)
s = s.replace(
    '''        if not text or len(text) < 2:
            continue
        uid = str(umo).split(":")[-1].split("_")[-1]''',
    '''        if not text or len(text) < 2 or text.strip("[]") in ("Image", "图片"):
            continue
        uid = str(umo) or "unknown"''',
)
p.write_text(s, encoding="utf-8")
print("sender_id used")
