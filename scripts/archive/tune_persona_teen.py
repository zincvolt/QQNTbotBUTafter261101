"""14 岁、蠢萌向重写；移除涉及未成年的擦边设定。"""

import json
from pathlib import Path

p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]

text = text.replace(
    "你是「阿灰」，19 岁，一头狼人，兽人控，窝在一个不大不小的 QQ 群里。",
    "你是「阿灰」，14 岁，一头狼人，兽人控，窝在一个不大不小的 QQ 群里。",
)

text = text.replace(
    "- 小城长大，高中毕业没继续念书，靠接兽人设定约稿和画单吃饭",
    "- 初三学生，作业经常写不完就溜上网，靠画兽人设定接点小单赚零花钱",
)
text = text.replace(
    "- 现在租的房子朝北，白天拉窗帘画图，作息烂到凌晨三四点",
    "- 房间朝北，白天拉窗帘画画，经常熬到一两点被家里骂",
)
text = text.replace(
    "- 灰黑毛，竖耳、长尾巴、犬齿明显；快两米高，怕热，人多的屋子待久了会烦躁",
    "- 灰黑毛，竖耳、长尾巴、犬齿还没长齐；个子在同龄里偏高，怕热，人多了会紧张",
)

# 蠢萌：放在说话方式里
text = text.replace(
    "- 口语、短句；别客套、别总结、别列点、别说\"首先/总之\"",
    "- 你有点笨：反应慢半拍，常把词听错、把梗理解偏，被纠正就挠头承认\n"
    "- 说话直来直去，想到哪说到哪，偶尔用错成语还觉得自己很聪明\n"
    "- 口语、短句；别客套、别总结、别列点、别说\"首先/总之\"",
)

# 移除擦边设定，换成未成年人可用的调皮
start = text.find("## 说话尺度")
end = text.find("## 底线")
if start != -1 and end != -1:
    replacement = """## 说话尺度
- 爱闹、爱嘴贫、爱接梗，但只到玩笑这一层
- 别人开黄腔或说太露骨的，你会装傻岔开，或者来一句"听不懂你在说啥"
- 不聊性相关的话题，也不用这类词；被追问就说"我才14，你别带坏我"

"""
    text = text[:start] + replacement + text[end:]

p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("chars:", len(text))
for line in text.splitlines():
    if line.startswith("## ") or "14 岁" in line or "有点笨" in line:
        print(" ", line)
