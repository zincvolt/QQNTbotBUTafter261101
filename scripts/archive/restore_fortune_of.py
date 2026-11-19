"""Restore fortune_of, which the earlier render_city rewrite accidentally removed."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

func = '''def fortune_of(uid: str, day: str) -> tuple[int, str, tuple[int, int, int], str]:
    """Derive today's fixed fortune for one QQ number.

    Args:
        uid: QQ number.
        day: Date string (YYYYMMDD).

    Returns:
        Tuple of (jrrp score 0-100, level name, level color, tip).
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
    elif jrrp >= 20:
        level, color = "小凶", (120, 160, 210)
    else:
        level, color = "凶", (130, 130, 160)
    tip = FORTUNE_TIPS[int(digest[8:12], 16) % len(FORTUNE_TIPS)]
    return jrrp, level, color, tip


'''

if "def fortune_of(" not in s:
    s = s.replace("def render_fortune(", func + "def render_fortune(", 1)
    PLUGIN.write_text(s, encoding="utf-8")
    print("fortune_of restored")
else:
    print("already present")
