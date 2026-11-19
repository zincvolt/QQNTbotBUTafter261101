import json
from pathlib import Path
pack = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs\group-feed")
mpath = pack / "manifest.json"
m = json.loads(mpath.read_text(encoding="utf-8"))
m["categories"]["未分类"] = {"description": "刚收进来还没归类的表情，暂存用"}
mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
(pack / "memes" / "未分类").mkdir(parents=True, exist_ok=True)
print("categories:", list(m["categories"].keys()))
