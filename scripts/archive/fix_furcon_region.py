from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    'hits = [e for e in events if city in (e["city"] + e["region"])]',
    'hits = [e for e in events if city in (str(e.get("city", "")) + str(e.get("region", "")))]',
)
p.write_text(s, encoding="utf-8")
print("region fallback added")
