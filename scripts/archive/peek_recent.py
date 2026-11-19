import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT created_at, user_id, sender_name, substr(content,1,90) FROM platform_message_history ORDER BY id DESC LIMIT 6").fetchall()
for r in rows:
    print(r)
