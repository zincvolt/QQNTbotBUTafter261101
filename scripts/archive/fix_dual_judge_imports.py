from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

if "\nimport httpx\n" not in s:
    s = s.replace("from pathlib import Path", "from pathlib import Path\n\nimport httpx", 1)
    print("httpx imported")

if "MAIN_JUDGE_URL" not in s:
    anchor = 'AUTOREPLY_CONFIG_PATH = Path(r"D:\\QQNTBOT\\data\\autoreply.json")'
    const = ('MAIN_JUDGE_URL = "http://127.0.0.1:8080/v1/chat/completions"\n'
             'MAIN_JUDGE_KEY = "sk-llm-7d41c9e2"\n\n' + anchor)
    s = s.replace(anchor, const, 1)
    print("constants added")

p.write_text(s, encoding="utf-8")
