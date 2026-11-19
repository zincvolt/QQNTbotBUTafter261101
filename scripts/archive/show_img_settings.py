import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
ps = cfg.get("provider_settings", {})
for k in sorted(ps):
    if any(x in k for x in ("image", "caption", "vision", "file", "stt", "tts")):
        print(f"{k} = {ps[k]}")
