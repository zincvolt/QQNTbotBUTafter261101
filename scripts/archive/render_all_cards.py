"""Render every card type once for visual inspection."""

import asyncio
import sys
import types
from pathlib import Path

# --- 给插件补最小桩，脱离 AstrBot 运行时 ---
stub_astrbot = types.ModuleType("astrbot")
stub_api = types.ModuleType("astrbot.api")


class _Logger:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


stub_api.logger = _Logger()
stub_api.star = types.SimpleNamespace(Star=object, Context=object)
stub_astrbot.api = stub_api

ev = types.ModuleType("astrbot.api.event")


class _Filter:
    EventMessageType = types.SimpleNamespace(ALL=1, GROUP_MESSAGE=2)

    def __getattr__(self, name):
        def deco(*a, **k):
            def wrap(fn):
                return fn

            return wrap

        return deco


ev.AstrMessageEvent = object
ev.filter = _Filter()
stub_astrbot.api.event = ev
sys.modules["astrbot"] = stub_astrbot
sys.modules["astrbot.api"] = stub_api
sys.modules["astrbot.api.event"] = ev


async def main() -> None:
    """Generate all card variants."""
    from importlib.machinery import SourceFileLoader

    mod = SourceFileLoader(
        "furcon2",
        r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py",
    ).load_module()

    events = await mod.fetch_events()
    print("events:", len(events))

    print("recent   ->", mod.render_recent(events))
    print("city next->", mod.render_city("上海", events, "next"))
    print("city past->", mod.render_city("广州", events, "past"))
    print("fortune  ->", mod.render_fortune("1154487120", "电池叔叔不约"))
    print("stats    ->", mod.render_stats("942316942"))


asyncio.run(main())
