import json, sys, types
from pathlib import Path
stub = types.ModuleType("astrbot"); api = types.ModuleType("astrbot.api")
class L:
    def info(self,*a,**k): print("INFO", *a)
    def warning(self,*a,**k): print("WARN", *a)
api.logger = L(); api.star = types.SimpleNamespace(Star=object, Context=object); stub.api = api
ev = types.ModuleType("astrbot.api.event")
class F:
    EventMessageType = types.SimpleNamespace(ALL=1, GROUP_MESSAGE=2)
    def __getattr__(self, n): return lambda *a, **k: (lambda fn: fn)
ev.AstrMessageEvent = object; ev.filter = F(); stub.api.event = ev
sys.modules.update({"astrbot": stub, "astrbot.api": api, "astrbot.api.event": ev})
from importlib.machinery import SourceFileLoader
m = SourceFileLoader("am2", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py").load_module()

print("切换到本地:")
print(" ", m.set_provider_mode("local"))
m.tune_reply_for_mode("local")
m.tune_local_provider()
m.set_vision_mode("local")
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
for p in cfg["provider"]:
    if p["id"] in ("local-llama","deepseek"):
        print(p["id"], "enable=", p.get("enable"), "body=", json.dumps(p.get("custom_extra_body"), ensure_ascii=False))
print("agent_runner:", json.dumps(cfg["agent_runner"]["config"]["model"], ensure_ascii=False))
reply = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
print("reply:", {k: reply.get(k) for k in ("meme_chance","dual_judge","text_rules")})
print("vision:", json.loads(Path(r"D:\QQNTBOT\data\vision_mode.json").read_text(encoding="utf-8"))["mode"])
