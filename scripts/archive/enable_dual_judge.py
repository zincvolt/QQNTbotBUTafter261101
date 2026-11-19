import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["dual_judge"] = True
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
d["dual_judge_model"] = cfg["provider"][0]["model"]
d["thinking"] = {"enable": False, "budget": 0}
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(d, ensure_ascii=False, indent=2))
