import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print(json.dumps(cfg.get("provider_ltm_settings", {}), ensure_ascii=False, indent=2))
