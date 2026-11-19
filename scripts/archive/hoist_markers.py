from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

helper = '''MARKER_RE = re.compile(r"&&[^&\\r\\n]{1,100}&&")


def _hoist_markers(text: str) -> str:
    """Move every ``&&...&&`` marker to the end of the message.

    表情插件要求标记在句末；模型经常写在句中，这里统一挪到最后并去重。

    Args:
        text: Raw reply text that may contain markers.

    Returns:
        Text with markers collected at the end, body otherwise untouched.
    """
    markers = MARKER_RE.findall(text)
    if not markers:
        return text
    body = MARKER_RE.sub("", text)
    body = re.sub(r"[ \\t]{2,}", " ", body).strip()
    unique: list[str] = []
    for marker in markers:
        if marker not in unique:
            unique.append(marker)
    return (body + "\\n" + " ".join(unique)).strip()


'''

if "_hoist_markers" not in s:
    anchor = "@filter.on_decorating_result()"
    s = s.replace(anchor, helper + anchor, 1)
    print("helper 已插入")

old = '''        if random.random() < load_reply_config()["meme_chance"]:
            self._attach_meme(result, text, event.message_str or "")'''
new = '''        # 先把 &&情绪&& 之类的标记挪到句末，再套正则，避免规则改坏标记
        for comp in result.chain:
            inner = getattr(comp, "text", None)
            if isinstance(inner, str):
                comp.text = _hoist_markers(inner)
        text = result.get_plain_text().strip()
        if random.random() < load_reply_config()["meme_chance"]:
            self._attach_meme(result, text, event.message_str or "")'''
if old in s:
    s = s.replace(old, new, 1)
    print("on_decorating_result 已接入标记搬家")

p.write_text(s, encoding="utf-8")
