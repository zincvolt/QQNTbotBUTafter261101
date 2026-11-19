import json, shutil
from pathlib import Path

base = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager")
packs = base / "packs"

# 1) group-feed -> furry（已分好类的）
old = packs / "group-feed"
new = packs / "furry"
if old.exists() and not new.exists():
    old.rename(new)
m = json.loads((new / "manifest.json").read_text(encoding="utf-8"))
m["id"] = "furry"
m["name"] = "furry"
m["description"] = "群友投喂的兽人表情，已分好 12 个情绪分类"
m.pop("tags", None)
(new / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

# 2) 新建"未分类"包当收件箱
inbox = packs / "unsorted"
if inbox.exists():
    shutil.rmtree(inbox)
(inbox / "memes" / "未分类").mkdir(parents=True, exist_ok=True)
(inbox / "manifest.json").write_text(json.dumps({
    "schema_version": 1,
    "id": "unsorted",
    "name": "未分类",
    "version": "1.0.0",
    "description": "群里新收到的表情先落这里，等待人工归类",
    "categories": {"未分类": {"description": "还没归类的表情，暂存区"}},
}, ensure_ascii=False, indent=2), encoding="utf-8")
(inbox / "memes_data.json").write_text("{}\n", encoding="utf-8")

# 3) registry
reg = base / "registry.json"
data = json.loads(reg.read_text(encoding="utf-8"))
items = [p for p in data["installed_packs"] if p["id"] not in ("group-feed", "furry", "unsorted")]
items.append({"id": "furry", "name": "furry", "version": "1.0.0", "enabled": True, "installed_at": "2026-11-17T10:45:00+00:00"})
items.append({"id": "unsorted", "name": "未分类", "version": "1.0.0", "enabled": True, "installed_at": "2026-11-17T10:45:00+00:00"})
data["installed_packs"] = items
reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# 4) 默认选包 -> furry
rules_path = base / "selection_rules.json"
rules = json.loads(rules_path.read_text(encoding="utf-8"))
rules["rules"] = [r for r in rules["rules"] if r.get("id") != "default"]
rules["rules"].insert(0, {"id": "default", "scope": "default", "pack_id": "furry"})
rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")

print("packs:", [p.name for p in packs.iterdir() if p.is_dir()])
print("registry:", [p["id"] for p in items])
print("rules:", rules["rules"])
