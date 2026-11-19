import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(p.read_text(encoding="utf-8"))
ar = cfg["provider_ltm_settings"]["active_reply"]
ar["enable"] = True
ar["method"] = "judge"
ar["possibility_reply"] = 0.05
p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("active_reply:", ar)
