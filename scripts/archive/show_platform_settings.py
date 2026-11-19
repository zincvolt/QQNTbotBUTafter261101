import json
cfg = json.loads(open(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json", encoding="utf-8-sig").read())
print(json.dumps(cfg.get("platform_settings"), ensure_ascii=False)[:600])
print("platforms:", json.dumps(cfg.get("platform"), ensure_ascii=False)[:300])
