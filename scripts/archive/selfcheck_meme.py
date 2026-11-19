from pathlib import Path
import random
root = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugin_data\meme_manager\packs\furry\memes")
hints = [((("卖萌","可爱","萌"), "害羞"))]
for words, name in hints:
    print("category dir exists:", (root/name).is_dir(), "->", len(list((root/name).glob("*"))), "张")
allf = [p for p in root.rglob("*") if p.is_file()]
print("全库:", len(allf), "张")
