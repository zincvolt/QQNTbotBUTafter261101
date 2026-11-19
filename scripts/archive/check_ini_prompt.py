from pathlib import Path
ini = Path(r"D:\LLM\scripts\models.ini")
raw = ini.read_bytes()
for enc in ("utf-8","gb18030"):
    try: text = raw.decode(enc); break
    except UnicodeDecodeError: continue
print("contains 厚:", "厚" in text)
for kw in ("system", "chat-template", "prompt"):
    hits = [l.strip() for l in text.splitlines() if kw in l.lower()]
    print(kw, "->", hits[:3])
