import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT created_at, sender_name, substr(content,1,90) FROM platform_message_history WHERE created_at LIKE '2026-11-17 07:5%' ORDER BY id LIMIT 10").fetchall()
for r in rows:
    print(r[0], r[1][:10] if r[1] else "", r[2][:70])
print("total today:", con.execute("SELECT COUNT(*) FROM platform_message_history").fetchone()[0])
