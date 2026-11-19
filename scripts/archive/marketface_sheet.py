from PIL import Image, ImageDraw
from pathlib import Path
src = Path(r"D:\QQ\DATA\1154487120\nt_qq\nt_data\Emoji\marketface")
files = sorted([p for p in src.rglob("*") if p.is_file() and p.suffix.lower() == ".png"])
print("png:", len(files))
COLS, ROWS, CELL = 6, 4, 180
canvas = Image.new("RGB", (COLS*CELL, ROWS*CELL), (245,245,245))
draw = ImageDraw.Draw(canvas)
for i, p in enumerate(files[:24]):
    try:
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", im.size, (245,245,245,255))
        im = Image.alpha_composite(bg, im).convert("RGB")
        im.thumbnail((CELL-10, CELL-26))
        canvas.paste(im, ((i % COLS)*CELL + (CELL-im.width)//2, (i//COLS)*CELL + 20))
        draw.text(((i % COLS)*CELL+4, (i//COLS)*CELL+3), p.parent.name, fill=(180,0,0))
    except Exception as e:
        pass
out = Path(r"D:\QQNTBOT\_research\marketface-sheet.png")
canvas.save(out)
print("saved", out)
