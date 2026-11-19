"""Delete every knowledge base directory and its database rows."""

import shutil
import sqlite3
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot\data\knowledge_base")

for item in ROOT.iterdir():
    if item.is_dir():
        shutil.rmtree(item, ignore_errors=True)
        print("删目录:", item.name)

con = sqlite3.connect(ROOT / "kb.db")
for table in ("kb_documents", "kb_media", "knowledge_bases"):
    con.execute(f"DELETE FROM {table}")
con.commit()
counts = [
    (t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    for t in ("knowledge_bases", "kb_documents", "kb_media")
]
print("剩余:", counts)
con.execute("VACUUM")
con.close()
print("清理完成")
