import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(p.read_text(encoding="utf-8"))
cfg["log_file_enable"] = True
cfg["log_file_path"] = "logs/astrbot.log"
cfg["log_file_max_mb"] = 20
p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("log_file_enable:", cfg["log_file_enable"], cfg["log_file_path"])
