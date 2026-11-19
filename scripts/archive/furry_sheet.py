from PIL import Image, ImageDraw
from pathlib import Path
src = Path(r"D:\QQNTBOT\_downloads\furry-emoji")
out = Path(r"D:\QQNTBOT\_research\furry-sheet.png")
files = sorted(src.glob("*"))
COLS, ROWS, CELL = 10, 8, 130
canvas = Image.new("RGB", (COLS*CELL, ROWS*CELL), (245,245,245))
draw = ImageDraw.Draw(canvas)
for i, p in enumerate(files[:80]):
    try:
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", im.size, (245,245,245,255))
        im = Image.alpha_composite(bg, im).convert("RGB")
        im.thumbnail((CELL-8, CELL-22))
        x = (i % COLS) * CELL + (CELL - im.width)//2
        y = (i // COLS) * CELL + 18
        canvas.paste(im, (x, y))
    except Exception:
        pass
    draw.text(((i % COLS) * CELL + 4, (i // COLS) * CELL + 2), str(i), fill=(200,0,0))
canvas.save(out)
print("saved", out, len(files))
