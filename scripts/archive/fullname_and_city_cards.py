"""Show full event names (org + name) and give city cards banner rows."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) 全名助手
helper = '''def _full_name(event: dict) -> str:
    """Combine organizer and event name, avoiding duplication.

    Args:
        event: Normalized event dict.

    Returns:
        Display name such as ``绒萌世界双澜遗珠``.
    """
    name = str(event.get("name", "")).strip()
    org = str(event.get("org", "")).strip()
    if org and org not in name:
        return f"{org}{name}"
    return name


'''
if "_full_name" not in s:
    s = s.replace("def _recent_row(", helper + "def _recent_row(", 1)
    print("full name helper added")

# 2) 单展会卡 & 近期展行 & 城市卡统一用全名
s = s.replace('draw.text((60, y), event["name"][:16], font=title_font',
              'draw.text((60, y), _full_name(event)[:18], font=title_font', 1)
s = s.replace('items = [', 'items = [', 1)
s = s.replace('(text_x, 140, event["name"][:15], name_font, name_color),',
              '(text_x, 140, _full_name(event)[:17], name_font, name_color),', 1)
print("names combined")

# 3) 城市卡改成带宣传图的卡片行
start = s.index("def render_city(")
end = s.index("def render_fortune(")
new_city = '''def render_city(city: str, events: list[dict], mode: str) -> Path:
    """Draw one city's events as banner cards (upcoming or finished)."""
    path = _card_path(f"city_{city}_{mode}")
    if path.exists():
        return path

    now = time.time()
    tokens = expand_place(city)
    hits = [
        e
        for e in events
        if any(t in (str(e.get("city", "")) + str(e.get("region", ""))) for t in tokens)
    ]
    if mode == "past":
        hits = [e for e in hits if e["end_ts"] < now][-6:][::-1]
        subtitle = "已举办"
    else:
        hits = [e for e in hits if e["end_ts"] >= now][:6]
        subtitle = "即将举办"

    width = 900
    margin = 24
    card_w = width - margin * 2
    card_h = 300
    gap = 20
    height = 190 + max(1, len(hits)) * (card_h + gap) + 70
    img = Image.new("RGB", (width, height), CARD_BG)
    draw = ImageDraw.Draw(img)
    big, small = _font(50), _font(24)

    draw.text((margin, 44), city, font=big, fill=(240, 240, 245))
    draw.text((margin, 112), f"{subtitle} {len(hits)} 场", font=small,
              fill=(140, 146, 160))

    y = 170
    if not hits:
        draw.text((margin, y), "没有查到记录", font=_font(32), fill=(160, 166, 178))
    for ev in hits:
        if mode == "past":
            over = max(0, int((now - ev["end_ts"]) // 86400))
            row = _recent_row(ev, card_w, card_h, "", over, False)
        else:
            row = _recent_row(ev, card_w, card_h, ev.get("scale", ""),
                              _days_until(ev), True)
        img.paste(row, (margin, y), row)
        y += card_h + gap

    stamp = datetime.now(CST).strftime("%m-%d %H:%M")
    draw.text((margin, height - 46), f"数据：FEC 兽展日历 · 生成于 {stamp}",
              font=small, fill=(96, 100, 112))

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


'''
s = s[:start] + new_city + s[end:]
print("city card rebuilt")

PLUGIN.write_text(s, encoding="utf-8")
print("done")
