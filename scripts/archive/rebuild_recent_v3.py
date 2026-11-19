"""Recent card v3: cover backgrounds, gradient text, finished events on top."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

new_fn = '''def _recent_row(event: dict, width: int, height: int, label: str,
                days: int, upcoming: bool) -> Image.Image:
    """Render one full-width row: cover image + gradient + caption."""
    row = Image.new("RGB", (width, height), (30, 33, 42))
    cover = _cover(event.get("thumb") or "", width, height)
    if cover:
        row.paste(cover, (0, 0))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    start_y = int(height * 0.34)
    for i in range(start_y, height):
        alpha = int(232 * (i - start_y) / max(1, height - start_y))
        od.rectangle((0, i, width, i + 1), fill=(8, 10, 14, alpha))
    row = Image.alpha_composite(row.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(row)
    num_font = _font(58)
    name_font = _font(34)
    info_font = _font(22)
    unit_font = _font(24)

    num_text = str(days)
    color = (255, 186, 80) if upcoming else (128, 132, 144)
    draw.text((36, height - 118), num_text, font=num_font, fill=color)
    x_unit = 36 + int(len(num_text) * 34)
    draw.text((x_unit, height - 74), "天" if upcoming else "天前", font=unit_font,
              fill=color)

    text_x = x_unit + 78
    draw.text((text_x, height - 122), event["name"][:16], font=name_font,
              fill=(248, 248, 252) if upcoming else (170, 174, 186))
    meta = " · ".join(
        x
        for x in (
            f"{event['start']}~{event['end']}",
            str(event.get("city", ""))[:14],
            label,
        )
        if x
    )
    draw.text((text_x, height - 72), meta[:40], font=info_font,
              fill=(206, 210, 220) if upcoming else (150, 154, 166))
    return row


def render_recent(events: list[dict]) -> Path:
    """Draw finished events first, then upcoming, each as a cover row."""
    path = _card_path("recent")
    if path.exists():
        return path

    now = time.time()
    past = [e for e in events if e["end_ts"] < now][-2:][::-1]
    upcoming = [e for e in events if e["end_ts"] >= now][:10]

    width = 900
    row_h = 230
    header_h = 150
    section_h = 62
    height = 120 + header_h + section_h + row_h * (len(past) + len(upcoming)) + 80
    img = Image.new("RGB", (width, height), (20, 22, 28))
    draw = ImageDraw.Draw(img)
    big, small = _font(50), _font(24)

    draw.text((44, 44), "近期展会", font=big, fill=(240, 240, 245))
    draw.text((44, 112), f"已结束 {len(past)} 场 · 即将举办 {len(upcoming)} 场",
              font=small, fill=(140, 146, 160))

    y = 170
    if past:
        draw.text((44, y), "已结束", font=small, fill=(150, 154, 166))
        y += section_h
        for ev in past:
            over = max(0, int((now - ev["end_ts"]) // 86400))
            img.paste(_recent_row(ev, width, row_h, f"已结束 {over} 天", over, False),
                      (0, y))
            y += row_h

    if upcoming:
        draw.text((44, y), "即将举办", font=small, fill=(255, 186, 80))
        y += section_h
        for ev in upcoming:
            img.paste(
                _recent_row(ev, width, row_h, ev.get("scale", ""), _days_until(ev), True),
                (0, y),
            )
            y += row_h

    stamp = datetime.now(CST).strftime("%m-%d %H:%M")
    draw.text((44, height - 48), f"数据：FEC 兽展日历 · 生成于 {stamp}",
              font=small, fill=(96, 100, 112))

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path
'''

start = s.index("def render_recent(events: list[dict]) -> Path:")
end = s.index("def render_city(")
s = s[:start] + new_fn + "\n\n" + s[end:]
PLUGIN.write_text(s, encoding="utf-8")
print("render_recent v3 written")
