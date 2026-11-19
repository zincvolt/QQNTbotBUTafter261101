from PIL import Image
from pathlib import Path
d = Path(r"D:\QQNTBOT\_research\emoji-sample")
for p in sorted(d.iterdir()):
    if not p.is_file(): continue
    try:
        im = Image.open(p)
        print(p.name, im.format, im.size)
    except Exception as e:
        print(p.name, "ERR", e)
