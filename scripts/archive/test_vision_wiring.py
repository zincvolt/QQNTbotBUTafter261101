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
peer = SourceFileLoader("peer", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py").load_module()
print("peer 读模式:", peer._third_party_mode())
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
d = [p for p in cfg["provider"] if p["id"] == "deepseek"][0]
print("deepseek:", {k: d[k] for k in ("model", "modalities", "enable", "api_base")})
