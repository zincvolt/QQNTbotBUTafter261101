import json
from pathlib import Path
CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
provs = cfg.setdefault("provider", [])
entry = {
    "id": "deepseek",
    "type": "openai_chat_completion",
    "provider_type": "chat_completion",
    "enable": False,
    "api_key": "填你的 DeepSeek API Key",
    "api_base": "https://api.deepseek.com/v1",
    "model": "deepseek-flash",
    "custom_extra_body": {"max_tokens": 300, "temperature": 0.8},
}
idx = next((i for i, p in enumerate(provs) if p.get("id") == "deepseek"), None)
if idx is None:
    provs.append(entry)
    print("已加入 deepseek provider（默认停用，等你填 key）")
else:
    print("deepseek provider 已存在")
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
