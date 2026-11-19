"""话段聚合、发送耗时估算与强触发规则的离线自测。

不联网、不读聊天记录。用 object.__new__ 绕开 AstrBot 的构造依赖。
运行：apps/AstrBot/.venv/Scripts/python.exe scripts/archive/test_burst_merge.py
"""

import asyncio
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(r"D:\QQNTBOT")
sys.path.insert(0, str(ROOT / "apps" / "AstrBot"))

import astrbot.builtin_stars.astrbot.group_chat_context as gcc  # noqa: E402
from astrbot.builtin_stars.astrbot.group_chat_context import (  # noqa: E402
    GroupChatContext,
    load_judge_api_config,
)

CFG = dict(load_judge_api_config())
CFG["bot_names"] = ["阿灰", "灰灰"]
CFG["break_words"] = ["傻逼", "滚", "智障"]
CFG["burst_enable"] = True
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
    ctx._last_bot_span = {}
    ctx._burst = {}
    return ctx


def test_suppression():
    print("\n[1] 在途 / 冷却")
    ctx = new_ctx()
    ctx._mark_trigger(UMO, "随便一句", CFG)
    check("判定通过后在途>0", ctx._inflight_for(UMO) > 0, True)
    check("在途期间冷却>0", ctx._suppressed_for(UMO) > 0, True)
    check("在途上限≈inflight_ttl", round(ctx._inflight_for(UMO)), CFG["inflight_ttl"])


def test_send_estimate():
    print("\n[2] 发送耗时估算（分段发送）")
    seg = gcc._load_segmented_reply()
    check("读到 AstrBot 分段配置", seg["enable"], True)
    check("分段方式=human", seg["interval_method"] == "human", True)

    many_short = gcc._estimate_send_seconds("一。二。三。")
    one_long = gcc._estimate_send_seconds("一二三四五六。")
    check("三段短句比一段长句更耗时", many_short > one_long, True)
    check("三段短句估算在 2-6 秒", 2.0 < many_short < 6.0, True)
    check("单句估算>0", one_long > 0.5, True)

    text = "第一句话。第二句话。第三句话。"
    mean = gcc._estimate_send_seconds(text)
    upper = gcc._estimate_send_seconds(text, upper=True)
    check("上沿严格大于均值（锁在途必须用上沿）", upper > mean, True)
    check("上沿按最坏抖动+停顿算 > 2 倍均值", upper > mean * 2, True)

    parts = gcc._split_segments("第一句。第二句！第三句？", seg)
    check("正则切出 3 段", len(parts), 3)


def test_note_reply():
    print("\n[3] 生成完 ≠ 发完，冷却从发完起算")
    gcc.is_third_party_mode = lambda: True
    ctx = new_ctx()
    ctx.note_bot_reply(UMO, "第一句话。第二句话。第三句话。")
    inflight = ctx._inflight_for(UMO)
    check("发送期间算在途", inflight > 1.5, True)
    check("冷却延到发完之后", ctx._suppressed_for(UMO) > inflight, True)
    span = ctx._last_bot_span.get(UMO)
    check("记了发言区间", bool(span) and span[1] > span[0], True)

    gcc.is_third_party_mode = lambda: False
    ctx2 = new_ctx()
    ctx2.note_bot_reply(UMO, "本地模式不该写状态")
    check("本地模式零侵入", ctx2._inflight_until, {})
    check("本地模式不记发言区间", ctx2._last_bot_span, {})
    gcc.is_third_party_mode = lambda: True


def test_sent_signal():
    print("\n[3b] 真实发完信号（after_message_sent）")
    gcc.is_third_party_mode = lambda: True
    ctx = new_ctx()
    ctx.note_bot_reply(UMO, "第一句话。第二句话。")
    check("生成完先按上沿锁住", ctx._inflight_for(UMO) > 3, True)

    # 非本插件触发的发送完成：不能顺手把在途放掉
    ctx.note_message_sent(UMO, owned=False)
    check("非本插件发送不动在途", ctx._inflight_for(UMO) > 3, True)

    ctx.note_message_sent(UMO, owned=True)
    check("真实发完立刻释放在途", round(ctx._inflight_for(UMO)), 0)
    check("冷却从发完起算", ctx._suppressed_for(UMO) > 0, True)
    span = ctx._last_bot_span.get(UMO)
    check("发言区间收敛到真实发完", bool(span) and span[1] <= time.time() + 0.5, True)

    # 没有在途时，别的回复发完不应给群加冷却
    ctx2 = new_ctx()
    ctx2.note_message_sent(UMO, owned=True)
    check("无在途时不凭空加冷却", ctx2._cool_until, {})

    gcc.is_third_party_mode = lambda: False
    ctx3 = new_ctx()
    ctx3.note_message_sent(UMO, owned=True)
    check("本地模式不写任何状态", ctx3._cool_until, {})
    gcc.is_third_party_mode = lambda: True


class FakeEvent:
    """够 on_req_llm 的 @ 拦截分支用，不构造真实 AstrBot 事件。"""

    def __init__(self, text, at=True, command=False):
        self.unified_msg_origin = UMO
        self.message_str = text
        self.is_at_or_wake_command = at
        self._extra = {"handlers_parsed_params": {"k": "v"}} if command else {}
        self.stopped = False

    def get_extra(self, key, default=None):
        return self._extra.get(key, default)

    def get_message_type(self):
        return gcc.MessageType.GROUP_MESSAGE

    def set_extra(self, key, value):
        self._extra[key] = value

    def stop_event(self):
        self.stopped = True


async def test_at_hard_lock():
    print("\n[8] 正在回复时 @ 它 / 唤醒前缀硬锁")
    gcc.is_third_party_mode = lambda: True
    ctx = new_ctx()

    # 无在途：这条 @ 先占住在途，然后才允许生成
    ev = FakeEvent("阿灰你说啥")
    await ctx.on_req_llm(ev, None)
    check("@ 触发的回复自己占在途", ctx._inflight_for(UMO) > 0, True)
    check("@ 首次不被拦", ev.stopped, False)
    check("已标记本插件认领", bool(ev.get_extra("_judge_inflight_owned")), True)

    # 在途期间再来一条 @：必须停掉事件（pipeline 因此不调 LLM）
    ev2 = FakeEvent("阿灰在吗")
    await ctx.on_req_llm(ev2, None)
    check("在途期间 @ 被停事件", ev2.stopped, True)

    # 同一条消息多轮工具调用：已认领的不再被自己拦
    ev3 = FakeEvent("阿灰你说啥")
    ev3.set_extra("_judge_inflight_owned", True)
    await ctx.on_req_llm(ev3, None)
    check("同一事件多轮不被自己拦", ev3.stopped, False)

    # @ + 明确指令：不该被聊天锁吞掉
    ev4 = FakeEvent("/reset", command=True)
    await ctx.on_req_llm(ev4, None)
    check("@ + 指令不被聊天锁拦", ev4.stopped, False)

    # 非 @ 的普通消息不走这里（由判官那套处理）
    ev5 = FakeEvent("今天吃啥")
    ev5.is_at_or_wake_command = False
    await ctx.on_req_llm(ev5, None)
    check("普通消息不被这里拦", ev5.stopped, False)

    # 关掉 inflight_lock 就退回原行为
    ctx2 = new_ctx()
    ctx2._inflight_until[UMO] = time.time() + 30
    off = dict(CFG)
    off["inflight_lock"] = False
    gcc.load_judge_api_config = lambda: off
    try:
        ev6 = FakeEvent("阿灰在吗")
        await ctx2.on_req_llm(ev6, None)
        check("inflight_lock=off 时不拦 @", ev6.stopped, False)
    finally:
        gcc.load_judge_api_config = load_judge_api_config

    gcc.is_third_party_mode = lambda: False
    try:
        ctx3 = new_ctx()
        deadline = time.time() + 30
        ctx3._inflight_until[UMO] = deadline
        ev7 = FakeEvent("阿灰在吗")
        await ctx3.on_req_llm(ev7, None)
        check("本地模式完全不拦", ev7.stopped, False)
        check("本地模式不占在途", ctx3._inflight_until.get(UMO) == deadline, True)
    finally:
        gcc.is_third_party_mode = lambda: True



def test_break_rules():
    print("\n[4] 点名 / 脏话 / 骂的是谁")
    ctx = new_ctx()
    now = time.time()
    ctx._prev_arrival[UMO] = now - 2
    ctx._last_bot_span[UMO] = (now - 5, now - 1)
    check("上条落在发言区间 → 在跟它说话", ctx._bot_spoke_last(UMO), True)
    check("叫名字=硬触发", ctx._hard_break(UMO, "阿灰你说呢", CFG), True)
    check("叫名字=值得放行", ctx._break_allowed(UMO, "阿灰你说呢", CFG), True)
    check("脏话也放行（交给判官判谁）", ctx._break_allowed(UMO, "你傻逼吧", CFG), True)
    check("脏话不是硬触发", ctx._hard_break(UMO, "你傻逼吧", CFG), False)
    check("无触发词不放行", ctx._break_allowed(UMO, "今天吃点啥", CFG), False)

    ctx2 = new_ctx()
    ctx2._prev_arrival[UMO] = now - 600
    ctx2._last_bot_span[UMO] = (now - 5, now - 1)
    check("上条远早于它发言 → 不是在跟它说话", ctx2._bot_spoke_last(UMO), False)


def test_burst_block():
    print("\n[5] 话段复用（省 token）")
    ctx = new_ctx()
    now = time.time()
    ctx._burst[UMO] = {"last": now, "until": now + 45, "why": "answered"}
    check("同段普通消息被挡", ctx._burst_blocked(UMO, "然后呢", CFG), True)
    check("同段点名 → 放行", ctx._burst_blocked(UMO, "阿灰你说呢", CFG), False)
    check("放行后状态清掉", UMO in ctx._burst, False)

    ctx2 = new_ctx()
    ctx2._burst[UMO] = {"last": now - 60, "until": now + 45, "why": "judged"}
    check("冷场超过 burst_gap → 算新段", ctx2._burst_blocked(UMO, "新话题", CFG), False)

    ctx3 = new_ctx()
    ctx3._burst[UMO] = {"last": now - 50, "until": now - 1, "why": "judged"}
    check("复用到期 → 放行", ctx3._burst_blocked(UMO, "新话题", CFG), False)

    ctx4 = new_ctx()
    off = dict(CFG)
    off["burst_enable"] = False
    ctx4._burst[UMO] = {"last": now, "until": now + 45, "why": "answered"}
    check("关掉 burst_enable 就完全不复用", ctx4._burst_blocked(UMO, "然后呢", off), False)


def test_burst_text():
    print("\n[6] 拆句合并后不算「过短」")
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
    print("\n[7] 拆句：只有最后一条去判定")
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
    test_send_estimate()
    test_note_reply()
    test_sent_signal()
    test_break_rules()
    test_burst_block()
    test_burst_text()
    asyncio.run(test_settle_relay())
    asyncio.run(test_at_hard_lock())
    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
