from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
import json
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
    "meme_chance": 0.3,
    "text_rules": [{"find": "。", "to": "~"}],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
