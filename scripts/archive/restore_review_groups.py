import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\api_mode.json")
st = json.loads(p.read_text(encoding="utf-8"))
st["review_groups"] = {"942316942": True, "1128093050": True}
p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
print("review_groups 恢复:", st["review_groups"])
