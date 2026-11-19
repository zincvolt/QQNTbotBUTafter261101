import re
from pathlib import Path
src = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py").read_text(encoding="utf-8")
block = src[src.index("VISION_HINTS ="):src.index("class Main(")]
ns = {}
exec(block.replace('def _should_read_images', 'def _should_read_images'), ns)
f = ns["_should_read_images"]
cases = [
    ("[表情包]", ["data:image/png;base64," + "A"*2000]),
    ("这图什么意思？", ["data:image/png;base64," + "A"*2000]),
    ("看这个截图", ["data:image/png;base64," + "A"*2000]),
    ("", ["x"*70000]),
    ("", ["a", "b", "c"]),
]
for text, imgs in cases:
    print(f"{text[:12]!r:16} 图片{len(imgs)} -> 读图 {f(text, imgs)}")
