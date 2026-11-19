"""Recent row v5: muted background, two-column text, no overlaps."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

new_row = '''def _recent_row(event: dict, width: int, height: int, label: str,
                days: int, upcoming: bool) -> Image.Image:
    """Render one rounded row: muted cover + two-column caption (no overlap)."""
    card = Image.new("RGB", (width, height), CARD_BG)
    cover = _cover(event.get("thumb") or "", width, height)
    if cover:
        # 统一压灰压暗，当背景纹理用，文字才不会和海报本体打架
        muted = cover.convert("L").convert("RGB")
        muted = Image.blend(muted, Image.new("RGB", muted.size, CARD_BG), 0.58)
        card.paste(muted, (0, 0))

    # 底部再柔和过渡到卡片底色，保证收尾无色偏
    fade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    tail = int(height * 0.52)
    for i in range(tail, height):
        ratio = (i - tail) / max(1, height - tail)
        fd.rectangle((0, i, width, i + 1), fill=(*CARD_BG, int(255 * (ratio ** 1.5))))
    card = Image.alpha_composite(card.convert("RGBA"), fade).convert("RGB")

    draw = ImageDraw.Draw(card)
    num_font = _font(66)
    unit_font = _font(24)
    name_font = _font(36)
    meta_font = _font(22)

    color = (255, 186, 80) if upcoming else (140, 144, 156)
    num_text = str(days)
    draw.text((26, 150), num_text, font=num_font, fill=color)
    num_w = draw.textlength(num_text, font=num_font)
    draw.text((26 + num_w + 6, 192), "天" if upcoming else "天前", font=unit_font,
              fill=color)

    text_x = 176
    name_color = (250, 250, 253) if upcoming else (176, 180, 190)
    draw.text((text_x, 140), event["name"][:15], font=name_font, fill=name_color)
    draw.text((text_x, 186), f"{event['start']} ~ {event['end']}", font=meta_font,
              fill=(206, 210, 220) if upcoming else (150, 154, 166))

    place = " · ".join(
        x for x in (str(event.get("region", ""))[:10], str(event.get("city", ""))[:20]) if x
    )
    if place:
        draw.text((text_x, 216), place[:32], font=meta_font,
                  fill=(190, 194, 206) if upcoming else (140, 144, 156))

    if label:
        draw.text((width - 26 - draw.textlength(label, font=meta_font), 216),
                  label, font=meta_font, fill=(255, 186, 80))

    return _rounded(card, 22)
'''

start = s.index("def _recent_row(")
end = s.index("def render_recent(")
s = s[:start] + new_row + "\n\n" + s[end:]

# 行高加大，给文字留空间
s = s.replace("    card_h = 270", "    card_h = 300", 1)
s = s.replace("    gap = 18", "    gap = 20", 1)

PLUGIN.write_text(s, encoding="utf-8")
print("row v5 written")
