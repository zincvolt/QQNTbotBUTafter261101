import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print("active_reply:", json.dumps(cfg["provider_ltm_settings"].get("active_reply"), ensure_ascii=False))
