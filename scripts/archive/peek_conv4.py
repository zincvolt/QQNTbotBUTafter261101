import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT updated_at, user_id, content FROM conversations ORDER BY updated_at DESC LIMIT 3").fetchall()
for ts, uid, content in rows:
    msgs = json.loads(content)
    print(f"=== {ts} {uid} ({len(msgs)} msgs)")
    for m in msgs[-2:]:
        t = m.get("content")
        if isinstance(t, list):
            t = " ".join(str(c.get("text", c)) for c in t)
        print("   ", m.get("role"), ":", str(t)[:110].replace("\n", " "))
