import json
cfg = json.loads(open(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json", encoding="utf-8-sig").read())
print(json.dumps(cfg.get("agent_runner"), ensure_ascii=False, indent=1)[:800])
