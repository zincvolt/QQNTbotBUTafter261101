import sqlite3
c = sqlite3.connect(r"file:D:\QQNTBOT\apps\AstrBot\data\knowledge_base\kb.db?mode=ro", uri=True)
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("表:", tables)
for t in tables:
    try:
        n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})")]
        print(f"  {t}: {n} 行 | 字段 {cols}")
    except Exception as e:
        print(t, "ERR", e)
