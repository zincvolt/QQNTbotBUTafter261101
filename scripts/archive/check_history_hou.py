import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT id, created_at, user_id, sender_name, content FROM platform_message_history ORDER BY id DESC LIMIT 400").fetchall()
hits = [(i,t,u,n,c) for i,t,u,n,c in rows if "厚" in (c or "")]
print("最近400条里含'厚'的:", len(hits))
for r in hits[:5]:
    print(" ", r[1], r[3], r[4][:90].replace("\n"," "))
print("总历史条数:", con.execute("SELECT COUNT(*) FROM platform_message_history").fetchone()[0])
