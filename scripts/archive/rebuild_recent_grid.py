"""Rebuild the recent-events card as a thumbnail grid with overlaid info."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

new_block = '''def _cover(url: str, width: int, height: int) -> Image.Image | None:
    """Download and center-crop a thumbnail to the requested size."""
    if not url:
        return None
    try:
        resp = httpx.get(url, timeout=12, follow_redirects=True)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        scale = max(width / img.width, height / img.height)
        img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
        left = (img.width - width) // 2
        top = (img.height - height) // 2
        return img.crop((left, top, left + width, top + height))
    except Exception:  # noqa: BLE001
        return None


def _tile(event: dict, width: int, height: int, days: int | None) -> Image.Image:
    """Render one event tile: cover image with a dark caption overlay."""
    tile = Image.new("RGB", (width, height), (34, 38, 48))
    cover = _cover(event.get("thumb") or "", width, height)
    if cover:
        tile.paste(cover, (0, 0))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    bar_top = int(height * 0.52)
    for i in range(bar_top, height):
        alpha = int(215 * (i - bar_top) / max(1, height - bar_top))
        od.rectangle((0, i, width, i + 1), fill=(10, 12, 16, alpha))
    tile = Image.alpha_composite(tile.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(tile)
    name_font = _font(30)
    info_font = _font(20)
    tiny_font = _font(18)

    draw.text((16, bar_top + 8), event["name"][:12], font=name_font,
              fill=(255, 255, 255))
    date_line = f"{event['start']} ~ {event['end']}"
    draw.text((16, bar_top + 46), date_line, font=info_font, fill=(220, 224, 232))
    place = " · ".join(
        x for x in (str(event.get("city", ""))[:12], event.get("scale", "")) if x
    )
    if place:
        draw.text((16, bar_top + 72), place, font=tiny_font, fill=(190, 196, 208))

    if days is not None:
        label = "今天" if days == 0 else f"{days} 天"
        box_w = 16 + len(label) * 20
        draw.rectangle((width - box_w - 16, 16, width - 16, 58), fill=(255, 176, 60))
        draw.text((width - box_w - 4, 22), label, font=info_font, fill=(24, 26, 32))
    return tile


def render_recent(events: list[dict]) -> Path:
    """Draw 10 upcoming plus 2 finished events as a thumbnail grid."""
    path = _card_path("recent")
    if path.exists():
        return path

    now = time.time()
    upcoming = [e for e in events if e["end_ts"] >= now][:10]
    past = [e for e in events if e["end_ts"] < now][-2:][::-1]

    width = 900
    margin, gap = 40, 20
    tile_w = (width - margin * 2 - gap) // 2
    tile_h = 250
    rows = (len(upcoming) + len(past) + 1) // 2 + 1
    height = 190 + rows * (tile_h + gap) + 90

    img = Image.new("RGB", (width, height), (22, 24, 30))
    draw = ImageDraw.Draw(img)
    big, small = _font(48), _font(24)

    draw.text((margin, 44), "近期展会", font=big, fill=(240, 240, 245))
    draw.text((margin, 112), f"即将举办 {len(upcoming)} 场 · 刚结束 {len(past)} 场",
              font=small, fill=(140, 146, 160))

    y = 170
    entries = [(e, _days_until(e)) for e in upcoming] + [(e, None) for e in past]
    for idx, (event, days) in enumerate(entries):
        col = idx % 2
        if idx and col == 0:
            y += tile_h + gap
        x = margin + col * (tile_w + gap)
        img.paste(_tile(event, tile_w, tile_h, days), (x, y))

    stamp = datetime.now(CST).strftime("%m-%d %H:%M")
    draw.text((margin, height - 50), f"数据：FEC 兽展日历 · 生成于 {stamp}",
              font=small, fill=(90, 94, 106))

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path
'''

start = s.index("def render_recent(events: list[dict]) -> Path:")
end = s.index("def render_city(")
s = s[:start] + new_block + "\n\n" + s[end:]
PLUGIN.write_text(s, encoding="utf-8")
print("render_recent rebuilt")
