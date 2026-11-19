from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''                following = [e for e in events if e["start_ts"] >= hits[0]["start_ts"]][1:3]'''
new = '''                # "之后还有"也只看该城市，避免混进外地展
                following = [e for e in hits[1:3]]'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("city following fixed")
