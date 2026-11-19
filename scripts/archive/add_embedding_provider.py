"""Register a local embedding provider (NPU bge-small-zh on :8097) in AstrBot config."""

import json
import shutil
from pathlib import Path

CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
BACKUP = CFG.with_suffix(".json.bak-embed")

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
provs = cfg.setdefault("provider", [])

entry = {
    "id": "local-embed",
    "type": "openai_embedding",
    "provider_type": "embedding",
    "enable": True,
    "embedding_api_base": "http://127.0.0.1:8097/v1",
    "embedding_api_key": "sk-local-embed",
    "embedding_model": "bge-small-zh-v1.5",
    "timeout": 30,
}

index = next((i for i, p in enumerate(provs) if p.get("id") == "local-embed"), None)
if index is None:
    provs.append(entry)
    print("已追加 local-embed")
else:
    provs[index].update(entry)
    print("已更新 local-embed")

if not BACKUP.exists():
    shutil.copy2(CFG, BACKUP)
    print("配置已备份:", BACKUP.name)

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("写入完成，provider 数量:", len(provs))
