from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''    for x, y, text, font, _c in items:
        sd.text((x + 2, y + 3), text, font=font, fill=(0, 0, 0, 235))
        sd.text((x, y), text, font=font, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))'''
new = '''    for x, y, text, font, _c in items:
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 3)):
            sd.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 225))
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("halo shadow")
