from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")
if "\nimport time\n" not in s:
    s = s.replace("import random\nimport re", "import random\nimport re\nimport time", 1)
    p.write_text(s, encoding="utf-8")
    print("time imported")
else:
    print("already imported")
