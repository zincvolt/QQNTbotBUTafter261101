import json
from pathlib import Path
from datetime import datetime

p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]

block = """不确定的事别编：
- 活动、赛事、画师、日期、数字，没听过就说没听过，别现编
- 猜的就直说是猜的，别当成事实讲
- 说错了被纠正就认，别硬圆

"""
if "不确定的事别编" not in text:
    text = text.replace("## 底线", block + "## 底线")
p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("persona chars:", len(text))

# 冷却改为 0：回完就能回下一条
peer = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = peer.read_text(encoding="utf-8")
s = s.replace("COOLDOWN_SECONDS = 60    # 自动接话的冷却（同会话）",
              "COOLDOWN_SECONDS = 0     # 回完就能接下一句，靠判官控制频率")
peer.write_text(s, encoding="utf-8")
print("cooldown:", "COOLDOWN_SECONDS = 0" in s)
