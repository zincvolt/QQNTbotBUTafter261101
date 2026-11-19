import json
cfg = json.loads(open(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json", encoding="utf-8-sig").read())
for p in cfg["provider"]:
    if p["id"] in ("vl-ocr", "ocr-local", "vl-local", "deepseek"):
        print(p["id"], "enable=", p.get("enable"), "modalities=", p.get("modalities"))
print("caption provider:", cfg["provider_settings"].get("default_image_caption_provider_id"))
