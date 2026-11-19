import re
MARKER_RE = re.compile(r"&&[^&\r\n]{1,100}&&")
def _hoist_markers(text):
    markers = MARKER_RE.findall(text)
    if not markers:
        return text
    body = MARKER_RE.sub("", text)
    body = re.sub(r"[ \t]{2,}", " ", body).strip()
    unique = []
    for m in markers:
        if m not in unique:
            unique.append(m)
    return (body + "\n" + " ".join(unique)).strip()

rule = re.compile(r"。 (?=\.)" if False else r"。(?=\s|$|[（(\[【「『])")
cases = [
    "今天好累&&难过&&，我先睡了。",
    "&&开心&&这游戏真好玩。&&meme:abc&&",
    "他说。（小声）我听见了。",
    "没有标记的一句话。",
]
for c in cases:
    out = _hoist_markers(c)
    out = rule.sub("~", out)
    print(repr(c), "->", repr(out))
