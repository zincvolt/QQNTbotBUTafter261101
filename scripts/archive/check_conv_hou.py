import sqlite3, json
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
for umo, cid, upd, content in con.execute("SELECT user_id, conversation_id, updated_at, content FROM conversations ORDER BY updated_at DESC").fetchall():
    msgs = json.loads(content) if content else []
    hou = [m for m in msgs if "厚" in str(m.get("content",""))]
    print(f"{umo} | {len(msgs)} 条 | 含厚 {len(hou)} | 更新 {upd[:16]}")
    for m in msgs[-2:]:
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(str(p.get("text","")) for p in c if isinstance(p, dict))
        print("   ", m.get("role"), str(c)[:110].replace("\n"," "))
