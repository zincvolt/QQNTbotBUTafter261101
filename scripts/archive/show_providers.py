import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
provs = cfg.get("provider") or []
for p in provs:
    print(p.get("id"), "|", p.get("type"), "|", p.get("enable"), "|", p.get("model_config", {}).get("model") if isinstance(p.get("model_config"), dict) else p.get("model"))
print("embedding providers:", [p.get("id") for p in provs if p.get("type") in ("embedding", "openai_embedding")])
