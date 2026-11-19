import json, shutil
from pathlib import Path
pack = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs\furry")
d = pack / "memes" / "未分类"
if d.exists():
    shutil.rmtree(d)
    print("removed empty 未分类 from furry")
mpath = pack / "manifest.json"
m = json.loads(mpath.read_text(encoding="utf-8"))
m["categories"].pop("未分类", None)
mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print("furry categories:", len(m["categories"]))
