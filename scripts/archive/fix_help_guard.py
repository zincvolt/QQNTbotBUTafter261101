from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''            if key == "help" and not (
                text.strip().startswith(("/", "／")) or re.search(NAME_CALL, text)
            ):
                return
'''
if old in s:
    s = s.replace(old, "", 1)
    p.write_text(s, encoding="utf-8")
    print("help guard removed")
else:
    print("guard not found")
