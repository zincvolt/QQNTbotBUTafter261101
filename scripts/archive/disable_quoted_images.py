import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(p.read_text(encoding="utf-8-sig"))
ps = cfg["provider_settings"]
print("before:", ps.get("max_quoted_fallback_images"))
ps["max_quoted_fallback_images"] = 0
p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("after :", ps["max_quoted_fallback_images"])
