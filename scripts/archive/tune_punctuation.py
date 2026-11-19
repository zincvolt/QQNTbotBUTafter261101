import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]

old = "- 任何情况下都不要出现句号「。」，句中句末都不许有；靠换行、语气词收尾"
new = ("- 句末一般不加句号；但句号当停顿用是可以的，比如「。。」「，，。」这种\n"
       "- 别每句都规规矩矩收句号，那样像客服；一口气说几句时用逗号或直接断行")
text = text.replace(old, new)

old2 = "- 淋语后面不要接句号，看起来很奇怪；整条消息本来就不该有句号"
new2 = "- 淋语词后面别紧跟着一个标准句号，看着别扭；要停顿用逗号或「。。」"
text = text.replace(old2, new2)

p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("chars:", len(text))
for line in text.splitlines():
    if "句号" in line:
        print(" ", line)
