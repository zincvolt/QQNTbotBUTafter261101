import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
for src in cfg.get("provider_sources", []):
    print(src.get("id"), src.get("api_base"))
p0 = cfg["provider"][0]
print("provider0 keys:", [k for k in p0])
print("api key:", str(p0.get("key"))[:30])
