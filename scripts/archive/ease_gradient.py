from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "        alpha = int(246 * (i - start_y) / max(1, height - start_y))",
    "        ratio = (i - start_y) / max(1, height - start_y)\n"
    "        alpha = int(246 * (ratio ** 0.45))",
)
p.write_text(s, encoding="utf-8")
print("eased gradient")
