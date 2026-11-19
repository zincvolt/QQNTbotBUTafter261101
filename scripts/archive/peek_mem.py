import sqlite3, json
db = r"D:\QQNTBOT\data\memory.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("SELECT uid, COUNT(*) FROM facts GROUP BY uid")
print("facts per user:", cur.fetchall())
cur.execute("SELECT text FROM facts ORDER BY created DESC LIMIT 15")
for (t,) in cur.fetchall():
    print(" -", t)
