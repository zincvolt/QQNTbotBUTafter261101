from PIL import Image
from pathlib import Path
d = Path(r"D:\QQ\DATA\1154487120\nt_qq\nt_data\Emoji\marketface")
for p in sorted([x for x in d.rglob("*.png")])[:4]:
    im = Image.open(p)
    print(p.parent.name, p.name, im.size, im.mode)
