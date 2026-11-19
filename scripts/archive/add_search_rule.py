import sqlite3
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
RULE = "- 上下文里有「实时搜索结果」时优先用；资料里没有的就说不知道，别装懂"
con = sqlite3.connect(db); cur = con.cursor()
cur.execute("SELECT system_prompt FROM personas WHERE persona_id='grey'")
p = cur.fetchone()[0]
if RULE not in p:
    p += RULE + "\n"
    cur.execute("UPDATE personas SET system_prompt=?, updated_at=datetime('now') WHERE persona_id='grey'", (p,))
    con.commit()
con.close()
print("rule added:", RULE in p, "| chars:", len(p))
