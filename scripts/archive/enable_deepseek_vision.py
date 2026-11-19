import json
from pathlib import Path
CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
for p in cfg.get("provider", []):
    if p.get("id") == "deepseek":
        p["model"] = "deepseek-flash"
        p["modalities"] = ["image", "text"]
        print("deepseek 已支持图片输入:", p["modalities"], "model:", p["model"])
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
