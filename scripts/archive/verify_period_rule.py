import json, re
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
rules = cfg["text_rules"]
samples = ["你好。（歪头）", "行吧。", "他说。（小声）我听见了。", "好的。。"]
for t in samples:
    out = t
    for r in rules:
        out = re.compile(r["pattern"]).sub(r["to"], out)
    print(f"{t!r} -> {out!r}")
