"""Fix slash detection: wake prefix is stripped, so read the raw message."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) match_command 改为接受"是否是斜杠命令"的显式标志
old_sig = '''def match_command(text: str) -> tuple[str, str]:'''
new_sig = '''def match_command(text: str, slash: bool = False) -> tuple[str, str]:'''
s = s.replace(old_sig, new_sig, 1)

old_body = '''    body = re.sub(r"^\\[[^\\]]*\\]\\s*", "", text).strip()
    body = re.sub(rf"@{NAME_CALL}\\s*", "", body)
    has_slash = bool(re.match(r"^\\s*[/／]", body))
    called = bool(re.search(NAME_CALL, body))
    body_clean = re.sub(r"^\\s*[/／]\\s*", "", body).strip()

    city = ""
    for name in CITY_NAMES:
        if name in body_clean:
            city = name
            break

    for key, pattern in COMMANDS:
        target = body_clean if has_slash else body_clean
        if pattern.search(target):
            if key in ("city_next", "city_past") or key == "city_list":
                return (key if city or key == "city_list" else "city_all"), city
            if not (has_slash or called):
                continue
            return key, city

    if (has_slash or called) and city:
        return "city_list", city
    return "", ""'''
new_body = '''    body = re.sub(r"^\\[[^\\]]*\\]\\s*", "", text).strip()
    body = re.sub(rf"@{NAME_CALL}\\s*", "", body)
    called = bool(re.search(NAME_CALL, body))
    body_clean = re.sub(r"^\\s*[/／]\\s*", "", body).strip()
    if not (slash or called):
        return "", ""

    city = ""
    for name in CITY_NAMES:
        if name in body_clean:
            city = name
            break

    for key, pattern in COMMANDS:
        if pattern.search(body_clean):
            if key.startswith("city_"):
                return key, city
            return key, city

    if city:
        return "city_list", city
    return "", ""'''
if old_body in s:
    s = s.replace(old_body, new_body, 1)
    print("match_command rewritten")

# 2) 处理器：从原始消息判断斜杠，并记录调试日志
old_head = '''        text = (event.message_str or "").strip()
        if not text:
            return
        key, city = match_command(text)
        if not key:
            return'''
new_head = '''        text = (event.message_str or "").strip()
        if not text:
            return

        raw = ""
        msg_obj = getattr(event, "message_obj", None)
        raw_msg = getattr(msg_obj, "raw_message", None)
        if isinstance(raw_msg, dict):
            raw = str(raw_msg.get("raw_message") or "")
        elif isinstance(raw_msg, str):
            raw = raw_msg
        slash = raw.lstrip().startswith(("/", "／")) or text.lstrip().startswith(
            ("/", "／")
        )

        key, city = match_command(text, slash=slash)
        logger.info(f"[furcon] recv slash={slash} key={key or '-'} text={text[:24]}")
        if not key:
            return'''
if old_head in s:
    s = s.replace(old_head, new_head, 1)
    print("handler reads raw message")

PLUGIN.write_text(s, encoding="utf-8")

# 3) peer 插件：任何以斜杠开头的消息都不进模型
PEER = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
p = PEER.read_text(encoding="utf-8")
anchor = '''        if INJECTION.search(text):'''
guard = '''        # 以斜杠开头的消息一律当指令处理，不送进大模型
        raw_msg = None
        msg_obj = getattr(event, "message_obj", None)
        if msg_obj is not None:
            raw_msg = getattr(msg_obj, "raw_message", None)
        raw_text = ""
        if isinstance(raw_msg, dict):
            raw_text = str(raw_msg.get("raw_message") or "")
        elif isinstance(raw_msg, str):
            raw_text = raw_msg
        if raw_text.lstrip().startswith(("/", "／")) or text.startswith(("/", "／")):
            logger.info(f"[peer] slash command not sent to model: {text[:30]}")
            event.stop_event()
            return

        if INJECTION.search(text):'''
if "slash command not sent to model" not in p:
    p = p.replace(anchor, guard, 1)
    PEER.write_text(p, encoding="utf-8")
    print("peer slash guard added")
