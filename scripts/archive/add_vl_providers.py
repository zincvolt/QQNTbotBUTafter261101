import json
from pathlib import Path
CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
provs = cfg.setdefault("provider", [])

wanted = [
    {"id": "vl-local", "type": "openai_chat_completion", "provider_type": "chat_completion",
     "enable": True, "api_key": "sk-vl-local", "api_base": "http://127.0.0.1:8085/v1",
     "model": "Qwen3VL-4B-Instruct", "modalities": ["image", "text"],
     "custom_extra_body": {"max_tokens": 200, "temperature": 0.2}},
    {"id": "ocr-local", "type": "openai_chat_completion", "provider_type": "chat_completion",
     "enable": True, "api_key": "sk-ocr-local", "api_base": "http://127.0.0.1:8083/v1",
     "model": "PaddleOCR-VL-1.6", "modalities": ["image", "text"],
     "custom_extra_body": {"max_tokens": 300, "temperature": 0}},
]
for entry in wanted:
    idx = next((i for i, p in enumerate(provs) if p.get("id") == entry["id"]), None)
    if idx is None:
        provs.append(entry)
        print("新增 provider:", entry["id"], entry["model"], entry["api_base"])
    else:
        provs[idx].update(entry)
        print("更新 provider:", entry["id"])
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("provider 总数:", len(provs))
