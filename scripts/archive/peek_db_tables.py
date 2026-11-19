import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    print(name)
print("=== preferences ===")
try:
    for r in con.execute("SELECT * FROM preferences LIMIT 8").fetchall():
        print(r)
except Exception as e:
    print("err", e)
