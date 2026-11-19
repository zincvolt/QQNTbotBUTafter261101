import json, shutil
from pathlib import Path

base = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager")
pack = base / "packs" / "furry-emoji"
if pack.exists():
    shutil.rmtree(pack)
    print("deleted pack dir furry-emoji")

reg = base / "registry.json"
data = json.loads(reg.read_text(encoding="utf-8"))
before = [p["id"] for p in data.get("installed_packs", [])]
data["installed_packs"] = [p for p in data.get("installed_packs", []) if p.get("id") != "furry-emoji"]
reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("registry:", before, "->", [p["id"] for p in data["installed_packs"]])

rules_path = base / "selection_rules.json"
rules = json.loads(rules_path.read_text(encoding="utf-8"))
rules["rules"] = [r for r in rules.get("rules", []) if r.get("pack_id") != "furry-emoji"]
rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
print("rules:", rules["rules"])

src = Path(r"D:\QQNTBOT\_downloads\furry-emoji")
if src.exists():
    shutil.rmtree(src)
    print("deleted download folder")
