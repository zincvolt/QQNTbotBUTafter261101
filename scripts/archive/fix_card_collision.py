from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '''def _card_path(key: str) -> Path:
    """Return the per-day cache path for a query key."""
    safe = re.sub(r"[^0-9A-Za-z_-]+", "_", key)[:40]
    return CARD_DIR / f"{_today()}_{safe}.png"'''
new = '''def _card_path(key: str) -> Path:
    """Return the per-day cache path for a query key.

    中日文会被过滤成下划线，不同城市会撞名，所以补一段短哈希做区分。
    """
    safe = re.sub(r"[^0-9A-Za-z_-]+", "_", key)[:20].strip("_") or "x"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
    return CARD_DIR / f"{_today()}_{safe}_{digest}.png"'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("card path hashed")
else:
    print("MISS")
