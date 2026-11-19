import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
ps = cfg.get("provider_settings", {})
for k, v in ps.items():
    if "tool" in k.lower() or "func" in k.lower():
        print(k, "=", v)
print("provider0:", json.dumps(cfg["provider"][0], ensure_ascii=False)[:400])
