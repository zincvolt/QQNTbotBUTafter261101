import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("tables:", tables)
for t in ("messages", "conversations"):
    if t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        print(f"\n{t} columns:", [r[1] for r in cur.fetchall()])
