import json, sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
for umo in ("qq:GroupMessage:942316942", "qq:GroupMessage:1128093050"):
    row = con.execute("SELECT content FROM conversations WHERE user_id=?", (umo,)).fetchone()
    if not row: continue
    msgs = json.loads(row[0])
    print(f"\n===== {umo} 共 {len(msgs)} 条 =====")
    for m in msgs[-6:]:
        role = m.get("role")
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(str(p.get("text", "")) for p in c if isinstance(p, dict))
        print(f"[{role}] {str(c)[:220].replace(chr(10), ' | ')}")
