from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

# 1) 常量
if "MEME_CHANCE" not in s:
    s = s.replace(
        "MEME_ROOT = Path(",
        "MEME_CHANCE = 0.3  # 正常回复时附带表情包的概率\n"
        "MEME_MOOD_HINTS = [\n"
        '    (("难过", "委屈", "哭", "可惜", "唉"), "难过"),\n'
        '    (("生气", "烦", "滚", "闭嘴", "气死"), "生气"),\n'
        '    (("无语", "离谱", "服了", "翻白眼"), "无语"),\n'
        '    (("笑", "开心", "哈哈", "好耶", "棒"), "开心"),\n'
        '    (("累", "困", "睡", "躺"), "累了"),\n'
        '    (("吃", "饭", "奶茶", "喝"), "吃喝"),\n'
        '    (("谢谢", "感谢", "多谢"), "感谢"),\n'
        "]\n\n"
        "MEME_ROOT = Path(",
        1,
    )

# 2) 在 mute_non_answer 末尾追加"概率挂表情"
old = '''        if text and NON_ANSWER.match(text):'''
new = '''        if random.random() < MEME_CHANCE:
            self._attach_meme(result, text)
        if text and NON_ANSWER.match(text):'''
if old in s and "_attach_meme" not in s:
    s = s.replace(old, new, 1)

# 3) 方法
method = '''    def _attach_meme(self, result, text: str) -> None:
        """Append a random sticker to an outgoing reply.

        Args:
            result: The message result about to be sent.
            text: The reply text, used to pick a matching category.
        """
        memes = MEME_ROOT / "furry" / "memes"
        if not memes.is_dir() or result is None or not result.chain:
            return
        category = ""
        for words, name in MEME_MOOD_HINTS:
            if any(word in (text or "") for word in words) and (memes / name).is_dir():
                category = name
                break
        pool = [p for p in (memes / category).iterdir() if p.is_file()] if category else []
        if not pool:
            pool = [p for p in memes.rglob("*") if p.is_file()]
        if not pool:
            return
        chosen = random.choice(pool)
        try:
            result.chain.append(Image.fromFileSystem(str(chosen)))
            logger.info(f"[peer] attached meme {chosen.parent.name}/{chosen.name}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[peer] attach meme failed: {exc}")

'''
if "def _attach_meme" not in s:
    anchor = "    @filter.on_llm_request()"
    s = s.replace(anchor, method + anchor, 1)

p.write_text(s, encoding="utf-8")
print("ok:", "MEME_CHANCE" in s, "def _attach_meme" in s, "_attach_meme(result" in s)
