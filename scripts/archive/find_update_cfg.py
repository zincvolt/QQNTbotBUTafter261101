import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if "update" in k.lower() or "upgrade" in k.lower():
                print(p, "=", v if not isinstance(v, (dict, list)) else type(v).__name__)
            walk(v, p)
walk(cfg)
