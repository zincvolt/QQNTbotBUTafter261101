import json
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
ps = cfg.get("provider_settings", {})
for k in ("prompt_prefix", "persona_id", "persona_pool", "datetime_system_prompt", "max_context_length", "dequeue_context_length"):
    if k in ps:
        print(k, "=", repr(ps[k])[:200])
print("--- provider[0] ---")
p0 = cfg["provider"][0]
print("model:", p0.get("model"))
print("extra_body:", json.dumps(p0.get("custom_extra_body", {}), ensure_ascii=False)[:300])
