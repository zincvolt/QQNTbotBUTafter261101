import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").read_text(encoding="utf-8")
print("recent 在 city_list 前:", s.index('("recent"') < s.index('("city_list"'))
print("help 冲突保护:", "text.strip().startswith((\"/\", \"／\"))" in s)
