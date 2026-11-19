import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
for p in cfg["provider"]:
    if p["id"] in ("local-llama", "deepseek"):
        print(p["id"], "enable=", p.get("enable"))
        print("   body:", json.dumps(p.get("custom_extra_body"), ensure_ascii=False))
print("agent_runner:", json.dumps(cfg["agent_runner"]["config"]["model"], ensure_ascii=False))
print("caption provider:", cfg["provider_settings"].get("default_image_caption_provider_id"))
reply = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
print("reply:", {k: reply[k] for k in ("meme_chance","dual_judge","text_rules","thinking") if k in reply})
