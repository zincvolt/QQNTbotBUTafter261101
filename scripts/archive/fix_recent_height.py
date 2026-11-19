from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "    rows = (len(upcoming) + len(past) + 1) // 2 + 1",
    "    rows = max(1, (len(upcoming) + len(past) + 1) // 2)",
)
p.write_text(s, encoding="utf-8")
print("height fixed")
