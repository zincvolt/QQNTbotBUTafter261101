import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT user_id, COUNT(*) FROM conversations GROUP BY user_id ORDER BY 2 DESC LIMIT 6").fetchall()
for r in rows: print(r)
