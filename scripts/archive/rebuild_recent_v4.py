"""Recent card v4: rounded cards with gaps, desaturating fade, larger text."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

new_fn = '''CARD_BG = (20, 22, 28)


def _rounded(img: Image.Image, radius: int) -> Image.Image:
    """Round the corners of an image using a mask."""
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1),
                                           radius=radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img.convert("RGBA"), (0, 0), mask)
    return out


def _recent_row(event: dict, width: int, height: int, label: str,
                days: int, upcoming: bool) -> Image.Image:
    """Render one rounded row: cover image + gray fade + caption."""
    card = Image.new("RGB", (width, height), CARD_BG)
    cover = _cover(event.get("thumb") or "", width, height)
    if cover:
        card.paste(cover, (0, 0))

        # 往下逐渐压灰：底部接近中性灰，避免彩色海报干扰文字
        gray = cover.convert("L").convert("RGB")
        mask = Image.new("L", (width, height), 0)
        md = ImageDraw.Draw(mask)
        start = int(height * 0.40)
        for i in range(start, height):
            ratio = (i - start) / max(1, height - start)
            md.rectangle((0, i, width, i + 1), fill=int(235 * (ratio ** 0.8)))
        card = Image.composite(gray, card, mask)

        # 末尾完全压到卡片底色，保证没有色偏
        bottom = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bottom)
        tail = int(height * 0.55)
        for i in range(tail, height):
            ratio = (i - tail) / max(1, height - tail)
            bd.rectangle((0, i, width, i + 1),
                         fill=(*CARD_BG, int(255 * (ratio ** 1.35))))
        card = Image.alpha_composite(card.convert("RGBA"), bottom).convert("RGB")

    draw = ImageDraw.Draw(card)
    num_font = _font(64)
    unit_font = _font(26)
    name_font = _font(38)
    meta_font = _font(23)

    color = (255, 186, 80) if upcoming else (135, 139, 150)
    num_text = str(days)
    draw.text((34, height - 118), num_text, font=num_font, fill=color)
    num_w = draw.textlength(num_text, font=num_font)
    draw.text((34 + num_w + 8, height - 74), "天" if upcoming else "天前",
              font=unit_font, fill=color)

    text_x = int(34 + num_w + 96)
    draw.text((text_x, height - 132), event["name"][:16], font=name_font,
              fill=(250, 250, 253) if upcoming else (186, 190, 200))

    place = " · ".join(
        x
        for x in (
            str(event.get("region", ""))[:10],
            str(event.get("city", ""))[:18],
        )
        if x
    )
    draw.text((text_x, height - 84), f"{event['start']}~{event['end']}",
              font=meta_font, fill=(214, 218, 228) if upcoming else (160, 164, 176))
    if place:
        draw.text((text_x, height - 52), place[:30], font=meta_font,
                  fill=(196, 200, 212) if upcoming else (146, 150, 162))
    if label:
        draw.text((width - 30 - draw.textlength(label, font=meta_font),
                   height - 52), label, font=meta_font, fill=(255, 186, 80))

    return _rounded(card, 22)


def render_recent(events: list[dict]) -> Path:
    """Draw finished events first, then upcoming, as rounded cards with gaps."""
    path = _card_path("recent")
    if path.exists():
        return path

    now = time.time()
    past = [e for e in events if e["end_ts"] < now][-2:][::-1]
    upcoming = [e for e in events if e["end_ts"] >= now][:10]

    width = 900
    margin = 24
    card_w = width - margin * 2
    card_h = 270
    gap = 18
    header_h = 150
    section_h = 58
    total_cards = len(past) + len(upcoming)
    height = (
        120
        + header_h
        + section_h * (1 if past else 0)
        + section_h * (1 if upcoming else 0)
        + total_cards * (card_h + gap)
        + 70
    )
    img = Image.new("RGB", (width, height), CARD_BG)
    draw = ImageDraw.Draw(img)
    big, small = _font(52), _font(24)

    draw.text((margin, 42), "近期展会", font=big, fill=(240, 240, 245))
    draw.text((margin, 112), f"已结束 {len(past)} 场 · 即将举办 {len(upcoming)} 场",
              font=small, fill=(140, 146, 160))

    y = 164
    if past:
        draw.text((margin, y), "已结束", font=small, fill=(150, 154, 166))
        y += section_h
        for ev in past:
            over = max(0, int((now - ev["end_ts"]) // 86400))
            img.paste(
                _recent_row(ev, card_w, card_h, "", over, False),
                (margin, y),
                _recent_row(ev, card_w, card_h, "", over, False),
            )
            y += card_h + gap

    if upcoming:
        draw.text((margin, y), "即将举办", font=small, fill=(255, 186, 80))
        y += section_h
        for ev in upcoming:
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

start = s.index("def _recent_row(")
end = s.index("def render_city(")
s = s[:start] + new_fn + "\n\n" + s[end:]
PLUGIN.write_text(s, encoding="utf-8")
print("render_recent v4 written")
