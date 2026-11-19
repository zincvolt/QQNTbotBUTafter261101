import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT created_at, user_id, sender_name FROM platform_message_history ORDER BY id DESC LIMIT 10").fetchall()
for r in rows:
    print(r[0], "|", r[1], "|", (r[2] or "")[:14])
