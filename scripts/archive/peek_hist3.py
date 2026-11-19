import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT created_at, user_id, sender_name, content FROM platform_message_history ORDER BY id DESC LIMIT 8").fetchall()
for ts, uid, name, content in rows:
    try:
        d = json.loads(content)
        text = " ".join(str(p.get("text","")) for p in d.get("message",[]) if p.get("type") in ("text","plain"))
    except Exception:
        text = content[:40]
    print(f"{ts} {name[:8]:8} {uid[:32]:32} {text[:60]}")
