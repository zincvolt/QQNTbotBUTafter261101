from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

# 1) 配置加载函数（带 mtime 缓存）
loader = '''

REPLY_FILE = Path(r"D:\\QQNTBOT\\data\\reply.json")
_reply_cache: dict = {"mtime": 0.0, "data": None}


def load_reply_config() -> dict:
    """Read meme chance and text replacement rules, cached by mtime.

    Returns:
        Dict with ``meme_chance`` (float) and ``text_rules`` (list of dicts).
    """
    global _reply_cache
    default = {"meme_chance": MEME_CHANCE, "text_rules": []}
    try:
        stat = REPLY_FILE.stat()
    except OSError:
        return default
    if _reply_cache["data"] is not None and stat.st_mtime == _reply_cache["mtime"]:
        return _reply_cache["data"]
    try:
        raw = json.loads(REPLY_FILE.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return default
    data = {
        "meme_chance": float(raw.get("meme_chance", MEME_CHANCE)),
        "text_rules": [
            {"find": str(r.get("find", "")), "to": str(r.get("to", ""))}
            for r in raw.get("text_rules", [])
            if isinstance(r, dict) and r.get("find")
        ],
    }
    _reply_cache = {"mtime": stat.st_mtime, "data": data}
    return data

'''
if "def load_reply_config" not in s:
    anchor = "\ndef _group_activity()"
    s = s.replace(anchor, loader + anchor, 1)

# 2) 概率改成读配置
s = s.replace(
    "        if random.random() < MEME_CHANCE:\n            self._attach_meme(result, text)",
    "        if random.random() < load_reply_config()[\"meme_chance\"]:\n            self._attach_meme(result, text)",
)

# 3) 文本替换：在 mute 判断之前处理 plain 文本
old = '''        if text and NON_ANSWER.match(text):'''
new = '''        for rule in load_reply_config()["text_rules"]:
            for comp in result.chain:
                inner = getattr(comp, "text", None)
                if isinstance(inner, str) and rule["find"] in inner:
                    comp.text = inner.replace(rule["find"], rule["to"])
        if text and NON_ANSWER.match(text):'''
if old in s and "text_rules\")" not in s.split("if text and NON_ANSWER")[0]:
    s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("loader:", "def load_reply_config" in s)
print("chance:", "load_reply_config()[\"meme_chance\"]" in s)
