import re
from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

new_lex = '''MEME_EMOTION_WORDS = {
    "开心": {"哈哈": 2, "笑死": 2, "嘿嘿": 1, "好耶": 2, "开心": 2, "高兴": 2,
             "爽": 1, "赞": 1, "棒": 1, "太好了": 2, "牛": 1, "厉害": 1,
             "有意思": 1, "可爱": 1, "喜欢": 1, "爱了": 2, "好欸": 2, "太好了": 2},
    "难过": {"难过": 2, "伤心": 2, "委屈": 2, "哭": 2, "泪": 1, "失落": 2,
             "心累": 2, "想哭": 2, "分手": 2, "走了": 1, "没了": 1,
             "可惜": 1, "遗憾": 1, "呜呜": 2, "唉": 1},
    "生气": {"生气": 2, "气愤": 2, "滚": 2, "烦死": 2, "气死": 2, "傻逼": 2,
             "弱智": 2, "过分": 2, "骂": 1, "怼": 2, "凶": 1, "怒": 2,
             "受不了": 2, "离谱": 1, "烦": 1},
    "无语": {"无语": 3, "服了": 3, "算了": 1, "罢了": 1, "呵呵": 2, "无奈": 2,
             "翻白眼": 3, "尬": 1, "尴尬": 2, "沉默": 2, "……": 2,
             "好吧": 1, "行吧": 1, "离谱": 2, "随便": 1},
    "惊讶": {"真的": 1, "卧槽": 2, "我靠": 2, "居然": 2, "竟然": 2, "震惊": 3,
             "不会吧": 2, "好家伙": 2, "？？": 2, "离谱": 1, "啊？": 2},
    "困惑": {"不懂": 2, "为什么": 1, "咋": 1, "怎么": 1, "啥意思": 3, "看不懂": 2,
             "迷惑": 2, "不清楚": 1, "问一下": 1, "求问": 2, "有没有人知道": 2},
    "累了": {"累": 2, "困": 2, "睡": 1, "躺": 1, "摆烂": 2, "疲惫": 2, "歇": 1,
             "摸鱼": 1, "下班": 1, "加班": 2, "熬夜": 2, "不想动": 2},
    "吃喝": {"吃": 1, "饭": 1, "喝": 1, "奶茶": 2, "咖啡": 1, "火锅": 2,
             "饿了": 2, "夜宵": 2, "外卖": 2, "菜": 1},
    "感谢": {"谢谢": 3, "感谢": 3, "多谢": 3, "谢啦": 3, "3q": 2, "thanks": 2,
             "thx": 2, "感恩": 2},
    "拒绝": {"不行": 2, "不要": 1, "拒绝": 2, "别": 1, "不用": 1, "免了": 2,
             "不同意": 2, "算了": 1},
    "害羞": {"害羞": 3, "脸红": 3, "不好意思": 2, "羞": 2, "尬住": 2, "啊这": 2,
             "别夸": 2, "讨厌": 1},
    "日常": {},
}'''

s = re.sub(r"MEME_EMOTION_WORDS = \{[\s\S]*?\n\}", new_lex, s, count=1)

old_score = '''        scores: dict[str, int] = {}
        for name, words in MEME_EMOTION_WORDS.items():
            if not words:
                continue
            hit_bot = sum(1 for w in words if w and w in (text or ""))
            hit_user = sum(1 for w in words if w and w in (user_text or ""))
            if hit_bot or hit_user:
                scores[name] = hit_bot + hit_user * 2'''
new_score = '''        scores: dict[str, int] = {}
        for name, words in MEME_EMOTION_WORDS.items():
            if not words:
                continue
            hit_bot = sum(wt for w, wt in words.items() if w and w in (text or ""))
            hit_user = sum(wt for w, wt in words.items() if w and w in (user_text or ""))
            if hit_bot or hit_user:
                scores[name] = hit_bot + hit_user * 2'''
if old_score in s:
    s = s.replace(old_score, new_score, 1)
    print("weighted scoring applied")

p.write_text(s, encoding="utf-8")
