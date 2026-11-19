import sqlite3
from pathlib import Path
db = Path(r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db")
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
print("schema:", con.execute("SELECT sql FROM sqlite_master WHERE name='preferences'").fetchone()[0])
rows = con.execute("SELECT * FROM preferences LIMIT 10").fetchall()
for r in rows: print(r)
