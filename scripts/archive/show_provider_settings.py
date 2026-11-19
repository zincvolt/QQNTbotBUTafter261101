import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print("provider_settings:", json.dumps(cfg.get("provider_settings"), ensure_ascii=False)[:600])
print("\nkb 相关:", {k: cfg.get(k) for k in ("default_kb_collection","kb_names","kb_agentic_mode","kb_fusion_top_k","kb_final_top_k")})
