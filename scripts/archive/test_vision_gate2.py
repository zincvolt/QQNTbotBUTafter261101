import re
from pathlib import Path
src = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py").read_text(encoding="utf-8")
block = src[src.index("VISION_HINTS ="):src.index("class Main(")]
ns = {}
exec(block, ns)
f = ns["_should_read_images"]
cases = [
    ("", ["d"*2000]),
    ("[表情]", ["d"*2000]),
    ("这是谁", ["d"*2000]),
    ("好看吗", ["d"*2000]),
    ("", ["d"*30000]),
    ("", ["d"*2000, "d"*2000, "d"*2000]),
]
for text, imgs in cases:
    print(f"{text!r:12} imgs={len(imgs)} -> {f(text, imgs)}")
