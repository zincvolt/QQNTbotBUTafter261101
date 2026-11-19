import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"].rstrip("\n")

block = """

不确定的事别编：
- 活动、赛事、画师、日期、数字，没听过就说没听过，别现编
- 猜的就直说是猜的，别当事实讲
- 被纠正就认，别硬圆"""

if "不确定的事别编" not in text:
    text = text + block
p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("chars:", len(text))
print(text)
