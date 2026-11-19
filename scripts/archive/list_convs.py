import json, sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT user_id, conversation_id, updated_at, title, length(content) FROM conversations ORDER BY updated_at DESC").fetchall()
for r in rows:
    print(r)
