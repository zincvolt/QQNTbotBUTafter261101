import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
for p in cfg["provider"]:
    print(f"{p.get('id'):<28} keys={sorted(p.keys())}")
