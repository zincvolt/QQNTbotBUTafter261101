import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
for r in con.execute("SELECT persona_id, substr(system_prompt,1,60) FROM personas").fetchall():
    print(r)
