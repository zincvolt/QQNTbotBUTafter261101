import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print("顶层键:", list(cfg.keys()))
print("\nprovider 段:")
print(json.dumps(cfg.get("provider"), ensure_ascii=False, indent=1)[:1500])
