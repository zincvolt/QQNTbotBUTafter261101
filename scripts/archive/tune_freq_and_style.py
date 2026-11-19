import json
from pathlib import Path

# 1) reply_chance = 1.0（不额外拦，靠判官温度）
rp = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(rp.read_text(encoding="utf-8"))
d["reply_chance"] = 1.0
rp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("reply_chance:", d["reply_chance"])

# 2) repeat_penalty 1.12
cp = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(cp.read_text(encoding="utf-8-sig"))
body = cfg["provider"][0]["custom_extra_body"]
body["repeat_penalty"] = 1.12
cp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("repeat_penalty:", body["repeat_penalty"])

# 3) 判官温度 0 -> 0.7
gp = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = gp.read_text(encoding="utf-8")
old = '"temperature": 0,'
if old in s:
    s = s.replace(old, '"temperature": 0.7,', 1)
    gp.write_text(s, encoding="utf-8")
    print("judge temperature -> 0.7")

# 4) STRICT_HINT 加两条
pp = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
ps = pp.read_text(encoding="utf-8")
if "不要重复使用同一句式" not in ps:
    ps = ps.replace(
        '"不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字；"',
        '"不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字；"\n'
        '    "不要重复使用同一句式或同一种自称，每条换说法；"\n'
        '    "不写性行为细节，暗示到为止；"',
    )
    pp.write_text(ps, encoding="utf-8")
    print("STRICT_HINT updated")
