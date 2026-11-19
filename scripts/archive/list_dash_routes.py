import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\dashboard\app.py").read_text(encoding="utf-8")
routes = sorted(set(re.findall(r'@app\.(?:get|post|put|delete)\("([^"]+)"', s)))
print("面板接口:", len(routes))
for r in routes: print(" ", r)
