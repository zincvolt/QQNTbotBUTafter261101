"""Reduce 淋语 frequency and forbid 句号 entirely."""

import json
from pathlib import Path

PERSONA_FILE = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(PERSONA_FILE.read_text(encoding="utf-8"))["text"]

repl = {
    "- 全篇不用句号「。」，句末也不加；靠换行、语气词收尾":
        "- 任何情况下都不要出现句号「。」，句中句末都不许有；靠换行、语气词收尾",
    "- 淋语只是偶尔点缀：十句里带一句就够了（惹、噜、厚、靴靴、本可），别每句都挂":
        "- 淋语只是极偶尔的点缀：整场对话里用一两次就到顶了，大多数消息一个淋语词都别带",
    "- 一条消息最多带一个淋语词，别堆":
        "- 一条消息最多一个淋语词；连续几条都带淋语会显得很怪",
    "- 大部分时候说正常口语，别为了玩梗把话说得难懂":
        "- 默认说正常口语，玩梗是例外不是常态；不确定该不该用时就不用",
}
for old, new in repl.items():
    text = text.replace(old, new)

PERSONA_FILE.write_text(
    json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("chars:", len(text))
print("句号规则:", [l for l in text.splitlines() if "句号" in l])
print("淋语规则:", [l for l in text.splitlines() if "淋语只是" in l])
