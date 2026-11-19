import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
for src in cfg.get("provider_sources", []):
    print(src.get("id"), "key=", src.get("key"))
