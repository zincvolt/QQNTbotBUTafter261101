import json
from pathlib import Path
cfg_path = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
cfg["kb_names"] = ["本地知识库"]
cfg["kb_agentic_mode"] = True
cfg["kb_final_top_k"] = 5
cfg["kb_fusion_top_k"] = 20
cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("kb_names:", cfg["kb_names"], "agentic:", cfg["kb_agentic_mode"])
