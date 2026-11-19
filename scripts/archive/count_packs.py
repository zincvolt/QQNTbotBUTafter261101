import hashlib, json
from pathlib import Path
base = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs")
for pack in sorted(base.iterdir()):
    if not pack.is_dir(): continue
    man = pack / "manifest.json"
    if not man.exists(): continue
    cats = json.loads(man.read_text(encoding="utf-8")).get("categories", {})
    total = 0
    for d in (pack / "memes").iterdir() if (pack / "memes").exists() else []:
        if d.is_dir():
            total += len([f for f in d.iterdir() if f.is_file()])
    print(f"{pack.name}: {len(cats)} 类, {total} 张")
