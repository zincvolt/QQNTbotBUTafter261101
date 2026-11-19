import re
pat = re.compile(r"。(\s|$)")
pat2 = re.compile(r"。(\s|$)")
p3 = re.compile(r"。")
import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
pat = re.compile(cfg["text_rules"][0]["pattern"])
for t in ["行吧。那我先躺一会。", "第一句。第二句。", "他说。你好。。"]:
    print(repr(t), "->", repr(pat.sub("~", t)))
