"""Fix place parsing, recent card layout, fortune cache key, group switch."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# ---------- 1) 地点字段解析：placeName / region 可能是 dict ----------
helper = '''def _place(value) -> str:
    """Normalize a place field that may be a string or a {localName} dict."""
    if isinstance(value, dict):
        for key in ("localName", "name", "fullName"):
            if value.get(key):
                return str(value[key])[:24]
        return ""
    return str(value or "")[:24]


'''
if "def _place(value)" not in s:
    s = s.replace("async def fetch_events(", helper + "async def fetch_events(", 1)
    print("place helper added")

s = s.replace(
    '''                "city": str(item.get("placeName") or item.get("region") or "")[:24],
                "region": str(item.get("region") or "")[:16],''',
    '''                "city": _place(item.get("placeName")) or _place(item.get("region")),
                "region": _place(item.get("region")),''',
    1,
)

# ---------- 2) 近期展：一行一个，天数最大，已结束灰色 ----------
new_recent = '''def render_recent(events: list[dict]) -> Path:
    """Draw a one-line-per-event list with the countdown as the biggest text."""
    path = _card_path("recent")
    if path.exists():
        return path

    now = time.time()
    upcoming = [e for e in events if e["end_ts"] >= now][:10]
    past = [e for e in events if e["end_ts"] < now][-2:][::-1]

    width = 900
    row_h = 132
    height = 180 + row_h * (len(upcoming) + len(past) + 1) + 80
    img = Image.new("RGB", (width, height), (22, 24, 30))
    draw = ImageDraw.Draw(img)
    big, mid, small = _font(48), _font(30), _font(24)
    num_font = _font(46)

    draw.text((50, 42), "近期展会", font=big, fill=(240, 240, 245))
    draw.text((50, 108), f"即将举办 {len(upcoming)} 场", font=small, fill=(140, 146, 160))

    y = 176
    for ev in upcoming:
        days = _days_until(ev)
        # 天数：最大、橙色
        draw.text((50, y), f"{days}", font=num_font, fill=(255, 186, 80))
        offset = 46 + int(len(str(days)) * 26)
        draw.text((50 + offset, y + 12), "天", font=small, fill=(255, 186, 80))
        draw.text((190, y - 4), ev["name"][:16], font=mid, fill=(240, 240, 245))
        sub = " · ".join(
            x for x in (f"{ev['start']}~{ev['end']}", ev.get("city", ""),
                        ev.get("scale", "")) if x
        )
        draw.text((190, y + 40), sub[:34], font=small, fill=(150, 156, 170))
        y += row_h

    if past:
        draw.line((50, y + 6, width - 50, y + 6), fill=(58, 62, 72), width=2)
        y += 34
        for ev in past:
            over = max(0, int((now - ev["end_ts"]) // 86400))
            draw.text((50, y), f"{over}", font=num_font, fill=(110, 114, 126))
            offset = 46 + int(len(str(over)) * 26)
            draw.text((50 + offset, y + 12), "天前", font=small, fill=(110, 114, 126))
            draw.text((190, y - 4), ev["name"][:16], font=mid, fill=(150, 154, 166))
            draw.text((190, y + 40), f"已结束 {over} 天", font=small,
                      fill=(120, 124, 136))
            y += row_h

    stamp = datetime.now(CST).strftime("%m-%d %H:%M")
    draw.text((50, height - 46), f"数据：FEC 兽展日历 · 生成于 {stamp}",
              font=small, fill=(90, 94, 106))

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path
'''

start = s.index("def render_recent(events: list[dict]) -> Path:")
end = s.index("def render_city(")
s = s[:start] + new_recent + "\n\n" + s[end:]
print("render_recent rewritten")

# ---------- 3) 运势缓存按昵称区分，避免跨群串名 ----------
s = s.replace(
    'path = _card_path(f"fortune_{uid}")',
    'path = _card_path(f"fortune_{uid}_{name}")',
    1,
)
print("fortune cache per name")

# ---------- 4) 城市/省份匹配增强 ----------
s = s.replace(
    '''CITY_NAMES = [''',
    '''PROVINCES = [
    "江苏", "浙江", "广东", "四川", "山东", "河南", "湖北", "湖南", "河北", "福建",
    "安徽", "江西", "山西", "陕西", "辽宁", "吉林", "黑龙江", "云南", "贵州", "广西",
    "甘肃", "青海", "宁夏", "新疆", "西藏", "内蒙古", "海南", "台湾", "香港", "澳门",
]

CITY_NAMES = [''',
    1,
)

old_city = '''    city = ""
    for name in CITY_NAMES:
        if name in body_clean:
            city = name
            break'''
new_city = '''    city = ""
    for name in CITY_NAMES + PROVINCES:
        if name in body_clean:
            city = name
            break'''
if old_city in s:
    s = s.replace(old_city, new_city, 1)
    print("province matching added")

# 带城市名 + 展/下次/上次 -> 城市查询（即使没有"哪里"）
old_loop = '''    for key, pattern in COMMANDS:
        if pattern.search(body_clean):
            if key.startswith("city_"):
                return key, city
            return key, city

    if city:
        return "city_list", city
    return "", ""'''
new_loop = '''    for key, pattern in COMMANDS:
        if not pattern.search(body_clean):
            continue
        # 命中"下次展/上次展/有什么展"之类，且句子里带了城市/省份 -> 走城市查询
        if city and key in ("next", "recent", "city_list"):
            if "上次" in body_clean:
                return "city_past", city
            if "下次" in body_clean or "下一" in body_clean:
                return "city_next", city
            return "city_list", city
        if key.startswith("city_"):
            return key, city or "北京"
        return key, city

    if city:
        return "city_list", city
    return "", ""'''
if old_loop in s:
    s = s.replace(old_loop, new_loop, 1)
    print("city routing improved")

PLUGIN.write_text(s, encoding="utf-8")
print("done")
