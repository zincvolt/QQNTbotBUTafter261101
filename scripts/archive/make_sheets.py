from PIL import Image, ImageDraw
from pathlib import Path

src = Path(r"D:\QQ\DATA\1154487120\nt_qq\nt_data\Emoji\emoji-recv")
out = Path(r"D:\QQNTBOT\_research\sheets")
out.mkdir(parents=True, exist_ok=True)

files = sorted(
    [p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg",".png",".gif"}],
    key=lambda p: p.stat().st_mtime, reverse=True,
)
print("total:", len(files))

COLS, ROWS, CELL = 5, 4, 220
per = COLS * ROWS
sheets = 0
for s in range(0, min(len(files), 80), per):
    batch = files[s:s+per]
    canvas = Image.new("RGB", (COLS*CELL, ROWS*CELL), "white")
    draw = ImageDraw.Draw(canvas)
    for i, p in enumerate(batch):
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((CELL-10, CELL-30))
            x = (i % COLS) * CELL + (CELL - im.width)//2
            y = (i // COLS) * CELL + 22
            canvas.paste(im, (x, y))
        except Exception:
            pass
        cx = (i % COLS) * CELL + 8
        cy = (i // COLS) * CELL + 4
        draw.text((cx, cy), str(s + i), fill="red")
    sheets += 1
    canvas.save(out / f"sheet{sheets}.png")
    print("saved", out / f"sheet{sheets}.png", "items", len(batch))
