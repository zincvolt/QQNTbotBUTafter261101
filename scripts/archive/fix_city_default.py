from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

# 1) 不再把空城市默认成北京
s = s.replace(
    '''        if key.startswith("city_"):
            return key, city or "北京"''',
    '''        if key.startswith("city_"):
            return key, city''',
    1,
)

# 2) city_next 没有城市时退化成全局下次展
s = s.replace(
    '''            if key == "city_next":
                target = city or "北京"''',
    '''            if key == "city_next" and not city:
                nxt = pick_next(events)
                if not nxt:
                    await event.send(event.plain_result("近期没有查到展会"))
                    event.stop_event()
                    return
                following = [e for e in events if e["start_ts"] >= nxt["start_ts"]][1:]
                await self._send_card(event, render_next(nxt, following), "next")
                return

            if key == "city_next":
                target = city''',
    1,
)
# city_past 也去掉北京默认
s = s.replace('''            if key == "city_past":
                target = city or "北京"''',
'''            if key == "city_past":
                target = city''', 1)
s = s.replace('''            if key == "city_past":
                target = city
                await self._send_card(event, render_city(target, events, "past"),''',
'''            if key == "city_past":
                target = city
                if not target:
                    await event.send(event.plain_result("说个城市名，比如 /上海上次展"))
                    event.stop_event()
                    return
                await self._send_card(event, render_city(target, events, "past"),''', 1)

p.write_text(s, encoding="utf-8")
print("defaults removed")
