from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
s = s.replace("    start_y = int(height * 0.34)", "    start_y = int(height * 0.26)")
s = s.replace("        alpha = int(232 * (i - start_y) / max(1, height - start_y))",
              "        alpha = int(246 * (i - start_y) / max(1, height - start_y))")
p.write_text(s, encoding="utf-8")
print("gradient darkened")
