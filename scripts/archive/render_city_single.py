import asyncio, sys, types
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
m = SourceFileLoader("f6", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").load_module()
async def main():
    evs = await m.fetch_events()
    now = m.time.time()
    tokens = m.expand_place("江苏")
    hits = [e for e in evs if e["end_ts"] >= now and any(t in (e["city"]+e["region"]) for t in tokens)]
    nxt = hits[0]
    following = [e for e in evs if e["start_ts"] >= nxt["start_ts"]][1:3]
    print("下一场:", m._full_name(nxt), nxt["start"])
    print(m.render_next(nxt, following, title="江苏 · 下一次兽聚"))
asyncio.run(main())
