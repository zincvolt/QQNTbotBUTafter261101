import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
ltm = cfg["provider_ltm_settings"]
print("群消息历史上限:", ltm.get("group_message_history_max_cnt"))
print("群消息上下文:", ltm.get("group_message_max_cnt"))
print("压缩 max_turns:", cfg["agent_runner"]["config"]["compression"]["max_turns"])
