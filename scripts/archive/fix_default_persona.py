import json, sqlite3
from pathlib import Path
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
text = json.load(open(r"D:\QQNTBOT\data\persona.json", encoding="utf-8"))["text"]
con = sqlite3.connect(db)
con.execute("UPDATE personas SET system_prompt = ?, updated_at = datetime('now') WHERE persona_id = 'default'", (text,))
con.commit()
for r in con.execute("SELECT persona_id, substr(system_prompt,1,40) FROM personas").fetchall():
    print(r)
con.close()
