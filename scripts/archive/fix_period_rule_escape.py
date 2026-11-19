"""Write the period rule with the correct escaping into reply.json."""

import json
from pathlib import Path

REPLY = Path(r"D:\QQNTBOT\data\reply.json")
PATTERN = r"。(?=\s|$|[（(\[【「『])"

cfg = json.loads(REPLY.read_text(encoding="utf-8"))
cfg["text_rules"] = [{"pattern": PATTERN, "to": "~"}]
REPLY.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

check = json.loads(REPLY.read_text(encoding="utf-8"))
print("写入的 pattern:", repr(check["text_rules"][0]["pattern"]))
