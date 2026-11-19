import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\api_mode.json")
st = json.loads(p.read_text(encoding="utf-8"))
st["history_keep"] = 10
p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
print("history_keep =", st["history_keep"])
