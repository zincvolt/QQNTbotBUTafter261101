import json
from pathlib import Path

# 判官温度 0.7 -> 0.5（温度对通过率几乎无影响，留一点随机性即可）
gp = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = gp.read_text(encoding="utf-8")
s = s.replace('"temperature": 0.7,', '"temperature": 0.5,', 1)
gp.write_text(s, encoding="utf-8")

# 频率靠显式闸：0.45
rp = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(rp.read_text(encoding="utf-8"))
d["reply_chance"] = 0.45
rp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("judge temp: 0.5  reply_chance:", d["reply_chance"])
