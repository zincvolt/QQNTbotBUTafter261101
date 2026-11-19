from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
# STRICT_HINT 补一句：它能发表情包
old = '"不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字）"'
new = '"不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字；"\n    "你确实能发表情包，别声称自己没有）"'
if old in s and "别声称自己没有" not in s:
    s = s.replace(old, new)
    print("hint updated")
p.write_text(s, encoding="utf-8")
