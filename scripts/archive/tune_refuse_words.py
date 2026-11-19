from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
old = '''    "拒绝": {"不行": 2, "不要": 1, "拒绝": 2, "别": 1, "不用": 1, "免了": 2,
             "不同意": 2, "算了": 1},'''
new = '''    "拒绝": {"不行": 2, "不要": 2, "拒绝": 2, "别": 1, "不用": 1, "免了": 2,
             "不同意": 2, "算了": 1, "不想": 2, "不去": 2, "不要了": 2},'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("refuse words added")
