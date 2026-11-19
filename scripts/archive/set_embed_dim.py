import json
from pathlib import Path
CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
for p in cfg.get("provider", []):
    if p.get("id") == "local-embed":
        p["embedding_dimensions"] = 512
        print("已设置 embedding_dimensions=512")
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
