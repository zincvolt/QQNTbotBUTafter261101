from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py")
s = p.read_text(encoding="utf-8")

old = '''EXTRACT_PROMPT.format(user=user_text[:800], bot=bot_text[:800])'''
new = '''EXTRACT_PROMPT.replace("{user}", user_text[:800]).replace(
                "{bot}", bot_text[:800]
            )'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("format -> replace")
else:
    print("pattern missing")
