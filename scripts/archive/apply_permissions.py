"""Apply access-control settings: single admin + explicit allowlist."""

import json
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot")
CFG = ROOT / "data" / "cmd_config.json"

ADMIN = "1154487120"
GROUP = "1128093050"
DM_UMO = f"qq:FriendMessage:{ADMIN}"

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))

cfg["admins_id"] = [ADMIN]

ps = cfg["platform_settings"]
ps["enable_id_white_list"] = True
ps["id_whitelist"] = [DM_UMO, GROUP]
ps["id_whitelist_log"] = True
ps["wl_ignore_admin_on_group"] = True
ps["wl_ignore_admin_on_friend"] = True

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("admins_id   :", cfg["admins_id"])
print("id_whitelist:", ps["id_whitelist"])

napcat = Path(r"D:\QQNTBOT\apps\NapCat\config\webui.json")
if napcat.exists():
    w = json.loads(napcat.read_text(encoding="utf-8-sig"))
    w["host"] = "127.0.0.1"
    napcat.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8")
    print("napcat webui host:", w["host"])
