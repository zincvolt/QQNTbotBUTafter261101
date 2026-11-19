from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

# 1) 常量：表情库路径 + 意图正则
const = '''
MEME_ROOT = Path(r"D:\\QQNTBOT\\apps\\AstrBot\\data\\plugin_data\\meme_manager\\packs")
MEME_REQUEST = re.compile(r"表情包|发张图|发个图|来张图|来张表情|卖萌|发表情")
MEME_CATEGORY_HINTS = [
    (("卖萌", "可爱", "萌"), "害羞"),
    (("无语", "翻白眼"), "无语"),
    (("生气", "凶"), "生气"),
    (("累", "困", "睡"), "累了"),
    (("难过", "哭", "委屈"), "难过"),
    (("开心", "笑"), "开心"),
    (("谢谢", "感谢"), "感谢"),
    (("吃", "饭", "奶茶"), "吃喝"),
]
'''
if "MEME_ROOT" not in s:
    s = s.replace("STRICT_HINT = (", const + "\nSTRICT_HINT = (", 1)

# 2) 在 gate 里做意图拦截：直接发图并结束，不进模型
old = '''        # @ / 唤醒类消息：一律放行，交给 AstrBot 的会话锁排队
        if getattr(event, "is_at_or_wake_command", False):
            logger.info(f"[peer] at-mention queued: {text[:30]}")
            return'''
new = '''        # 要表情包就直接发，别让模型去编"我没有表情包"
        if MEME_REQUEST.search(text):
            if await self._send_random_meme(event, text):
                event.stop_event()
                return

        # @ / 唤醒类消息：一律放行，交给 AstrBot 的会话锁排队
        if getattr(event, "is_at_or_wake_command", False):
            logger.info(f"[peer] at-mention queued: {text[:30]}")
            return'''
if old in s:
    s = s.replace(old, new)

# 3) 方法：选分类 + 随机一张 + 发送
method = '''
    async def _send_random_meme(self, event: AstrMessageEvent, text: str) -> bool:
        """Send a random sticker from the furry pack, bypassing the model.

        Args:
            event: The group message asking for a sticker.
            text: The raw message text, used to pick a matching category.

        Returns:
            True when a sticker was sent.
        """
        pack = MEME_ROOT / "furry"
        memes = pack / "memes"
        if not memes.is_dir():
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
if "_send_random_meme" not in s:
    idx = s.index("    @filter.on_llm_request()")
    s = s[:idx] + method + "\n" + s[idx:]

p.write_text(s, encoding="utf-8")
print("patched:", "_send_random_meme" in s, "MEME_REQUEST" in s)
