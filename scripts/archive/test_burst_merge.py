"""话段聚合 + 强触发规则的离线自测（不联网、不读聊天记录）。

用 object.__new__ 绕开 AstrBot 的构造依赖，只测判定用的纯逻辑。
运行：python scripts/archive/test_burst_merge.py
"""

import asyncio
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT")
sys.path.insert(0, str(ROOT / "apps" / "AstrBot"))

from astrbot.builtin_stars.astrbot.group_chat_context import (  # noqa: E402
    GroupChatContext,
    load_judge_api_config,
)

CFG = dict(load_judge_api_config())
CFG["bot_names"] = ["阿灰", "灰灰"]
CFG["break_words"] = ["傻逼", "滚", "智障"]
UMO = "test:group:1"

failures = []


def check(name, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + f"{name}: got={got!r} want={want!r}")
    if not ok:
        failures.append(name)


def new_ctx():
    ctx = object.__new__(GroupChatContext)
    ctx._locks = {}
    ctx.raw_records = defaultdict(deque)
    ctx._record_ids = defaultdict(deque)
    ctx._record_times = defaultdict(deque)
    ctx._reply_times = defaultdict(deque)
    ctx._last_bot = {}
    ctx._inflight_until = {}
    ctx._cool_until = {}
    ctx._last_trigger = {}
    ctx._last_arrival = {}
    ctx._prev_arrival = {}
    ctx._last_bot_at = {}
    ctx._burst = {}
    return ctx


def test_suppression():
    print("\n[1] 在途 / 冷却")
    ctx = new_ctx()
    ctx._mark_trigger(UMO, "随便一句", CFG)
    check("判定通过后在途>0", ctx._inflight_for(UMO) > 0, True)
    check("在途期间冷却为0", ctx._suppressed_for(UMO) > 0, True)
    ctx.note_bot_reply(UMO, "回完了")
    check("发完后在途清零", ctx._inflight_for(UMO), 0.0)
    check("发完后冷却>0", ctx._suppressed_for(UMO) > 0, True)
    check("冷却时长≈reply_gap", round(ctx._suppressed_for(UMO)), CFG["reply_gap"])


def test_break_rules():
    print("\n[2] 强触发：往上看是不是在说自己")
    ctx = new_ctx()
    now = time.time()
    # 上一条是它说的（prev_arrival 早于 last_bot_at）
    ctx._prev_arrival[UMO] = now - 5
    ctx._last_bot_at[UMO] = now - 3
    check("骂人+你+上条是它 → 打破", ctx._break_allowed(UMO, "你傻逼吧", CFG), True)
    check("骂人无你但上条是它 → 打破", ctx._break_allowed(UMO, "傻逼", CFG), True)
    check("叫名字 → 打破", ctx._break_allowed(UMO, "阿灰在吗滚出来", CFG), True)
    check("不带触发词 → 不打破", ctx._break_allowed(UMO, "今天吃点啥", CFG), False)

    # 上一条是别人说的：骂的是别人，不该插嘴
    ctx2 = new_ctx()
    ctx2._prev_arrival[UMO] = now - 1
    ctx2._last_bot_at[UMO] = now - 40
    check("骂人+你+上条是别人 → 不打破", ctx2._break_allowed(UMO, "你傻逼吧", CFG), False)
    check("上条是别人但叫名字 → 打破", ctx2._break_allowed(UMO, "灰灰你说呢", CFG), True)


def test_burst_block():
    print("\n[3] 话段复用（省 token）")
    ctx = new_ctx()
    now = time.time()
    # 前提：它刚说过话（否则「你傻逼吧」骂的不是它，规则本来就不该打破）
    ctx._prev_arrival[UMO] = now - 5
    ctx._last_bot_at[UMO] = now - 3
    ctx._burst[UMO] = {"last": now, "until": now + 45, "why": "answered"}
    check("同段普通消息被挡", ctx._burst_blocked(UMO, "然后呢", CFG), True)
    check("同段骂它 → 放行", ctx._burst_blocked(UMO, "你傻逼吧", CFG), False)
    check("放行后状态清掉", UMO in ctx._burst, False)

    ctx2 = new_ctx()
    ctx2._burst[UMO] = {"last": now - 60, "until": now + 45, "why": "judged"}
    check("冷场超过 burst_gap → 算新段", ctx2._burst_blocked(UMO, "新话题", CFG), False)

    ctx3 = new_ctx()
    ctx3._burst[UMO] = {"last": now - 50, "until": now - 1, "why": "judged"}
    check("复用到期 → 放行", ctx3._burst_blocked(UMO, "新话题", CFG), False)


def test_burst_text():
    print("\n[4] 拆句合并后不算「过短」")
    ctx = new_ctx()
    now = time.time()
    for text in ("我刚买了个", "特别奇怪的东西", "你猜是啥"):
        ctx.raw_records[UMO].append(f"[群友]: {text}")
        ctx._record_times[UMO].append(now)
    merged = ctx._burst_text(UMO, "哈哈哈", CFG)
    check("合并包含前面分句", "我刚买了个" in merged, True)
    check("合并长度 > 3", len(merged) > 3, True)
    check("单条只有 3 字也不会被过短挡", len("哈哈哈") <= 3 and len(merged) > 3, True)


async def test_settle_relay():
    print("\n[5] 拆句：只有最后一条去判定")
    ctx = new_ctx()
    cfg = dict(CFG)
    cfg["burst_settle"] = 0.6
    calls = []

    async def fake_inner(event, _cfg, _api, summon_hit=""):
        calls.append(getattr(event, "tag", "?"))
        return True

    ctx._need_active_reply_api_inner = fake_inner

    class Ev:
        def __init__(self, tag, text):
            self.unified_msg_origin = UMO
            self.message_str = text
            self.tag = tag

    # 三句拆发：间隔 0.2s，模拟同一口气
    async def sender(tag, text, at):
        await asyncio.sleep(at)
        return await ctx._need_active_reply_api(Ev(tag, text), cfg, cfg, "")

    results = await asyncio.gather(
        sender("m1", "我刚买了个", 0.0),
        sender("m2", "特别奇怪的东西", 0.2),
        sender("m3", "你猜是啥", 0.4),
    )
    check("只有一条判定通过", results.count(True), 1)
    check("去判定的是最后一条", calls, ["m3"])


def main():
    test_suppression()
    test_break_rules()
    test_burst_block()
    test_burst_text()
    asyncio.run(test_settle_relay())
    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
