from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_vision_context\main.py")
s = p.read_text(encoding="utf-8")
old = '            pack_root = COLLECT_DIR.parent\n            if any(p.name.startswith(digest) for p in pack_root.rglob("*") if p.is_file()):\n                return'
new = ('            packs_root = COLLECT_DIR.parent.parent.parent\n'
       '            if any(p.name.startswith(digest) for p in packs_root.rglob("*") if p.is_file()):\n'
       '                return')
if old in s:
    p.write_text(s.replace(old, new), encoding="utf-8")
    print("dedupe scope -> all packs")
else:
    print("pattern not found; check manually")
