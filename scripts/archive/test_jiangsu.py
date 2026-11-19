import asyncio, sys, types
from pathlib import Path
stub = types.ModuleType("astrbot"); api = types.ModuleType("astrbot.api")
class L:
    def info(self,*a,**k): pass
    def warning(self,*a,**k): pass
api.logger = L(); api.star = types.SimpleNamespace(Star=object, Context=object)
stub.api = api
ev = types.ModuleType("astrbot.api.event")
class F:
    EventMessageType = types.SimpleNamespace(ALL=1, GROUP_MESSAGE=2)
    def __getattr__(self, n):
        def d(*a, **k):
            return lambda fn: fn
        return d
ev.AstrMessageEvent = object; ev.filter = F()
stub.api.event = ev
sys.modules.update({"astrbot": stub, "astrbot.api": api, "astrbot.api.event": ev})
from importlib.machinery import SourceFileLoader
m = SourceFileLoader("f3", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").load_module()
async def main():
    evs = await m.fetch_events()
    print("江苏 ->", m.render_city("江苏", evs, "next"))
    rows = [e for e in evs if any(t in (e["city"]+e["region"]) for t in m.expand_place("江苏"))]
    for e in rows[:5]:
        print("   ", e["start"], e["name"], e["city"], e["region"])
asyncio.run(main())
