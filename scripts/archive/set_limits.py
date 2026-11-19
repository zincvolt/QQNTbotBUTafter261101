import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(p.read_text(encoding="utf-8-sig"))
prov = cfg["provider"][0]
extra = prov.setdefault("custom_extra_body", {})
extra["max_tokens"] = 300
extra["temperature"] = 0.85
p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("provider id:", prov.get("id"))
print("custom_extra_body:", extra)
