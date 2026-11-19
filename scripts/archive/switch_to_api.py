"""Switch the bot back to the third-party API and unload local models."""

import json
import sys
import types
from pathlib import Path

stub = types.ModuleType("astrbot")
api = types.ModuleType("astrbot.api")


class _Logger:
    def info(self, *a, **k):
        print("INFO", *a)

    def warning(self, *a, **k):
        print("WARN", *a)


api.logger = _Logger()
api.star = types.SimpleNamespace(Star=object, Context=object)
stub.api = api
ev = types.ModuleType("astrbot.api.event")


class _Filter:
    EventMessageType = types.SimpleNamespace(ALL=1, GROUP_MESSAGE=2)

    def __getattr__(self, name):
        return lambda *a, **k: (lambda fn: fn)


ev.AstrMessageEvent = object
ev.filter = _Filter()
stub.api.event = ev
sys.modules.update({"astrbot": stub, "astrbot.api": api, "astrbot.api.event": ev})

from importlib.machinery import SourceFileLoader

mod = SourceFileLoader(
    "am3", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py"
).load_module()

print("provider:", mod.set_provider_mode("third_party"))
mod.tune_reply_for_mode("third_party")
print("thinking:", mod.set_thinking("off"))
print("vision:", mod.set_vision_mode("third_party"))
print("unloaded:", mod.unload_local_models())

state = mod.load_state()
state["mode"] = "third_party"
mod.save_state(state)

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
print("agent_runner:", json.dumps(cfg["agent_runner"]["config"]["model"], ensure_ascii=False))
reply = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))
print("reply:", {k: reply.get(k) for k in ("meme_chance", "dual_judge", "text_rules")})
