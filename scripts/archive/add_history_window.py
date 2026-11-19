from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 1) 时间窗加载器（读 reply.json 的 history_minutes）
loader = '''

def load_history_window() -> float:
    """群上下文时间窗（秒），来自 data/reply.json 的 history_minutes。

    Returns:
        float: 时间窗秒数，默认 1800（30 分钟）。
    """
    global _ar_chance_cache
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        minutes = float(raw.get("history_minutes", 30))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 1800.0
    minutes = max(1.0, min(240.0, minutes))
    return minutes * 60.0

'''
if "def load_history_window" not in s:
    s = s.replace("\n\ndef load_autoreply_config()", loader + "\ndef load_autoreply_config()", 1)

p.write_text(s, encoding="utf-8")
print("loader:", "def load_history_window" in s)
