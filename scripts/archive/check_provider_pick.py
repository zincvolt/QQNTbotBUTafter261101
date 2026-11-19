import json, sys
sys.path.insert(0, r"D:\QQNTBOT\apps\AstrBot")
cfg = json.loads(open(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json", encoding="utf-8-sig").read())
ps = cfg.get("provider_settings", {})
print("provider_pool:", ps.get("provider_pool"))
print("default_provider_id:", ps.get("default_provider_id"))
print("enable:", ps.get("enable"))
print("providers enable 状态:")
for p in cfg["provider"]:
    print("  ", p["id"], p.get("enable"))
