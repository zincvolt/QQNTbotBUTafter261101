from PIL import Image, ImageDraw, ImageSequence
from pathlib import Path
src = Path(r"D:\QQNTBOT\build\collected")
out = Path(r"D:\QQNTBOT\_research")
files = sorted(src.glob("*.gif"), key=lambda p: p.stat().st_mtime)
print("gifs:", len(files))
COLS, ROWS, CELL = 7, 6, 170
per = COLS*ROWS
for si in range(0, len(files), per):
    batch = files[si:si+per]
    canvas = Image.new("RGB", (COLS*CELL, ROWS*CELL), (245,245,245))
    draw = ImageDraw.Draw(canvas)
    for i, p in enumerate(batch):
        try:
            im = Image.open(p)
            im.seek(0)
            fr = im.convert("RGBA")
            bg = Image.new("RGBA", fr.size, (245,245,245,255))
            fr = Image.alpha_composite(bg, fr).convert("RGB")
            fr.thumbnail((CELL-8, CELL-24))
            canvas.paste(fr, ((i%COLS)*CELL + (CELL-fr.width)//2, (i//COLS)*CELL+20))
        except Exception:
            pass
        draw.text(((i%COLS)*CELL+4, (i//COLS)*CELL+3), str(si+i), fill=(180,0,0))
    f = out / f"collected-sheet{si//per+1}.png"
    canvas.save(f)
    print("saved", f, len(batch))
