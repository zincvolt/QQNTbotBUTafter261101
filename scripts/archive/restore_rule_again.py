import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["text_rules"] = [{"pattern": "。(?=\\s|$)", "to": "~"}]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
