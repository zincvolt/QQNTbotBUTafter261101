from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

method = '''    async def _send_random_meme(self, event: AstrMessageEvent, text: str) -> bool:
        """Send a random sticker from the furry pack, bypassing the model.

        Args:
            event: The group message asking for a sticker.
            text: The raw message text, used to pick a matching category.

        Returns:
            True when a sticker was sent.
        """
        memes = MEME_ROOT / "furry" / "memes"
        if not memes.is_dir():
            logger.warning(f"[peer] meme pack missing: {memes}")
            return False
        category = ""
        for words, name in MEME_CATEGORY_HINTS:
            if any(word in text for word in words) and (memes / name).is_dir():
                category = name
                break
        pool = []
        if category:
            pool = [p for p in (memes / category).iterdir() if p.is_file()]
        if not pool:
            pool = [p for p in memes.rglob("*") if p.is_file()]
        if not pool:
            logger.warning("[peer] meme pack empty")
            return False
        chosen = random.choice(pool)
        try:
            await event.send(event.image_result(str(chosen)))
            logger.info(f"[peer] sent meme {chosen.parent.name}/{chosen.name}")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[peer] meme send failed: {exc}")
            return False

'''

if "async def _send_random_meme" not in s:
    anchor = "    @filter.on_llm_request()"
    s = s.replace(anchor, method + anchor, 1)
    print("method inserted")
else:
    print("already exists")

p.write_text(s, encoding="utf-8")
