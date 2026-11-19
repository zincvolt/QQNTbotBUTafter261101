from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''    elif jrrp >= 40:
        level, color = "平", (150, 190, 150)
    elif jrrp >= 25:
        level, color = "小凶", (120, 160, 210)'''
new = '''    elif jrrp >= 40:
        level, color = "平", (150, 190, 150)
    elif jrrp >= 20:
        level, color = "小凶", (120, 160, 210)'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("threshold tuned")
