from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

# 主办方可能是 dict / list / str，统一取名字
old = '''        name = str(item.get("name", "")).strip()
        if not name:
            continue'''
new = '''        name = str(item.get("name", "")).strip()
        if not name or name.isdigit():
            continue

        raw_org = item.get("organization") or item.get("organizations") or ""
        if isinstance(raw_org, dict):
            org = str(raw_org.get("name", "")).strip()
        elif isinstance(raw_org, list):
            names = []
            for one in raw_org:
                if isinstance(one, dict):
                    names.append(str(one.get("name", "")).strip())
                elif isinstance(one, str):
                    names.append(one.strip())
            org = "、".join(n for n in names if n)
        else:
            org = str(raw_org).strip()'''
if old in s:
    s = s.replace(old, new, 1)
    print("org parsing added")

s = s.replace('                "org": str(item.get("organization") or ""),', '                "org": org,', 1)
# 城市也可能是 dict
s = s.replace(
    '                "city": str(item.get("placeName") or item.get("region") or ""),',
    '                "city": str(item.get("placeName") or item.get("region") or "")[:24],',
    1,
)
p.write_text(s, encoding="utf-8")
