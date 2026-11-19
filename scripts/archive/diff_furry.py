from pathlib import Path
import hashlib
src = Path(r"D:\QQNTBOT\_downloads\furry-emoji")
pack = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs\furry-emoji\memes")
pack_names = {p.name for p in pack.rglob("*") if p.is_file()}
missing = []
for p in src.glob("*"):
    if p.name not in pack_names:
        missing.append((p.name, p.suffix, p.stat().st_size))
print("缺失:", len(missing))
for m in missing[:10]:
    print("  ", m)
print("包内文件按扩展名:")
from collections import Counter
print(Counter(p.suffix for p in pack.rglob("*") if p.is_file()))
