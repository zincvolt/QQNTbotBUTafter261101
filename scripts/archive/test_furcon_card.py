"""Standalone check: fetch FEC events and render one countdown card."""

import asyncio
import json
import sys
from pathlib import Path

# 只借用插件的纯函数：把模块里的 astrbot 依赖替换成桩
import types

stub_api = types.ModuleType("astrbot.api")


class _Dummy:
    """Placeholder that tolerates any attribute access."""

    def __getattr__(self, name):
        return lambda *a, **k: None


stub_api.logger = _Dummy()
stub_api.star = types.SimpleNamespace(Star=object, Context=object)
sys.modules["astrbot"] = types.ModuleType("astrbot")
sys.modules["astrbot.api"] = stub_api

event_mod = types.ModuleType("astrbot.api.event")


class _Filter:
    """No-op decorator factory."""

    def __getattr__(self, name):
        def deco(*a, **k):
            def wrap(fn):
                return fn

            return wrap

        return deco


class _Event:
    """Placeholder event type."""


event_mod.AstrMessageEvent = _Event
_F = _Filter()
_F.EventMessageType = type("E", (), {"GROUP_MESSAGE": 1})()
event_mod.filter = _F
sys.modules["astrbot.api.event"] = event_mod


async def main() -> None:
    """Fetch events, print the next ones, render a card."""
    from importlib.machinery import SourceFileLoader

    mod = SourceFileLoader(
        "furcon", r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py"
    ).load_module()
    events = await mod.fetch_events(force=True)
    print("抓到展会:", len(events))
    for e in events[:5]:
        print(f"  {e['start']} ~ {e['end']}  {e['name'][:18]}  {e['city']}  {e['scale']}")
    nxt = mod.pick_next(events)
    print("\n最近一场:", nxt["name"], nxt["start"])
    upcoming = [x for x in events if x["start_ts"] >= nxt["start_ts"]][1:]
    card = mod.render_card(nxt, upcoming)
    print("卡片:", card)


asyncio.run(main())
