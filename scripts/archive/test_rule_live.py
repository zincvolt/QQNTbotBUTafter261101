import json, re
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
rules = cfg["text_rules"]
def apply(t):
    for r in rules:
        t = re.compile(r["pattern"]).sub(r["to"], t)
    return t
for s in ["你好。（歪头）", "行吧。", "好的。。", "嗯。」"]:
    print(repr(s), "->", repr(apply(s)))
