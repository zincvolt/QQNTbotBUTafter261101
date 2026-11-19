import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\furcon_enabled.json")
p.write_text(json.dumps({"groups": {"942316942": True, "1128093050": True}}, ensure_ascii=False, indent=2), encoding="utf-8")
print(p.read_text(encoding="utf-8"))
