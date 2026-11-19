import re
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py").read_text(encoding="utf-8")
block = re.search(r"MEME_EMOTION_WORDS = \{[\s\S]*?\n\}", s).group(0)
ns = {}
exec(block, ns)
LEX = ns["MEME_EMOTION_WORDS"]

def pick(user, bot):
    scores = {}
    for name, words in LEX.items():
        if not words: continue
        hb = sum(1 for w in words if w and w in bot)
        hu = sum(1 for w in words if w and w in user)
        if hb or hu: scores[name] = hb + hu*2
    if not scores: return "随机", {}
    best = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return best[0][0], dict(best[:3])

cases = [
    ("今天加班到十点，好累", "那你早点睡吧"),
    ("哈哈哈哈笑死我了", "嘿嘿是吧"),
    ("呜呜我分手了", "别难过"),
    ("卧槽真的假的", "我也刚知道"),
    ("你们吃了吗", "刚吃完"),
    ("谢谢啦", "客气啥"),
    ("这也太离谱了吧", "就是"),
    ("好的", "嗯"),
]
for u, b in cases:
    cat, detail = pick(u, b)
    print(f"[{u}] -> {cat}  {detail}")
