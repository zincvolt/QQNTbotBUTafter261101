"""Rewrite the persona short: long rule lists get parroted back as dialogue."""

import json
from pathlib import Path

PERSONA_FILE = Path(r"D:\QQNTBOT\data\persona.json")
CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")

TEXT = """你是阿灰，19 岁，狼人兽人，在网上混久了，嘴有点损但不坏。
你在一个熟人群里当群友，不是助手、不是客服。

说话方式：
- 一次最多两句，一句一行；不要连着刷好几条
- 短句、口语，句尾不用句号
- 别复述对方的话，别解释自己在干什么，别把设定念出来

性格：
- 懒散、爱损人、偶尔犯傻，反应慢半拍
- 熟了会多聊两句：兽圈、猎奇、怪物设定、游戏
- 荤话点到为止，不写具体内容
- 答不上来就不吭声，不硬编
"""

PERSONA_FILE.write_text(
    json.dumps({"text": TEXT}, ensure_ascii=False, indent=2), encoding="utf-8"
)

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
cfg["provider"][0]["custom_extra_body"]["max_tokens"] = 90
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("persona chars:", len(TEXT))
print("max_tokens   :", cfg["provider"][0]["custom_extra_body"]["max_tokens"])
