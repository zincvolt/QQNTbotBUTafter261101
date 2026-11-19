import asyncio, sys, time, types
from pathlib import Path
stub = types.ModuleType("astrbot"); api = types.ModuleType("astrbot.api")
class L:
    def info(self,*a,**k): pass
    def warning(self,*a,**k): pass
api.logger = L(); api.star = types.SimpleNamespace(Star=object, Context=object); stub.api = api
ev = types.ModuleType("astrbot.api.event")
class F:
    EventMessageType = types.SimpleNamespace(ALL=1, GROUP_MESSAGE=2)
    def __getattr__(self, n): return lambda *a, **k: (lambda fn: fn)
ev.AstrMessageEvent = object; ev.filter = F(); stub.api.event = ev
sys.modules.update({"astrbot": stub, "astrbot.api": api, "astrbot.api.event": ev})
from importlib.machinery import SourceFileLoader
m = SourceFileLoader("f7", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").load_module()

async def main():
    evs = await m.fetch_events()
    nxt = m.pick_next(evs)
    for label, fn in [
        ("next", lambda: m.render_next(nxt, [])),
        ("recent", lambda: m.render_recent(evs)),
        ("city", lambda: m.render_city("江苏", evs, "next")),
        ("fortune", lambda: m.render_fortune("1154487120", "测试")),
        ("stats", lambda: m.render_stats("942316942")),
    ]:
        t = time.perf_counter(); p = fn(); first = int((time.perf_counter()-t)*1000)
        t = time.perf_counter(); p2 = fn(); second = int((time.perf_counter()-t)*1000)
        print(f"{label:<8} 首次 {first:>4} ms   缓存命中 {second:>3} ms   {p.name}")
asyncio.run(main())
