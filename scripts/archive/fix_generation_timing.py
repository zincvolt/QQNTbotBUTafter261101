"""Make every card footer report real generation time (cache hits keep the original)."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) render_next：自己计时，去掉外部传参
s = s.replace(
    '''def render_next(event: dict, following: list[dict], elapsed_ms: int = 0,
                updated: str = "", title: str = "下一次兽聚") -> Path:
    """Draw the countdown card for one convention."""
    path = _card_path(f"next_{title}")''',
    '''def render_next(event: dict, following: list[dict],
                updated: str = "", title: str = "下一次兽聚") -> Path:
    """Draw the countdown card for one convention."""
    started = time.perf_counter()
    path = _card_path(f"next_{title}")''',
    1,
)
s = s.replace(
    'draw.text((60, height - 50), f"生成于 {stamp} · {elapsed_ms} ms",',
    'draw.text((60, height - 50),\n'
    '              f"生成于 {stamp} · {int((time.perf_counter() - started) * 1000)} ms",',
    1,
)
print("render_next timed")

# 2) 近期展
s = s.replace(
    '''def render_recent(events: list[dict]) -> Path:
    """Draw finished events first, then upcoming, as rounded cards with gaps."""
    path = _card_path("recent")''',
    '''def render_recent(events: list[dict]) -> Path:
    """Draw finished events first, then upcoming, as rounded cards with gaps."""
    started = time.perf_counter()
    path = _card_path("recent")''',
    1,
)

# 3) 城市卡
s = s.replace(
    '''def render_city(city: str, events: list[dict], mode: str) -> Path:
    """Draw one city's events as banner cards (upcoming or finished)."""
    path = _card_path(f"city_{city}_{mode}")''',
    '''def render_city(city: str, events: list[dict], mode: str) -> Path:
    """Draw one city's events as banner cards (upcoming or finished)."""
    started = time.perf_counter()
    path = _card_path(f"city_{city}_{mode}")''',
    1,
)

# 4) 运势
s = s.replace(
    '''def render_fortune(uid: str, name: str) -> Path:
    """Draw today's jrrp card; same QQ and date always yields the same result."""
    path = _card_path(f"fortune_{uid}_{name}")''',
    '''def render_fortune(uid: str, name: str) -> Path:
    """Draw today's jrrp card; same QQ and date always yields the same result."""
    started = time.perf_counter()
    path = _card_path(f"fortune_{uid}_{name}")''',
    1,
)

# 5) 群统计
s = s.replace(
    '''def render_stats(group_id: str) -> Path:
    """Draw a group activity card."""
    path = _card_path(f"stats_{group_id}")''',
    '''def render_stats(group_id: str) -> Path:
    """Draw a group activity card."""
    started = time.perf_counter()
    path = _card_path(f"stats_{group_id}")''',
    1,
)
print("timers added")

# 6) 三处 footer 加上耗时（近期展 / 城市卡 / 群统计）
s = s.replace(
    '''draw.text((margin, height - 46), f"数据：FEC 兽展日历 · 生成于 {stamp}",
              font=small, fill=(96, 100, 112))''',
    '''draw.text(
        (margin, height - 46),
        f"数据：FEC 兽展日历 · 生成于 {stamp} · "
        f"{int((time.perf_counter() - started) * 1000)} ms",
        font=small,
        fill=(96, 100, 112),
    )''',
)
s = s.replace(
    'draw.text((60, height - 50), f"生成于 {stamp}", font=small, fill=(90, 94, 106))',
    'draw.text((60, height - 50),\n'
    '              f"生成于 {stamp} · {int((time.perf_counter() - started) * 1000)} ms",\n'
    '              font=small, fill=(90, 94, 106))',
    1,
)
print("footers updated")

# 7) 运势卡 footer 也加（它原来只有日期）
s = s.replace(
    'draw.text((60, height - 48), f"{day} · 仅供娱乐", font=small, fill=(90, 94, 106))',
    'draw.text((60, height - 48),\n'
    '              f"{day} · 仅供娱乐 · {int((time.perf_counter() - started) * 1000)} ms",\n'
    '              font=small, fill=(90, 94, 106))',
    1,
)

PLUGIN.write_text(s, encoding="utf-8")
print("done")
