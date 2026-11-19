import json, sys
from pathlib import Path
sys.path.insert(0, r"D:\QQNTBOT\apps\AstrBot")
raw = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
text = "行吧。那我先躺一会。"
for r in raw["text_rules"]:
    text = text.replace(r["find"], r["to"])
print("原文: 行吧。那我先躺一会。")
print("替换后:", text)
print("概率:", raw["meme_chance"])
