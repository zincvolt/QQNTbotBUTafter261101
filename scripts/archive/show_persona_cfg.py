import json
cfg = json.loads(open(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json", encoding="utf-8-sig").read())
print("persona:", json.dumps(cfg.get("persona"), ensure_ascii=False)[:200])
print("agent_runner persona:", json.dumps(cfg["agent_runner"]["config"].get("persona"), ensure_ascii=False))
