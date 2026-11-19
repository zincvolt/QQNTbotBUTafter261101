from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''            img.paste(
                _recent_row(ev, card_w, card_h, "", over, False),
                (margin, y),
                _recent_row(ev, card_w, card_h, "", over, False),
            )'''
new = '''            row = _recent_row(ev, card_w, card_h, "", over, False)
            img.paste(row, (margin, y), row)'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("dedup render")
