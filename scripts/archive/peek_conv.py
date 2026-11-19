import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("SELECT updated_at, user_id, content FROM conversations ORDER BY updated_at DESC LIMIT 1")
row = cur.fetchone()
data = json.loads(row[2])
print("updated:", row[0], "user:", row[1], "msgs:", len(data))
for m in data[-8:]:
    txt = m.get("content")
    if isinstance(txt, list):
        txt = " ".join(str(c.get("text", c)) for c in txt)
    print(f"[{m.get('role')}] {str(txt)[:500]}")
