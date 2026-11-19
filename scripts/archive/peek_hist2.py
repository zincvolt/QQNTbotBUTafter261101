import sqlite3, datetime
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT created_at, user_id, sender_name, substr(content,1,60) FROM platform_message_history ORDER BY id DESC LIMIT 5").fetchall()
for r in rows:
    print(r)
print("now utc:", datetime.datetime.utcnow().strftime("%H:%M:%S"))
