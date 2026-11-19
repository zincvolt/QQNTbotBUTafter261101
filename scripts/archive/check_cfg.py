import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8"))
ps = cfg["platform_settings"]
print("admins_id :", cfg["admins_id"])
print("whitelist :", ps["id_whitelist"])
seg = ps["segmented_reply"]
print("segmented :", seg["enable"], seg["interval_method"], seg["interval"])
print("regex     :", seg["regex"])
print("max_tokens:", cfg["provider"][0]["custom_extra_body"]["max_tokens"])
print("persona   :", cfg["agent_runner"]["config"]["persona"]["persona_id"])
