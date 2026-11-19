import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print(json.dumps(cfg.get("provider_sources"), ensure_ascii=False, indent=1)[:1200])
print("\n--- vl-local / ocr-local ---")
for p in cfg["provider"]:
    if p["id"] in ("vl-local", "ocr-local"):
        print(json.dumps(p, ensure_ascii=False))
