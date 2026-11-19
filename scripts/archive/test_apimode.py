import json, sys, types
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
m = SourceFileLoader("am", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py").load_module()
print("状态:", json.dumps(m.load_state(), ensure_ascii=False))
print("审查词数:", len(m.review_words()))
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print("provider 列表:", [(p["id"], p.get("enable")) for p in cfg["provider"]])
