import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
data = json.loads(p.read_text(encoding="utf-8"))
data.setdefault("reply_chance", 0.55)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
