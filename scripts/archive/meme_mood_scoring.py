from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

# 1) 情绪词库（按分类），覆盖口语/网络语
lex = '''MEME_EMOTION_WORDS = {
    "开心": ["哈哈", "笑死", "好耶", "开心", "高兴", "爽", "赞", "棒", "太好了",
             "牛", "厉害", "6", "有意思", "可爱", "喜欢", "爱了", "嘿嘿", "好欸"],
    "难过": ["难过", "伤心", "委屈", "哭", "泪", "失落", "心累", "想哭", "难过",
             "离别", "分手", "走了", "没了", "可惜", "遗憾", "呜呜"],
    "生气": ["生气", "气愤", "滚", "烦", "烦死", "气死", "傻逼", "弱智", "离谱",
             "过分", "骂", "怼", "凶", "怒", "恼", "受不了"],
    "无语": ["无语", "服了", "算了", "罢了", "随便", "呵呵", "无奈", "无语子",
             "翻白眼", "尬", "尴尬", "沉默", "……", "好吧", "行吧"],
    "惊讶": ["真的", "卧槽", "我靠", "居然", "竟然", "什么", "啊？", "震惊",
             "不会吧", "好家伙", "？？", "牛逼", "离谱"],
    "困惑": ["不懂", "为什么", "咋", "怎么", "啥意思", "看不懂", "迷惑", "不清楚",
             "问一下", "求问", "有没有人知道"],
    "累了": ["累", "困", "睡", "躺", "摆烂", "疲惫", "歇", "摸鱼", "下班", "加班",
             "熬夜", "不想动"],
    "吃喝": ["吃", "饭", "喝", "奶茶", "咖啡", "火锅", "饿了", "夜宵", "外卖", "菜"],
    "感谢": ["谢谢", "感谢", "多谢", "谢啦", "3q", "thanks", "thx", "感恩"],
    "拒绝": ["不行", "不要", "拒绝", "算了", "别", "不用", "免了", "不同意"],
    "害羞": ["害羞", "脸红", "不好意思", "羞", "尬住", "啊这", "别夸", "讨厌"],
    "日常": [],
}

'''
if "MEME_EMOTION_WORDS" not in s:
    s = s.replace("MEME_CHANCE = 0.3", lex + "MEME_CHANCE = 0.3", 1)
    print("lexicon added")

# 2) 打分选分类
old = '''        memes = MEME_ROOT / "furry" / "memes"
        if not memes.is_dir() or result is None or not result.chain:
            return
        category = ""
        for words, name in MEME_MOOD_HINTS:
            if any(word in (text or "") for word in words) and (memes / name).is_dir():
                category = name
                break
        pool = [p for p in (memes / category).iterdir() if p.is_file()] if category else []'''
new = '''        memes = MEME_ROOT / "furry" / "memes"
        if not memes.is_dir() or result is None or not result.chain:
            return
        # 用户消息权重 2，机器人回复权重 1：跟谁的情绪走更准
        scores: dict[str, int] = {}
        for name, words in MEME_EMOTION_WORDS.items():
            if not words:
                continue
            hit_bot = sum(1 for w in words if w and w in (text or ""))
            hit_user = sum(1 for w in words if w and w in (user_text or ""))
            if hit_bot or hit_user:
                scores[name] = hit_bot + hit_user * 2
        category = ""
        if scores:
            best = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            if (memes / best[0][0]).is_dir():
                category = best[0][0]
            logger.info(f"[peer] meme mood {category} scores={dict(best[:3])}")
        pool = [p for p in (memes / category).iterdir() if p.is_file()] if category else []'''
if old in s:
    s = s.replace(old, new, 1)
    print("scoring added")

# 3) 方法签名加 user_text，调用处传进去
s = s.replace("    def _attach_meme(self, result, text: str) -> None:",
              "    def _attach_meme(self, result, text: str, user_text: str = \"\") -> None:", 1)
s = s.replace("            self._attach_meme(result, text)",
              "            self._attach_meme(result, text, event.message_str or \"\")", 1)

p.write_text(s, encoding="utf-8")
