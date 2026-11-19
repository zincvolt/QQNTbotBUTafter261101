"""Point the caption provider at the cache proxy and widen the context budget."""

import json
from pathlib import Path

CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))

for src in cfg.get("provider_sources", []):
    if src.get("id") == "ocr_source":
        src["api_base"] = "http://127.0.0.1:8084/v1"
        src["key"] = ["sk-ocr-local"]

comp = cfg["agent_runner"]["config"]["compression"]
comp["max_turns"] = 40
comp["fallback_max_tokens"] = 60000
comp["overflow_strategy"] = "llm_compress"
comp["keep_recent_ratio"] = 0.15

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("ocr api_base :", next(s["api_base"] for s in cfg["provider_sources"] if s["id"] == "ocr_source"))
print("max_turns    :", comp["max_turns"])
print("fallback_tok :", comp["fallback_max_tokens"])
