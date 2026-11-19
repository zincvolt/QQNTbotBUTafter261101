from pathlib import Path
p = Path(r"D:\QQNTBOT\_tmp_furcon_new.py")
s = p.read_text(encoding="utf-8")

# 1) 近期展从 city_list 里移出，交给 recent
s = s.replace(
    '("city_list", re.compile(r"(有什么展|有哪些展|有啥展|有什么兽聚|哪有展|有什么活动|近期展|近期兽聚)")),',
    '("city_list", re.compile(r"(有什么展|有哪些展|有啥展|有什么兽聚|哪有展|有什么活动)")),',
)
# 2) recent 提前（放在 city_list 之前）
lines = s.splitlines()
recent_line = next(l for l in lines if l.strip().startswith('("recent"'))
s = s.replace(recent_line + "\n", "", 1)
anchor = '    ("city_list", re.compile('
s = s.replace(anchor, recent_line + "\n" + anchor, 1)

# 3) help 必须带斜杠或喊名字，避免和系统 /help 冲突
s = s.replace(
    '''            if key == "help":''',
    '''            if key == "help" and not (
                text.strip().startswith(("/", "／")) or re.search(NAME_CALL, text)
            ):
                return
            if key == "help":''',
)
p.write_text(s, encoding="utf-8")
print("patched")
