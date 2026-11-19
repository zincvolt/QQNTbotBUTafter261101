"""Wire the local NPU Whisper into AstrBot and clean up persona fallbacks."""

import json
import sqlite3
from pathlib import Path

CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
DB = Path(r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db")

cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))

providers = cfg.setdefault("provider", [])
if not any(p.get("id") == "stt-local" for p in providers):
    providers.append(
        {
            "id": "stt-local",
            "type": "openai_whisper_api",
            "provider_type": "speech_to_text",
            "enable": True,
            "api_key": "sk-stt-local",
            "api_base": "http://127.0.0.1:8096/v1",
            "model": "whisper-small-int8-ov",
            "timeout": 120,
        }
    )

cfg["provider_stt_settings"] = {"enable": True, "provider_id": "stt-local"}
cfg["provider_tts_settings"] = {"enable": False, "provider_id": "", "dual_output": False,
                                "use_file_service": False, "trigger_probability": 1.0}

# 只留我们自己的人格，避免回退到默认 "helpful assistant"
cfg["provider_settings"]["persona_pool"] = ["*"]

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

con = sqlite3.connect(DB)
try:
    rows = con.execute("SELECT persona_id FROM personas").fetchall()
    print("personas before:", rows)
    con.execute("DELETE FROM personas WHERE persona_id = 'default'")
    con.commit()
    print("personas after :", con.execute("SELECT persona_id FROM personas").fetchall())
finally:
    con.close()

print("stt provider:", [p["id"] for p in providers if p.get("type") == "openai_whisper_api"])
print("stt enabled :", cfg["provider_stt_settings"])
