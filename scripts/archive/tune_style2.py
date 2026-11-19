"""Rewrite the QQ style block, cap reply length, switch to human-like delays."""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot")
DB = ROOT / "data" / "data_v4.db"
CFG = ROOT / "data" / "cmd_config.json"

STYLE = """## QQ 聊天风格（优先级最高，覆盖上面所有叙事要求）
- 这是手机 QQ 聊天，不是写小说：一次最多 3 行，每行不超过 18 字
- 一句话一行，行与行之间不空行；每行会被当成一条独立消息发出去
- 句末不加句号「。」；用空格、语气词或换行收尾
- 说人话：口语、短句、别客套、别总结、别列点、别用「首先/总之/综上」
- 不知道就直接说不知道，一句话说完，绝对不要硬编内容凑字数
- 不用敬语，把「您」换成「你」
- 动作神态最多一处，能省就省；不要每句都接问句
"""

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT system_prompt FROM personas WHERE persona_id = 'grey'")
prompt = cur.fetchone()[0]
prompt = re.sub(r"## QQ 聊天风格.*?(?=\Z|## )", "", prompt, flags=re.S).rstrip()
prompt = prompt + "\n\n" + STYLE
cur.execute(
    "UPDATE personas SET system_prompt = ?, updated_at = datetime('now') WHERE persona_id = 'grey'",
    (prompt,),
)
con.commit()
con.close()

cfg = json.loads(CFG.read_text(encoding="utf-8"))
cfg["provider"][0]["custom_extra_body"]["max_tokens"] = 140
seg = cfg["platform_settings"]["segmented_reply"]
seg["interval_method"] = "human"
seg["interval"] = "0.8,2.0"
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("persona chars:", len(prompt))
print("max_tokens   :", cfg["provider"][0]["custom_extra_body"]["max_tokens"])
print("interval     :", seg["interval_method"])
print("style tail   :", prompt.strip().splitlines()[-1][:40])
