import sqlite3, time
from datetime import datetime
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT user_id, MAX(created_at) FROM platform_message_history WHERE user_id LIKE 'qq:GroupMessage:%' GROUP BY user_id").fetchall()
for umo, ts in rows:
    stamp = datetime.fromisoformat(str(ts)).timestamp()
    print(f"{umo}  last={ts}  idle={int((time.time()-stamp)/60)} min  group={str(umo).rsplit('_',1)[-1]}")
