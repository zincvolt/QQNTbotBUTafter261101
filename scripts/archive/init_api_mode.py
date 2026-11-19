"""Write the default api_mode state so the switch commands have a base."""

import json
from pathlib import Path

STATE = Path(r"D:\QQNTBOT\data\api_mode.json")

if not STATE.exists():
    STATE.write_text(json.dumps({
        "mode": "local",
        "save_token": True,
        "daily_limit": 200000,
        "used": {"date": "", "tokens": 0},
        "review_groups": {"942316942": True, "1128093050": True},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已写入默认状态")
else:
    print("状态文件已存在:", STATE.read_text(encoding="utf-8")[:200])
