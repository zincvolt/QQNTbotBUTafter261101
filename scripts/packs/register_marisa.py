import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\registry.json")
data = json.loads(p.read_text(encoding="utf-8"))
packs = [x for x in data.get("installed_packs", []) if x.get("id") != "marisa-meme-pack"]
packs.append({
    "id": "marisa-meme-pack",
    "name": "魔理沙表情包",
    "version": "1.0.0",
    "enabled": True,
    "installed_at": "2026-11-17T10:30:00+00:00",
})
data["installed_packs"] = packs
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
for x in packs:
    print(x["id"], x["name"], x["enabled"])
