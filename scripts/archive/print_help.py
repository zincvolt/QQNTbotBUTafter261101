import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").read_text(encoding="utf-8")
m = re.search(r'HELP_TEXT = """(.*?)"""', s, re.S)
print(m.group(1))
