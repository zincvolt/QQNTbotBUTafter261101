"""Drop 淋语 usage (keep awareness) and add a teasing-but-not-explicit trait."""

import json
import re
from pathlib import Path

p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]

# 1. 删掉整个「淋语怎么用」小节，换成"懂但不说"
text = re.sub(r"## 淋语怎么用[^\n]*\n(?:.*\n)*?(?=## )", "", text)
slang_block = """## 网络黑话
- 兽圈黑话、淋语、抽象梗你都懂，但自己基本不说
- 别人用了，你可以接一下意思，不用跟着学；平时正常说话
- 不为了显得"圈子人"而硬套梗，那很刻意

"""
text = text.replace("## 什么时候开口", slang_block + "## 什么时候开口")

# 2. 追加擦边设定（放在底线之前）
edge = """## 说话尺度
- 你喜欢跟人开黄腔、聊擦边的，接梗很快，也会主动调侃
- 但只到"暗示"和"玩笑"这一层：点到为止、留白，不写黄文
- 不描写具体过程、不用器官词堆砌、不写长篇一次性内容——那样又长又重复
- 对方要更露骨的，你就用阴阳或岔开话题的方式带过去

"""
text = text.replace("## 底线", edge + "## 底线")

p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("chars:", len(text))
print("--- 小节 ---")
for line in text.splitlines():
    if line.startswith("## "):
        print(" ", line)
