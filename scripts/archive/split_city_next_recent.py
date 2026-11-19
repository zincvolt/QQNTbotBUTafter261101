"""Split "city next" (single event) from "city recent" (list)."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) 新命令 city_recent：某地近期展
s = s.replace(
    '    ("recent", re.compile(',
    '    ("city_recent", re.compile(r"(近期展|近期兽聚|最近的展|最近有什么|最近有哪些)")),\n'
    '    ("recent", re.compile(',
    1,
)

# 2) 路由：带城市 + 近期展 -> city_recent；带城市 + 下次展 -> city_next（单场）
old = '''        if city and key in ("next", "recent", "city_list"):
            if "上次" in body_clean:
                return "city_past", city
            if "下次" in body_clean or "下一" in body_clean:
                return "city_next", city
            return "city_list", city'''
new = '''        if city and key in ("next", "recent", "city_recent", "city_list"):
            if "上次" in body_clean:
                return "city_past", city
            if "下次" in body_clean or "下一" in body_clean or "下一场" in body_clean:
                return "city_next", city
            return "city_recent", city'''
if old in s:
    s = s.replace(old, new, 1)
    print("routing updated")

# 3) render_next 支持标题，方便城市单场卡复用
s = s.replace(
    '''def render_next(event: dict, following: list[dict], elapsed_ms: int = 0,
                updated: str = "") -> Path:
    """Draw the countdown card for the next convention."""
    path = _card_path("next")''',
    '''def render_next(event: dict, following: list[dict], elapsed_ms: int = 0,
                updated: str = "", title: str = "下一次兽聚") -> Path:
    """Draw the countdown card for one convention."""
    path = _card_path(f"next_{title}")''',
    1,
)
s = s.replace('draw.text((60, y), "下一次兽聚", font=small_font, fill=(140, 146, 160))',
              'draw.text((60, y), title[:16], font=small_font, fill=(140, 146, 160))', 1)
print("render_next title param")

# 4) handle：city_next 出单场；city_recent/city_list 出列表
old_handle = '''            if key in ("recent", "city_list", "city_all"):
                await self._send_card(event, render_recent(events), key)
                return

            if key in ("city_next", "city_past"):
                target = city or "北京"
                mode = "past" if key == "city_past" else "next"
                await self._send_card(event, render_city(target, events, mode),
                                      f"{key}_{target}")
                return'''
new_handle = '''            if key == "recent":
                await self._send_card(event, render_recent(events), key)
                return

            if key in ("city_recent", "city_list", "city_all"):
                if city:
                    await self._send_card(event, render_city(city, events, "next"),
                                          f"city_recent_{city}")
                else:
                    await self._send_card(event, render_recent(events), key)
                return

            if key == "city_past":
                target = city or "北京"
                await self._send_card(event, render_city(target, events, "past"),
                                      f"city_past_{target}")
                return

            if key == "city_next":
                target = city or "北京"
                tokens = expand_place(target)
                now = time.time()
                hits = [
                    e
                    for e in events
                    if e["end_ts"] >= now
                    and any(
                        t in (str(e.get("city", "")) + str(e.get("region", "")))
                        for t in tokens
                    )
                ]
                if not hits:
                    await event.send(
                        event.plain_result(f"{target}近期没有查到展会")
                    )
                    event.stop_event()
                    return
                following = [e for e in events if e["start_ts"] >= hits[0]["start_ts"]][1:3]
                card = render_next(hits[0], following, title=f"{target} · 下一次兽聚")
                await self._send_card(event, card, f"city_next_{target}")
                return'''
if old_handle in s:
    s = s.replace(old_handle, new_handle, 1)
    print("handler split")

PLUGIN.write_text(s, encoding="utf-8")
print("done")
