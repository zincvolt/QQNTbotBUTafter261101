import sqlite3
db = r"D:\QQNTBOT\data\memory.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
print("count:", con.execute("SELECT COUNT(*) FROM facts").fetchone()[0])
print("max id:", con.execute("SELECT MAX(id) FROM facts").fetchone()[0])
print(con.execute("SELECT id, substr(text,1,30) FROM facts ORDER BY id DESC LIMIT 3").fetchall())
