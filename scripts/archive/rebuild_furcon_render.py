"""Rebuild render_card with a layout that adapts to content height."""

import re
from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

new_fn = '''def render_card(event: dict, following: list[dict], elapsed_ms: int = 0,
                updated: str = "") -> Path:
    """Draw a countdown card and return its path.

    Args:
        event: The event being counted down to.
        following: A few events after it, shown as a list.
        elapsed_ms: How long data fetching plus rendering took.
        updated: When the cached data was last refreshed.

    Returns:
        Path of the rendered PNG.
    """
    width, banner_h = 900, 380
    shown = following[:3]
    body_h = 700 + max(1, len(shown)) * 64 + 150
    height = banner_h + body_h

    img = Image.new("RGB", (width, height), (24, 26, 32))
    draw = ImageDraw.Draw(img)

    title_font = _font(52)
    big_font = _font(150)
    body_font = _font(34)
    small_font = _font(26)

    # 顶部宣传图（下载失败就用纯色，不影响其他内容）
    banner = None
    url = event.get("thumb") or ""
    if url:
        try:
            import io

            import httpx as _httpx

            resp = _httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            banner = Image.open(io.BytesIO(resp.content)).convert("RGB")
            scale = max(width / banner.width, banner_h / banner.height)
            banner = banner.resize(
                (int(banner.width * scale) + 1, int(banner.height * scale) + 1)
            )
            left = (banner.width - width) // 2
            top = (banner.height - banner_h) // 2
            banner = banner.crop((left, top, left + width, top + banner_h))
        except Exception:  # noqa: BLE001
            banner = None
    if banner:
        img.paste(banner, (0, 0))
    else:
        draw.rectangle((0, 0, width, banner_h), fill=(38, 42, 52))

    days = max(
        0,
        (
            datetime.strptime(event["start"], "%Y-%m-%d").date()
            - datetime.now(CST).date()
        ).days,
    )

    y = banner_h + 40
    draw.text((60, y), "下一次兽聚", font=small_font, fill=(140, 146, 160))
    y += 42
    draw.text((60, y), event["name"][:16], font=title_font, fill=(240, 240, 245))
    y += 100
    draw.text((60, y), "今天" if days == 0 else "还有", font=body_font, fill=(140, 146, 160))
    y += 40
    draw.text((60, y), f"{days} 天", font=big_font, fill=(255, 190, 90))
    y += 220

    draw.text((60, y), f"{event['start']} ~ {event['end']}", font=body_font,
              fill=(220, 220, 228))
    y += 60
    line2 = " · ".join(x for x in (event["city"], event["scale"], event["type"]) if x)
    if line2:
        draw.text((60, y), line2, font=body_font, fill=(180, 186, 198))
        y += 60
    if event.get("org"):
        draw.text((60, y), f"主办：{event['org']}", font=small_font, fill=(150, 156, 170))
        y += 50

    y += 20
    draw.line((60, y, width - 60, y), fill=(60, 64, 74), width=2)
    y += 30
    draw.text((60, y), "之后还有", font=small_font, fill=(140, 146, 160))
    y += 50
    for nxt in shown:
        draw.text((60, y), f"{nxt['start']}  {nxt['name'][:14]}", font=body_font,
                  fill=(210, 214, 222))
        y += 64

    stamp = datetime.now(CST).strftime("%m-%d %H:%M")
    footer = "数据：FEC 兽展日历 furrycons.cn"
    if updated:
        footer += f" · 更新于 {updated}"
    draw.text((60, height - 92), footer, font=small_font, fill=(120, 124, 136))
    draw.text(
        (60, height - 50),
        f"图片生成于 {stamp} · 耗时 {elapsed_ms} ms",
        font=small_font,
        fill=(90, 94, 106),
    )

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    path = CARD_DIR / f"furcon_{int(time.time())}.png"
    img.save(path)
    return path
'''

start = s.index("def render_card(")
end = s.index("class Main(star.Star):")
s = s[:start] + new_fn + "\n\n" + s[end:]
PLUGIN.write_text(s, encoding="utf-8")
print("render_card replaced")
