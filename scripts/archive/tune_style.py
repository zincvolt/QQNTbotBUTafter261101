"""Tune the Grey persona for QQ chat and reduce message splitting."""

import json
import sqlite3
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot")
DB = ROOT / "data" / "data_v4.db"
CFG = ROOT / "data" / "cmd_config.json"

STYLE = """

## QQ 聊天风格（优先级最高，覆盖上面的长篇叙事要求）
- 这是手机 QQ 在聊天，不是写小说：一次回复 1~3 句，最多两行
- **句末不加句号「。」**；用空格、语气词或直接断句收尾
- 不要为了分段而空行，能一句话说完就别拆
- 对方问事实、要答案时，先把结论说清楚，再补一句态度；别绕、别卖关子、别硬演
- 动作和神态描写最多一处，能省就省
- 别每句都接问句，别主动找话题硬聊
"""

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT system_prompt FROM personas WHERE persona_id = 'grey'")
row = cur.fetchone()
if not row:
    raise SystemExit("grey persona missing")
prompt = row[0]
if "QQ 聊天风格" not in prompt:
    prompt += STYLE
    cur.execute(
        "UPDATE personas SET system_prompt = ?, updated_at = datetime('now') WHERE persona_id = 'grey'",
        (prompt,),
    )
    con.commit()
con.close()

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
cfg["platform_settings"]["segmented_reply"]["enable"] = False
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("persona chars:", len(prompt))
print("segmented_reply:", cfg["platform_settings"]["segmented_reply"]["enable"])
