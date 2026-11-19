from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")

# 1) 加载器：读 reply.json 里的 reply_chance
loader = '''

REPLY_CONFIG_PATH = Path(r"D:\\QQNTBOT\\data\\reply.json")
_ar_chance_cache: dict = {"mtime": 0.0, "value": 1.0}


def load_reply_chance() -> float:
    """主动回复概率（判官说接了之后，还按这个概率再抽一次）。

    Returns:
        float: 0~1，1 表示判官说接就接。
    """
    global _ar_chance_cache
    try:
        stat = REPLY_CONFIG_PATH.stat()
    except OSError:
        return 1.0
    if stat.st_mtime == _ar_chance_cache["mtime"]:
        return _ar_chance_cache["value"]
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        value = float(raw.get("reply_chance", 1.0))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        value = 1.0
    value = max(0.0, min(1.0, value))
    _ar_chance_cache = {"mtime": stat.st_mtime, "value": value}
    return value

'''
if "def load_reply_chance" not in s:
    anchor = "\ndef load_autoreply_config()"
    s = s.replace(anchor, loader + anchor, 1)

# 2) 判官通过后再抽一次概率
old = '''            case "judge":
                return await self._judge_reply(event, cfg)'''
new = '''            case "judge":
                if not await self._judge_reply(event, cfg):
                    return False
                # 判官说接，再按概率收一次频率
                chance = load_reply_chance()
                if chance >= 1.0:
                    return True
                if random.random() < chance:
                    return True
                logger.info(f"group judge | 概率闸拦截 (chance={chance:.2f}) | {event.message_str[:30]}")
                return False'''
if old in s:
    s = s.replace(old, new, 1)
    print("gate inserted")

p.write_text(s, encoding="utf-8")
