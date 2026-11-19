import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py").read_text(encoding="utf-8")
m = re.search(r'EXTRACT_PROMPT\s*=\s*(?:"""(.*?)"""|f"""(.*?)""")', s, re.S)
print(m.group(1) or m.group(2) if m else "not found")
