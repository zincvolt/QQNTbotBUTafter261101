import asyncio, sys, types
from pathlib import Path
stub = types.ModuleType("astrbot"); api = types.ModuleType("astrbot.api")
class L:
    def info(self,*a,**k): pass
    def warning(self,*a,**k): print("WARN", *a)
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
m = SourceFileLoader("f4", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").load_module()
async def main():
    evs = await m.fetch_events()
    nxt = m.pick_next(evs)
    print("next:", nxt["name"], "thumb:", (nxt.get("thumb") or "")[:70])
    following = [e for e in evs if e["start_ts"] >= nxt["start_ts"]][1:]
    p = m.render_next(nxt, following)
    print("card:", p)
asyncio.run(main())
