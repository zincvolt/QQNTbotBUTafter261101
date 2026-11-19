from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
for line in (
    '    "不要重复使用同一句式或同一种自称，每条换说法；"\n',
    '    "不写性行为细节，暗示到为止；"\n',
):
    if line in s:
        s = s.replace(line, "", 1)
        print("reverted:", line.strip())
p.write_text(s, encoding="utf-8")
