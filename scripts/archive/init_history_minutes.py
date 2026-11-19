import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["history_minutes"] = 30
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
