from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py").read_text(encoding="utf-8")
lines = s.splitlines()
for i, line in enumerate(lines, 1):
    if "lines.append" in line or "记忆" in line or "system_prompt +=" in line:
        print(i, line.strip()[:110])
