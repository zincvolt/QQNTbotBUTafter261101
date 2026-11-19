import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(p.read_text(encoding="utf-8"))
d.setdefault("text_rules", [])
if not d["text_rules"]:
    d["text_rules"] = [{"pattern": "。(?=\\s|$)", "to": "~"}]
d.setdefault("reply_budget", 8)
d.setdefault("reply_budget_minutes", 10)
d.setdefault("history_minutes", 30)
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
