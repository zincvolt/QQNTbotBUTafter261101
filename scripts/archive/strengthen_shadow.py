from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''    for x, y, text, font, _c in items:
        sd.text((x + 2, y + 3), text, font=font, fill=(0, 0, 0, 210))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))'''
new = '''    for x, y, text, font, _c in items:
        sd.text((x + 2, y + 3), text, font=font, fill=(0, 0, 0, 235))
        sd.text((x, y), text, font=font, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("shadow strengthened")
