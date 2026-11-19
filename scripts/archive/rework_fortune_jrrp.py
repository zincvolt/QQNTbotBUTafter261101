"""Rework fortune to a jrrp-style deterministic value and add jrrp/jrys aliases."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) 词表：加 jrrp / jrys / 人品
s = s.replace(
    '("fortune", re.compile(r"(运势|运气|抽个签|求签|吉凶|今日份|转运)")),',
    '("fortune", re.compile(r"(运势|运气|抽个签|求签|吉凶|今日份|转运|人品|jrrp|jrys)")),',
    1,
)

# 2) 运势算法：QQ+日期 -> 固定人品值 0~100
old_start = s.index("def render_fortune(")
old_end = s.index("def group_stats(")
new_fn = '''def fortune_of(uid: str, day: str) -> tuple[int, str, tuple[int, int, int], str]:
    """Derive today's fixed fortune for one QQ number.

    Args:
        uid: QQ number.
        day: Date string (YYYYMMDD).

    Returns:
        Tuple of (jrrp score 0-100, level name, level color, comment).
    """
    digest = hashlib.sha256(f"{uid}|{day}".encode()).hexdigest()
    jrrp = int(digest[:8], 16) % 101
    if jrrp >= 90:
        level, color = "大吉", (255, 96, 96)
    elif jrrp >= 75:
        level, color = "中吉", (255, 150, 80)
    elif jrrp >= 60:
        level, color = "小吉", (255, 200, 90)
    elif jrrp >= 40:
        level, color = "平", (150, 190, 150)
    elif jrrp >= 25:
        level, color = "小凶", (120, 160, 210)
    else:
        level, color = "凶", (130, 130, 160)
    tip = FORTUNE_TIPS[int(digest[8:12], 16) % len(FORTUNE_TIPS)]
    return jrrp, level, color, tip


def render_fortune(uid: str, name: str) -> Path:
    """Draw today's jrrp card; same QQ and date always yields the same result."""
    path = _card_path(f"fortune_{uid}_{name}")
    if path.exists():
        return path

    day = _today()
    jrrp, level, color, tip = fortune_of(uid, day)

    width, height = 900, 900
    img = Image.new("RGB", (width, height), (24, 26, 32))
    draw = ImageDraw.Draw(img)
    big, huge, mid, small = _font(48), _font(150), _font(34), _font(24)

    draw.text((60, 46), "今日人品 · jrrp", font=big, fill=(200, 204, 214))
    draw.text((60, 112), f"{name[:12]} · {day}", font=small, fill=(140, 146, 160))
    draw.text((60, 176), str(jrrp), font=huge, fill=color)
    offset = 60 + int(len(str(jrrp)) * 92)
    draw.text((offset, 268), "分", font=mid, fill=color)
    draw.text((60, 380), level, font=big, fill=color)

    draw.rectangle((60, 470, 820, 502), outline=(70, 74, 84), width=2)
    draw.rectangle((60, 470, 60 + int(760 * jrrp / 100), 502), fill=color)
    draw.text((60, 530), f"今日提示：{tip}", font=mid, fill=(210, 214, 222))
    draw.text((60, 596), "同一 QQ 同一天结果固定，明天重算", font=small,
              fill=(140, 146, 160))

    draw.text((60, height - 56), f"{day} · 仅供娱乐", font=small, fill=(90, 94, 106))

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


'''
s = s[:old_start] + new_fn + s[old_end:]
print("fortune rewritten")

# 3) 帮助文案
s = s.replace("/运势  今日运势", "/运势  今日运势 / 人品（也支持 /jrrp /jrys）", 1)

PLUGIN.write_text(s, encoding="utf-8")
print("done")
