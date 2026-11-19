from PIL import Image
from pathlib import Path
import shutil
d = Path(r"D:\QQNTBOT\_research\emoji-sample")
out = Path(r"D:\QQNTBOT\_research\emoji-view")
out.mkdir(exist_ok=True)
for p in sorted(d.iterdir()):
    if not p.is_file(): continue
    try:
        im = Image.open(p)
        fmt = im.format
        if fmt == "GIF":
            target = out / (p.stem + ".gif")
            shutil.copy2(p, target)
        else:
            target = out / (p.stem + ".png")
            im.convert("RGB").save(target)
        print("ok", target.name, fmt)
    except Exception as e:
        print("ERR", p.name, e)
