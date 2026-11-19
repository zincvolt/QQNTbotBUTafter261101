from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")
if "MAIN_JUDGE_URL =" not in s:
    anchor = "AUTOREPLY_CONFIG_PATH = Path("
    idx = s.index(anchor)
    s = s[:idx] + 'MAIN_JUDGE_URL = "http://127.0.0.1:8080/v1/chat/completions"\nMAIN_JUDGE_KEY = "sk-llm-7d41c9e2"\n\n' + s[idx:]
    p.write_text(s, encoding="utf-8")
    print("constants inserted")
