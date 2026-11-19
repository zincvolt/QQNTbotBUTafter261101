import json
from pathlib import Path
CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))

fix = {
    "vl-local_source": {"key": ["sk-vl-local"], "provider": "openai", "timeout": 120,
                        "proxy": "", "custom_headers": {}},
    "ocr-local_source": {"key": ["sk-ocr-local"], "provider": "openai", "timeout": 120,
                         "proxy": "", "custom_headers": {}},
}
for src in cfg.get("provider_sources", []):
    patch = fix.get(src.get("id"))
    if patch:
        src.update(patch)
        print("修复 source:", src["id"], "key=", src["key"], "api_base=", src.get("api_base"))

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("已写入")
