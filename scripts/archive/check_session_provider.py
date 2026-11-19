import sqlite3
from pathlib import Path
db = Path(r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db")
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
try:
    rows = con.execute("SELECT umo, provider_id FROM platform_settings").fetchall()
    print("platform_settings:", rows[:5])
except Exception as e:
    print("platform_settings 读取失败:", e)
    print("表:", [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")])
