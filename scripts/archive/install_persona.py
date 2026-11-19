"""Install the Grey persona into AstrBot (DB + config)."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT\apps\AstrBot")
DB = ROOT / "data" / "data_v4.db"
CFG = ROOT / "data" / "cmd_config.json"
SRC = Path(r"D:\LLM\prompts\persona-grey-werewolf.md")
BASE = Path(r"D:\LLM\prompts\base-context.md")

PERSONA_ID = "grey"


def read_any(p: Path) -> str:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


prompt = read_any(SRC).strip()
if BASE.exists():
    prompt = read_any(BASE).strip() + "\n\n---\n\n" + prompt

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("DELETE FROM personas WHERE persona_id = ?", (PERSONA_ID,))
cur.execute(
    """INSERT INTO personas
       (created_at, updated_at, persona_id, system_prompt, begin_dialogs, tools, skills,
        custom_error_message, folder_id, sort_order)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (now, now, PERSONA_ID, prompt, "[]", "null", "null", "None", "None", 0),
)
con.commit()
con.close()

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
cfg["agent_runner"]["config"]["persona"]["persona_id"] = PERSONA_ID
cfg["agent_runner"]["config"]["persona"]["safety_mode"] = False
CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

print("persona chars:", len(prompt))
print("persona_id   :", PERSONA_ID)
print("first line   :", prompt.splitlines()[0][:60])
