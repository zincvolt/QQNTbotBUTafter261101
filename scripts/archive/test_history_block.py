import re, sys
from pathlib import Path
src = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py").read_text(encoding="utf-8")
ns = {}
for name in ("GROUP_HISTORY_HEADER", "GROUP_HISTORY_FOOTER"):
    m = re.search(rf"{name} = \((.*?)\n\)", src, re.S)
    exec(f"{name} = ({m.group(1)}\n)", ns)
records = ["[电池叔叔不约/23:10:02]:  今天好累", "[沐辉/23:10:20]:  我也是"]
print(ns["GROUP_HISTORY_HEADER"] + "\n".join(records) + ns["GROUP_HISTORY_FOOTER"])
