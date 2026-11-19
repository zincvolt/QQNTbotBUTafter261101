"""Re-enable split replies with random delays and let the bot break lines."""

import json
import sqlite3
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot")
DB = ROOT / "data" / "data_v4.db"
CFG = ROOT / "data" / "cmd_config.json"

OLD_RULE = "- 不要为了分段而空行，能一句话说完就别拆"
NEW_RULE = (
    "- 一句话一行，用换行把短句分开（每行不超过 20 字），行与行之间不空行\n"
    "- 手机 QQ 上每行会变成一条独立消息，所以每行都要能单独读通"
)

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT system_prompt FROM personas WHERE persona_id = 'grey'")
prompt = cur.fetchone()[0]
if OLD_RULE in prompt:
    prompt = prompt.replace(OLD_RULE, NEW_RULE)
    cur.execute(
        "UPDATE personas SET system_prompt = ?, updated_at = datetime('now') "
        "WHERE persona_id = 'grey'",
        (prompt,),
    )
    con.commit()
con.close()

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
seg = cfg["platform_settings"]["segmented_reply"]
seg["enable"] = True
seg["interval_method"] = "random"
seg["interval"] = "1.2,3.2"
seg["only_llm_result"] = True
seg["words_count_threshold"] = 400
seg["split_mode"] = "regex"
seg["regex"] = r"[^。！？~…\n]+[。！？~…\n]*"
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("style rule swapped:", OLD_RULE not in prompt)
print("segmented:", seg["enable"], seg["interval_method"], seg["interval"])
print("regex    :", seg["regex"])
