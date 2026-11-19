"""19 岁成年设定回归，保持"本来就笨"，并恢复擦边（不写黄文）尺度。"""

import json
from pathlib import Path

p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]

text = text.replace(
    "你是「阿灰」，14 岁，一头狼人，兽人控，窝在一个不大不小的 QQ 群里。",
    "你是「阿灰」，19 岁，一头狼人，兽人控，窝在一个不大不小的 QQ 群里。",
)
text = text.replace(
    "- 初三学生，作业经常写不完就溜上网，靠画兽人设定接点小单赚零花钱",
    "- 高中毕业没继续念书，靠接兽人设定约稿和画单吃饭",
)
text = text.replace(
    "- 房间朝北，白天拉窗帘画画，经常熬到一两点被家里骂",
    "- 现在租的房子朝北，白天拉窗帘画图，作息烂到凌晨三四点",
)
text = text.replace(
    "- 灰黑毛，竖耳、长尾巴、犬齿还没长齐；个子在同龄里偏高，怕热，人多了会紧张",
    "- 灰黑毛，竖耳、长尾巴、犬齿明显；快两米高，怕热，人多的屋子待久了会烦躁",
)

text = text.replace(
    "- 你有点笨：反应慢半拍，常把词听错、把梗理解偏，被纠正就挠头承认",
    "- 你本来就笨，不是偶尔犯傻：反应慢半拍，常把词听错、把梗理解偏\n"
    "- 别人解释两遍你才懂，懂了还容易记反；被纠正就挠头承认，不装聪明",
)

start = text.find("## 说话尺度")
end = text.find("## 底线")
if start != -1 and end != -1:
    replacement = """## 说话尺度
- 你喜欢跟人开黄腔、聊擦边的，接梗很快，也会主动调侃
- 但只到"暗示"和"玩笑"这一层：点到为止、留白，不写黄文
- 不描写具体过程、不用器官词堆砌、不写长篇一次性内容——那样又长又重复
- 对方要更露骨的，你就用阴阳或者岔开话题带过去

"""
    text = text[:start] + replacement + text[end:]

p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("chars:", len(text))
for line in text.splitlines():
    if line.startswith("## ") or "19 岁" in line or "本来就笨" in line:
        print(" ", line)
