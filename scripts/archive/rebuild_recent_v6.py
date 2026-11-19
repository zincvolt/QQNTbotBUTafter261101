"""Recent row v6: colour for upcoming, gray only for finished, soft text shadow."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 需要模糊做阴影
if "from PIL import ImageFilter" not in s:
    s = s.replace("from PIL import Image, ImageDraw, ImageFont",
                  "from PIL import Image, ImageDraw, ImageFilter, ImageFont", 1)
    print("ImageFilter imported")

new_row = '''def _recent_row(event: dict, width: int, height: int, label: str,
                days: int, upcoming: bool) -> Image.Image:
    """Render one rounded row: colour cover, soft text shadow, no heavy overlay."""
    card = Image.new("RGB", (width, height), CARD_BG)
    cover = _cover(event.get("thumb") or "", width, height)
    if cover:
        if upcoming:
            # 未开始：保留原色，只压一点点亮度，避免文字被亮部吃掉
            dimmed = Image.blend(cover, Image.new("RGB", cover.size, (0, 0, 0)), 0.18)
        else:
            # 已结束：整张转灰
            dimmed = cover.convert("L").convert("RGB")
            dimmed = Image.blend(dimmed, Image.new("RGB", cover.size, CARD_BG), 0.45)
        card.paste(dimmed, (0, 0))

    # 底部轻过渡到卡片底色，收尾自然
    fade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    tail = int(height * 0.55)
    for i in range(tail, height):
        ratio = (i - tail) / max(1, height - tail)
        fd.rectangle((0, i, width, i + 1), fill=(*CARD_BG, int(190 * (ratio ** 1.6))))
    card = Image.alpha_composite(card.convert("RGBA"), fade).convert("RGB")

    num_font = _font(66)
    unit_font = _font(24)
    name_font = _font(36)
    meta_font = _font(22)

    color = (255, 186, 80) if upcoming else (150, 154, 166)
    name_color = (255, 255, 255) if upcoming else (184, 188, 198)
    meta_color = (226, 230, 238) if upcoming else (152, 156, 168)

    num_text = str(days)
    tmp = ImageDraw.Draw(card)
    num_w = tmp.textlength(num_text, font=num_font)

    text_x = 176
    items = [
        (26, 150, num_text, num_font, color),
        (26 + num_w + 6, 192, "天" if upcoming else "天前", unit_font, color),
        (text_x, 140, event["name"][:15], name_font, name_color),
        (text_x, 186, f"{event['start']} ~ {event['end']}", meta_font, meta_color),
    ]
    place = " · ".join(
        x for x in (str(event.get("region", ""))[:10], str(event.get("city", ""))[:20]) if x
    )
    if place:
        items.append((text_x, 216, place[:32], meta_font, meta_color))
    if label:
        items.append((width - 26 - tmp.textlength(label, font=meta_font), 216,
                      label, meta_font, (255, 186, 80)))

    # 柔光阴影：文字铺一层模糊黑，再画正文
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for x, y, text, font, _c in items:
        sd.text((x + 2, y + 3), text, font=font, fill=(0, 0, 0, 210))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    card = Image.alpha_composite(card.convert("RGBA"), shadow).convert("RGB")

    draw = ImageDraw.Draw(card)
    for x, y, text, font, fill in items:
        draw.text((x, y), text, font=font, fill=fill)

    return _rounded(card, 22)
'''

start = s.index("def _recent_row(")
end = s.index("def render_recent(")
s = s[:start] + new_row + "\n\n" + s[end:]
PLUGIN.write_text(s, encoding="utf-8")
print("row v6 written")
