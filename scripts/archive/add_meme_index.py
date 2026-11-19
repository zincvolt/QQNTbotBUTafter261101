from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_vision_context\main.py")
s = p.read_text(encoding="utf-8")

helper = '''

def load_meme_index() -> dict[str, tuple[str, str, str]]:
    """Map image hash to (pack, category, description) for every installed pack.

    Returns:
        Mapping of sha256 prefix to pack name, category name and its description.
    """
    index: dict[str, tuple[str, str, str]] = {}
    packs_root = COLLECT_DIR.parent.parent.parent
    if not packs_root.exists():
        return index
    for pack_dir in packs_root.iterdir():
        manifest = pack_dir / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            meta = json.loads(manifest.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        categories = meta.get("categories") or {}
        memes_dir = pack_dir / "memes"
        if not memes_dir.is_dir():
            continue
        for category_dir in memes_dir.iterdir():
            if not category_dir.is_dir():
                continue
            desc = str((categories.get(category_dir.name) or {}).get("description") or category_dir.name)
            for image in category_dir.iterdir():
                if not image.is_file():
                    continue
                try:
                    digest = hashlib.sha256(image.read_bytes()).hexdigest()[:16]
                except OSError:
                    continue
                index[digest] = (pack_dir.name, category_dir.name, desc)
    return index


class Main(star.Star):'''

s = s.replace("\n\nclass Main(star.Star):", helper, 1)
s = s.replace(
    "        self._inflight: set[str] = set()\n        logger.info(\"[vision] context captioner ready\")",
    "        self._inflight: set[str] = set()\n        self.meme_index = load_meme_index()\n        logger.info(f\"[vision] ready, meme index: {len(self.meme_index)} images\")",
    1,
)
p.write_text(s, encoding="utf-8")
print("patched")
