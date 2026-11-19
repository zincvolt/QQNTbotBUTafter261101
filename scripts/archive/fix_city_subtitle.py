from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''        draw.text((60, y + 36), f"{ev['start']} ~ {ev['end']} · {ev['scale']}",
                  font=small, fill=(150, 156, 170))'''
new = '''        detail = " · ".join(
            x for x in (f"{ev['start']} ~ {ev['end']}", ev.get("scale", "")) if x
        )
        draw.text((60, y + 36), detail, font=small, fill=(150, 156, 170))'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("city subtitle fixed")
