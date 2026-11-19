import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("PRAGMA table_info(personas)")
print("columns:", [r[1] for r in cur.fetchall()])
cur.execute("SELECT * FROM personas")
for r in cur.fetchall():
    print("ROW:", [str(x)[:200] for x in r])
