import json, shutil
from pathlib import Path

pack = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs\furry-emoji")
paw = pack / "memes" / "爪印"
if paw.exists():
    shutil.rmtree(paw)
    print("removed 爪印 dir")

mpath = pack / "manifest.json"
m = json.loads(mpath.read_text(encoding="utf-8"))
m["categories"].pop("爪印", None)
mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print("categories:", list(m["categories"].keys()))

script = Path(r"D:\QQNTBOT\scripts\build_furry_pack.py")
s = script.read_text(encoding="utf-8")
s = s.replace('    "爪印": [17, 44, 49, 56, 60],\n', "")
s = s.replace('    "爪印": "毛茸茸的爪子印，适合盖章式回应、卖萌",\n', "")
script.write_text(s, encoding="utf-8")
print("build script cleaned:", "爪印" not in s)
