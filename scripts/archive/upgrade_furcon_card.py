"""Upgrade the convention card: promo banner, venue, timings in the footer."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) 抓取时带上缩略图（相对路径补全成绝对 URL）
old_append = '''        events.append(
            {
                "name": name,'''
new_append = '''        thumb = str(item.get("thumbnail") or "").strip()
        if thumb and not thumb.startswith("http"):
            thumb = f"https://images.furrycons.cn/{thumb.lstrip('/')}"

        events.append(
            {
                "name": name,
                "thumb": thumb,'''
if old_append in s:
    s = s.replace(old_append, new_append, 1)
    print("thumb field added")

# 2) 渲染：顶部宣传图 + 底部生成信息
old_render_start = '''def render_card(event: dict, following: list[dict]) -> Path:'''
new_render_sig = '''def render_card(event: dict, following: list[dict], elapsed_ms: int = 0,
                updated: str = "") -> Path:'''
s = s.replace(old_render_start, new_render_sig, 1)

old_body = '''    width, height = 900, 1000
    img = Image.new("RGB", (width, height), (24, 26, 32))
    draw = ImageDraw.Draw(img)'''
new_body = '''    width, height = 900, 1180
    img = Image.new("RGB", (width, height), (24, 26, 32))
    draw = ImageDraw.Draw(img)

    # 顶部宣传图（下载失败就用纯色，不影响其他内容）
    banner_h = 380
    banner = None
    url = event.get("thumb") or ""
    if url:
        try:
            import httpx as _httpx

            resp = _httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            import io

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
        draw.rectangle((0, 0, width, banner_h), fill=(38, 42, 52))'''
if old_body in s:
    s = s.replace(old_body, new_body, 1)
    print("banner added")

# 3) 文字整体下移，跟着 banner 高度走
s = s.replace('draw.text((60, 60), "下一次兽聚"', 'draw.text((60, banner_h + 40), "下一次兽聚"')
s = s.replace('draw.text((60, 100), event["name"][:16]', 'draw.text((60, banner_h + 80), event["name"][:16]')
s = s.replace('draw.text((60, 220), label', 'draw.text((60, banner_h + 200), label')
s = s.replace('draw.text((60, 260), f"{days} 天"', 'draw.text((60, banner_h + 240), f"{days} 天"')
s = s.replace('draw.text((60, 480), info', 'draw.text((60, banner_h + 470), info')
s = s.replace('draw.text((60, 540), line2', 'draw.text((60, banner_h + 530), line2')
s = s.replace('draw.text((60, 600), f"主办：{event[\'org\']}"', 'draw.text((60, banner_h + 590), f"主办：{event[\'org\']}"')
s = s.replace('draw.line((60, 670, width - 60, 670)', 'draw.line((60, banner_h + 660, width - 60, banner_h + 660)')
s = s.replace('draw.text((60, 700), "之后还有"', 'draw.text((60, banner_h + 690), "之后还有"')
s = s.replace('    y = 750\n', '    y = banner_h + 740\n')

# 4) 底部：生成时间 + 耗时 + 数据更新时间
old_footer = '''    draw.text(
        (60, height - 60),
        "数据来源：FEC 兽展日历 furrycons.cn",
        font=small_font,
        fill=(110, 114, 126),
    )'''
new_footer = '''    stamp = datetime.now(CST).strftime("%m-%d %H:%M")
    footer = f"数据：FEC 兽展日历 furrycons.cn"
    if updated:
        footer += f" · 更新于 {updated}"
    draw.text((60, height - 100), footer, font=small_font, fill=(120, 124, 136))
    draw.text(
        (60, height - 58),
        f"图片生成于 {stamp} · 耗时 {elapsed_ms} ms",
        font=small_font,
        fill=(90, 94, 106),
    )'''
if old_footer in s:
    s = s.replace(old_footer, new_footer, 1)
    print("footer added")

# 5) 调用处计时 + 传更新时间
old_call = '''            events = await fetch_events()
            nxt = pick_next(events)
            if not nxt:
                return
            upcoming = [e for e in events if e["start_ts"] >= nxt["start_ts"]][1:]
            card = render_card(nxt, upcoming)
            await event.send(event.image_result(str(card)))'''
new_call = '''            started = time.time()
            events = await fetch_events()
            nxt = pick_next(events)
            if not nxt:
                return
            upcoming = [e for e in events if e["start_ts"] >= nxt["start_ts"]][1:]
            updated = ""
            try:
                cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                updated = datetime.fromtimestamp(cached.get("fetched", 0), CST).strftime(
                    "%m-%d %H:%M"
                )
            except (json.JSONDecodeError, OSError):
                pass
            elapsed_ms = int((time.time() - started) * 1000)
            card = render_card(nxt, upcoming, elapsed_ms=elapsed_ms, updated=updated)
            days = max(
                0,
                (
                    datetime.strptime(nxt["start"], "%Y-%m-%d").date()
                    - datetime.now(CST).date()
                ).days,
            )
            await event.send(
                event.image_result(str(card))
            )
            await event.send(
                event.plain_result(f"{nxt['name']} · 还有 {days} 天 · {nxt['start']}")
            )'''
if old_call in s:
    s = s.replace(old_call, new_call, 1)
    print("call updated")

PLUGIN.write_text(s, encoding="utf-8")
print("done")
