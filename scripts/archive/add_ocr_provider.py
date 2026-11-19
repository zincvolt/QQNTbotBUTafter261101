"""Register the dedicated OCR server as an image-caption provider."""

import json
from pathlib import Path

CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")

cfg = json.loads(CFG.read_text(encoding="utf-8"))

sources = cfg.setdefault("provider_sources", [])
if not any(s.get("id") == "ocr_source" for s in sources):
    sources.append(
        {
            "id": "ocr_source",
            "provider": "openai",
            "type": "openai_chat_completion",
            "provider_type": "chat_completion",
            "key": ["sk-ocr-local"],
            "api_base": "http://127.0.0.1:8083/v1",
            "timeout": 120,
            "proxy": "",
            "custom_headers": {},
        }
    )

providers = cfg.setdefault("provider", [])
if not any(p.get("id") == "vl-ocr" for p in providers):
    providers.append(
        {
            "id": "vl-ocr",
            "enable": True,
            "model": "PaddleOCR-VL-1.6",
            "provider_source_id": "ocr_source",
            "modalities": ["image", "text"],
            "custom_extra_body": {"max_tokens": 300, "temperature": 0},
        }
    )

ps = cfg["platform_settings"]
ps.setdefault("provider_settings", {})
cfg["provider_settings"]["default_image_caption_provider_id"] = "vl-ocr"
cfg["provider_settings"]["image_caption_prompt"] = (
    "用中文描述这张图：先写图上出现的所有文字（逐字照抄，不要翻译），"
    "再用一句话说画面是什么。总长度不超过 120 字。"
)
cfg["provider_ltm_settings"]["image_caption"] = True
cfg["provider_ltm_settings"]["image_caption_provider_id"] = "vl-ocr"

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("providers:", [p.get("id") for p in cfg["provider"]])
print("caption   :", cfg["provider_settings"]["default_image_caption_provider_id"])
