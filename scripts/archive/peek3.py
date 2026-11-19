import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("SELECT updated_at, user_id, content FROM conversations ORDER BY updated_at DESC LIMIT 2")
for ts, uid, content in cur.fetchall():
    data = json.loads(content)
    print(f"=== {ts} {uid} ===")
    for m in data[-4:]:
        txt = m.get("content")
        if isinstance(txt, list):
            txt = " ".join(str(c.get("text", c)) for c in txt)
        print(f"[{m.get('role')}] {str(txt)[:400]}")
