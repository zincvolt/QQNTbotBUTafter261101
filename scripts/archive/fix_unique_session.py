import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(p.read_text(encoding="utf-8-sig"))
cfg["platform_settings"]["unique_session"] = False
p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("unique_session:", cfg["platform_settings"]["unique_session"])
