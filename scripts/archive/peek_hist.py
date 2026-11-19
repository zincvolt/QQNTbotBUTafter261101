import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("PRAGMA table_info(platform_message_history)")
print("cols:", [r[1] for r in cur.fetchall()])
cur.execute("SELECT * FROM platform_message_history ORDER BY 1 DESC LIMIT 3")
for r in cur.fetchall():
    print([str(x)[:60] for x in r])
