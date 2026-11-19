import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
for p in cfg["provider"]:
    if "deepseek" in p["id"]:
        print(p["id"], "enable=", p.get("enable"), "model=", p.get("model"), "source=", p.get("provider_source_id"))
for s in cfg["provider_sources"]:
    if "deepseek" in s["id"]:
        k = s.get("key") or ([s.get("api_key")] if s.get("api_key") else [])
        print("source", s["id"], "key长度", len(k[0]) if k else 0, "base", s.get("api_base"))
