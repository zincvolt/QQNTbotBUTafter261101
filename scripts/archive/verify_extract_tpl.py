import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py").read_text(encoding="utf-8")
m = re.search(r'EXTRACT_PROMPT = """(.*?)"""', s, re.S)
tpl = m.group(1)
try:
    tpl.format(user="x", bot="y")
    print("format 仍然可用（说明花括号没冲突）")
except KeyError as e:
    print("format 会炸:", e)
out = tpl.replace("{user}", "用户说的话").replace("{bot}", "机器人说的话")
print("replace 结果正常，长度", len(out))
