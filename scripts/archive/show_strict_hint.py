import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py").read_text(encoding="utf-8")
m = re.search(r'STRICT_HINT = (?:"""|\'\'\'|")(.*?)(?:"""|\'\'\'|")', s, re.S)
print(m.group(1).strip() if m else "未找到")
