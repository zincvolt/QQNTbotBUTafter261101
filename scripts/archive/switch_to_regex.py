import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
p.write_text(json.dumps({
    "meme_chance": 0.3,
    "text_rules": [{"pattern": "。(?=\\s|$)", "to": "~"}],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
