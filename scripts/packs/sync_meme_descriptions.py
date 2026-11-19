import json
from pathlib import Path
base = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs")
for name in ("furry", "unsorted"):
    pack = base / name
    man = pack / "manifest.json"
    if not man.exists():
        continue
    cats = json.loads(man.read_text(encoding="utf-8")).get("categories", {})
    flat = {}
    for cat, meta in cats.items():
        flat[cat] = (meta.get("description") if isinstance(meta, dict) else str(meta)) or cat
    (pack / "memes_data.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")
    print(name, "->", len(flat), "条描述写入 memes_data.json")
