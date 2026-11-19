import json
from pathlib import Path

cp = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
cfg = json.loads(cp.read_text(encoding="utf-8-sig"))
ltm = cfg["provider_ltm_settings"]
print("before:", ltm.get("group_message_history_max_cnt"), ltm.get("group_message_max_cnt"),
      cfg["agent_runner"]["config"]["compression"]["max_turns"])
# 群上下文从 200 条砍到 40 条（约最近十几分钟），压缩窗口 40 轮 -> 12 轮
ltm["group_message_history_max_cnt"] = 40
ltm["group_message_max_cnt"] = 200
cfg["agent_runner"]["config"]["compression"]["max_turns"] = 12
cp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("after :", ltm["group_message_history_max_cnt"], ltm["group_message_max_cnt"],
      cfg["agent_runner"]["config"]["compression"]["max_turns"])

# 记忆注入：8 条 -> 4 条，且只召回 30 天内的
lp = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py")
s = lp.read_text(encoding="utf-8")
s = s.replace("MAX_INJECTED = 8", "MAX_INJECTED = 4", 1)
old = '"SELECT id, text, emb, created FROM facts WHERE uid = ? ORDER BY created DESC LIMIT 400",'
new = '"SELECT id, text, emb, created FROM facts WHERE uid = ? AND created >= ? "\n            "ORDER BY created DESC LIMIT 400",'
if old in s:
    s = s.replace(old, new, 1)
    # 补参数
    s = s.replace("(uid,),", "(uid, time.time() - 30 * 86400),", 1)
    print("recall window -> 30 days")
lp.write_text(s, encoding="utf-8")
print("MAX_INJECTED:", "MAX_INJECTED = 4" in s)
