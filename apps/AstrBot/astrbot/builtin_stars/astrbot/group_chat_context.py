import asyncio
import datetime
import difflib
import json
import random
import re
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path

import httpx

from astrbot import logger
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import (
    At,
    AtAll,
    Face,
    File,
    Forward,
    Image,
    Json,
    Plain,
    Record,
    Reply,
    Video,
)
from astrbot.api.platform import MessageType
from astrbot.api.provider import Provider, ProviderRequest
from astrbot.core.agent.message import TextPart
from astrbot.core.astrbot_config_mgr import AstrBotConfigManager

"""
Group chat context awareness.
"""

GROUP_HISTORY_HEADER = (
    "<system_reminder>"
    "你在一个 QQ 群里。下面是自你上次发言以来的群聊记录，"
    "每行开头的方括号是【说话人昵称/时间】，不同昵称是不同的人，"
    "不要把别人的话当成同一个人说的。\n"
    "--- BEGIN CONTEXT---\n"
)
GROUP_HISTORY_FOOTER = (
    "\n--- END CONTEXT ---\n"
    "（以上每行方括号里是说话人，请区分不同的人；"
    "只有最后一条 user 消息是要你回的）"
    "</system_reminder>"
)
DEFAULT_GROUP_MESSAGE_MAX_CNT = 1000

# 判官的提示词与关键词规则放在这里，控制台可直接编辑
JUDGE_CONFIG_PATH = Path(r"D:\QQNTBOT\data\judge.json")
DEFAULT_JUDGE_PROMPT = (
    "你在一个 QQ 群里，是个老群友。下面是刚才的对话和一条新消息。\n"
    "判断你要不要接这句话。\n"
    "接的情况：有人 @ 你或点名；有人提了一个具体、能回答的问题；"
    "有人在倾诉、情绪不好、骂街吐槽（接一句安慰或共鸣）；"
    "话题正好是兽圈、猎奇、gore 设定、游戏这类你熟的；你能补一句有用的。\n"
    "不接的情况：普通寒暄、已经有人在回答、你看不懂、"
    "或者你接了也只能说不知道。\n"
    "最近聊天：\n{recent}\n\n"
    "新消息：{message}\n\n"
    "只输出 1 或 0，不要解释。"
)

_judge_cache: dict = {"mtime": 0.0, "data": None}

# 第三方模式专用的判官配置（独立密钥/规则/额度，不写在 judge.json 里）
JUDGE_API_CONFIG_PATH = Path(r"D:\QQNTBOT\data\judge_api.json")
DEFAULT_JUDGE_API_PROMPT = (
    "你是群聊接话判定器。判断机器人要不要接最后一条消息。\n"
    "规则：\n"
    "- @ 机器人、叫它名字、纠错或追问它刚才说的话 → 1\n"
    "- 向它提问、倾诉、求助 → 1\n"
    "- 别人互相聊天、陈述自己的安排、跟它无关 → 0\n"
    "- 骂人、复读、纯表情 → 0\n"
    "最近聊天：\n{recent}\n\n"
    "你刚才说：{last_bot}\n\n"
    "新消息：{message}\n\n"
    "只输出 1 或 0。"
)
_judge_api_cache: dict = {"mtime": 0.0, "data": None}

# 主模型 provider 的唯一真相（和 /切换 共用同一个配置）
PROVIDER_CONFIG_PATH = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")
_provider_cache: dict = {"mtime": 0.0, "id": ""}

# 分段发送配置：一句话拆成几段发、每段隔多久，决定「回复真正发完」的时刻
_segmented_cache: dict = {"mtime": 0.0, "data": None}
DEFAULT_SEGMENTED_REPLY = {
    "enable": False,
    "interval_method": "random",
    "interval": [1.5, 3.5],
    "log_base": 2.6,
    "split_mode": "regex",
    "regex": r"[^。！？~…\n]+[。！？~…\n]*",
    "split_words": ["。", "？", "！", "~", "…"],
}
# 每段发送的网络往返（NapCat → QQ），实测 0.2-0.4 秒
SEGMENT_NETWORK_COST = 0.25
# 取上沿时用最慢的一档：估长了只是多锁几秒，估短了会双发
SEGMENT_NETWORK_UPPER = 0.4


def _load_segmented_reply() -> dict:
    """读 AstrBot 的 ``platform_settings.segmented_reply``。

    分段发送是 AstrBot 自带功能，每段之间会 ``sleep``。判定「回复是否还在
    发送中」必须按这份配置算，不能拍一个固定秒数。

    Returns:
        归一化后的分段配置；读不到就用默认值（关闭）。
    """
    global _segmented_cache
    try:
        stat = PROVIDER_CONFIG_PATH.stat()
    except OSError:
        return DEFAULT_SEGMENTED_REPLY
    if stat.st_mtime == _segmented_cache["mtime"] and _segmented_cache["data"]:
        return _segmented_cache["data"]
    data = dict(DEFAULT_SEGMENTED_REPLY)
    try:
        raw = json.loads(PROVIDER_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        seg = (raw.get("platform_settings") or {}).get("segmented_reply") or {}
        if isinstance(seg, dict):
            data["enable"] = bool(seg.get("enable", False))
            data["interval_method"] = str(
                seg.get("interval_method") or data["interval_method"]
            )
            interval = seg.get("interval")
            if isinstance(interval, str):
                try:
                    parts = [float(x) for x in interval.replace(" ", "").split(",")]
                    if len(parts) == 2:
                        data["interval"] = parts
                except ValueError:
                    pass
            try:
                data["log_base"] = float(seg.get("log_base") or data["log_base"])
            except (TypeError, ValueError):
                pass
            data["split_mode"] = str(seg.get("split_mode") or data["split_mode"])
            data["regex"] = str(seg.get("regex") or data["regex"])
            words = seg.get("split_words")
            if isinstance(words, list) and words:
                data["split_words"] = [str(w) for w in words if str(w)]
    except (json.JSONDecodeError, OSError):
        pass
    _segmented_cache = {"mtime": stat.st_mtime, "data": data}
    return data


def _split_segments(text: str, seg: dict) -> list[str]:
    """按 AstrBot 的规则把回复切成若干段（只要段数，不需要完全一致）。"""
    text = (text or "").strip()
    if not text:
        return []
    if seg["split_mode"] == "regex":
        try:
            parts = [p for p in re.findall(seg["regex"], text) if p.strip()]
        except re.error:
            parts = [text]
    elif seg["split_mode"] == "words":
        pattern = "|".join(re.escape(w) for w in seg["split_words"] if w)
        parts = [p for p in re.split(f"({pattern})", text) if p and p.strip()]
    else:
        parts = [text]
    return parts or [text]


def _estimate_send_seconds(text: str, upper: bool = False) -> float:
    """估算这条回复从开始发送到全部发完需要多少秒。

    分段算法照抄 AstrBot ``core/pipeline/respond/stage.py`` 的
    ``_calc_comp_interval``：human 模式每段 ``0.45 + 字数/7``，乘 0.75~1.35
    抖动，15% 概率再停 0.8~1.8 秒，单段上限 5.5 秒；每段还有网络往返。

    Args:
        text: 模型产出的完整回复。
        upper: ``True`` 取最坏情况上沿（最大抖动 + 一定发生停顿 + 最慢网络）。
            锁「正在发送」必须用上沿：取均值会有一半概率低估，估短了就会在
            真正发完之前放开锁。上沿只在真实发完信号到达前顶一下，不会长期多锁。

    Returns:
        估算秒数；未开分段时返回单条发送的耗时（约 0.3 秒）。
    """
    seg = _load_segmented_reply()
    parts = _split_segments(text, seg) if seg["enable"] else [text or ""]
    if not parts:
        return SEGMENT_NETWORK_COST
    method = seg["interval_method"]
    total = 0.0
    for part in parts:
        chars = len(part.strip())
        if method == "human":
            delay = 0.45 + chars / 7.0
            if upper:
                # 与 AstrBot 同序：先乘抖动、再加停顿、最后截断
                delay = min(delay * 1.35 + 1.8, 5.5)
            else:
                delay *= 1.05  # uniform(0.75, 1.35) 的均值
                delay += 0.195  # 15% 概率额外 0.8~1.8s 的期望
                delay = min(delay, 5.5)
        elif method == "log":
            import math

            base = math.log(chars + 1, max(1.1, seg["log_base"]))
            delay = base + (0.5 if upper else 0.25)  # uniform(base, base+0.5)
        else:
            low, high = seg["interval"]
            delay = high if upper else (low + high) / 2
        total += delay + (SEGMENT_NETWORK_UPPER if upper else SEGMENT_NETWORK_COST)
    return total


# 按群的自动接话开关，缺省等于全开
MAIN_JUDGE_URL = "http://127.0.0.1:8080/v1/chat/completions"
MAIN_JUDGE_KEY = "sk-llm-7d41c9e2"

AUTOREPLY_CONFIG_PATH = Path(r"D:\QQNTBOT\data\autoreply.json")
_autoreply_cache: dict = {"mtime": 0.0, "data": None}

# access 插件 /群聊 指令写的群开关（与 autoreply.json 二选一即可关接话，
# 两个面板口径一致：任一为关，判官在任何规则/LLM 调用之前就短路）
GROUP_FLAGS_PATH = Path(
    r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_access\group_flags.json"
)
_group_flags_cache: dict = {"mtime": 0.0, "data": {}}


def load_group_flags() -> dict:
    """Read access 插件的群开关，mtime 缓存。缺文件/缺群 = 接话默认开。

    Returns:
        ``{gid: {"proactive": bool, "reply_at": bool, "welcome": bool}}``。
    """
    global _group_flags_cache
    try:
        stat = GROUP_FLAGS_PATH.stat()
    except OSError:
        return _group_flags_cache["data"]
    if _group_flags_cache["data"] and stat.st_mtime == _group_flags_cache["mtime"]:
        return _group_flags_cache["data"]
    try:
        raw = json.loads(GROUP_FLAGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _group_flags_cache["data"]
    data = {}
    for gid, conf in (raw.get("groups") or {}).items():
        if isinstance(conf, dict):
            data[str(gid)] = conf
    _group_flags_cache = {"mtime": stat.st_mtime, "data": data}
    return data



REPLY_CONFIG_PATH = Path(r"D:\QQNTBOT\data\reply.json")
_ar_chance_cache: dict = {"mtime": 0.0, "value": 1.0}


def load_reply_chance() -> float:
    """主动回复概率（判官说接了之后，还按这个概率再抽一次）。

    Returns:
        float: 0~1，1 表示判官说接就接。
    """
    global _ar_chance_cache
    try:
        stat = REPLY_CONFIG_PATH.stat()
    except OSError:
        return 1.0
    if stat.st_mtime == _ar_chance_cache["mtime"]:
        return _ar_chance_cache["value"]
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        value = float(raw.get("reply_chance", 1.0))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        value = 1.0
    value = max(0.0, min(1.0, value))
    _ar_chance_cache = {"mtime": stat.st_mtime, "value": value}
    return value


def load_dual_judge() -> dict:
    """读取双判官配置。

    Returns:
        dict: ``enable``(bool) 与 ``model``(str)。
    """
    data = {"enable": False, "model": ""}
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return data
    data["enable"] = bool(raw.get("dual_judge", False))
    data["model"] = str(raw.get("dual_judge_model", "")).strip()
    return data


def load_history_window() -> float:
    """群上下文时间窗（秒），来自 data/reply.json 的 history_minutes。

    Returns:
        float: 时间窗秒数，默认 1800（30 分钟）。
    """
    global _ar_chance_cache
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        minutes = float(raw.get("history_minutes", 30))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 1800.0
    minutes = max(1.0, min(240.0, minutes))
    return minutes * 60.0


HISTORY_MIN_COUNT_DEFAULT = 3
HISTORY_FALLBACK_COUNT_DEFAULT = 12


def load_history_fallback() -> tuple[int, int]:
    """时间窗内消息太少时改成按条数补的配置。

    冷场半小时后开新话题，「最近 20 分钟」里可能只有一两句，模型等于没有
    上下文，容易答得牛头不对马嘴。这里允许退回到「最近 N 条」——旧一点
    也比空着强。

    Returns:
        tuple[int, int]: (窗内最少条数, 不足时补到多少条)，默认 (3, 12)。
    """
    min_count = HISTORY_MIN_COUNT_DEFAULT
    count = HISTORY_FALLBACK_COUNT_DEFAULT
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        min_count = int(raw.get("history_min_count", min_count))
        count = int(raw.get("history_fallback_count", count))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    min_count = max(1, min(20, min_count))
    count = max(min_count, min(40, count))
    return min_count, count


def load_reply_budget() -> tuple[int, float]:
    """每群回复预算：(窗口内最大条数, 窗口秒数)。

    Returns:
        tuple[int, float]: (最大条数, 窗口秒数)，默认 (8, 600)。
    """
    try:
        raw = json.loads(REPLY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        limit = int(raw.get("reply_budget", 8))
        window = float(raw.get("reply_budget_minutes", 10)) * 60.0
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 8, 600.0
    return max(1, min(60, limit)), max(60.0, min(3600.0, window))


def load_autoreply_config() -> dict[str, bool]:
    """Read per-group auto-reply switches, cached by file mtime.

    Returns:
        Mapping of group id to enabled flag. Missing groups default to True.
    """
    global _autoreply_cache
    try:
        stat = AUTOREPLY_CONFIG_PATH.stat()
    except OSError:
        return {}
    if _autoreply_cache["data"] is not None and stat.st_mtime == _autoreply_cache["mtime"]:
        return _autoreply_cache["data"]

    try:
        raw = json.loads(AUTOREPLY_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    data = {
        str(gid): bool(conf.get("enabled", True))
        for gid, conf in (raw.get("groups") or {}).items()
        if isinstance(conf, dict)
    }
    _autoreply_cache = {"mtime": stat.st_mtime, "data": data}
    return data


def load_judge_config() -> dict:
    """Load the judge prompt and keyword rules, cached by file mtime.

    Returns:
        A dict with ``prompt``, ``ignore`` and ``force_reply`` keys.
    """
    global _judge_cache
    try:
        stat = JUDGE_CONFIG_PATH.stat()
    except OSError:
        return {"prompt": DEFAULT_JUDGE_PROMPT, "ignore": [], "force_reply": []}

    if _judge_cache["data"] is not None and stat.st_mtime == _judge_cache["mtime"]:
        return _judge_cache["data"]

    try:
        raw = json.loads(JUDGE_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raw = {}

    prompt = str(raw.get("prompt") or DEFAULT_JUDGE_PROMPT)
    if "{message}" not in prompt:
        prompt = DEFAULT_JUDGE_PROMPT
    data = {
        "prompt": prompt,
        "ignore": [str(x).strip() for x in raw.get("ignore", []) if str(x).strip()],
        "force_reply": [
            str(x).strip() for x in raw.get("force_reply", []) if str(x).strip()
        ],
        "force_patterns": [
            str(x).strip()
            for x in raw.get("force_patterns", [])
            if str(x).strip()
        ],
        "summon": [
            str(x).strip() for x in raw.get("summon", []) if str(x).strip()
        ],
    }
    _judge_cache = {"mtime": stat.st_mtime, "data": data}
    return data


def _as_int(value, default: int, low: int, high: int) -> int:
    """Clamp an arbitrary config value into an int range."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _as_float(value, default: float, low: float, high: float) -> float:
    """Clamp an arbitrary config value into a float range."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def load_judge_api_config() -> dict:
    """Load the third-party judge profile (``data/judge_api.json``).

    Kept separate from ``judge.json`` so the dashboard's local-judge editor
    can never wipe the API settings. Cached by file mtime.

    Returns:
        A normalized dict with backend, prompt, rules and budget fields.
    """
    global _judge_api_cache
    defaults = {
        "enable": True,
        "api_base": "https://api.deepseek.com/v1",
        "api_key": "",
        "model": "",
        "prompt": DEFAULT_JUDGE_API_PROMPT,
        "recent_max": 3,
        "recent_chars": 60,
        "include_last_bot": True,
        "max_tokens": 2,
        "temperature": 0.0,
        "budget_gate": True,
        "use_reply_chance": False,
        "reply_chance": 1.0,
        "fallback_chance": 0.3,
        "cache_seconds": 30,
        # 连发抑制：一条在生成/刚发完时，别把后一句也当成新话题再回一遍
        "judge_delay": 2.0,
        "reply_gap": 6,
        "inflight_ttl": 45,
        # 在途硬锁：回复正在生成/分段发送时，@ 它和唤醒前缀也一并挡掉
        "inflight_lock": True,
        "dup_window": 45,
        "dup_ratio": 0.75,
        # 话段聚合：很多人一句话拆成两三句发。等这一口气说完再判一次，
        # 判过/回过的这一段不再送判官（省 token），除非命中强触发规则。
        "burst_enable": True,
        "burst_gap": 15,
        "burst_settle": 3.5,
        "burst_reuse": 45,
        "break_words": [],
        "bot_names": [],
        "break_follow": 30,
        "summon_gap": 4,
        "daily_limit": 50000,
        "used": {"date": "", "tokens": 0},
        "ignore": [],
        "force_reply": [],
        "force_patterns": [],
        "followup_patterns": [],
        "summon": [],
    }
    try:
        stat = JUDGE_API_CONFIG_PATH.stat()
    except OSError:
        return defaults

    if _judge_api_cache["data"] is not None and stat.st_mtime == _judge_api_cache["mtime"]:
        return _judge_api_cache["data"]

    try:
        raw = json.loads(JUDGE_API_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        raw = {}

    prompt = str(raw.get("prompt") or DEFAULT_JUDGE_API_PROMPT)
    if "{message}" not in prompt:
        prompt = DEFAULT_JUDGE_API_PROMPT

    def _words(key: str) -> list[str]:
        return [str(x).strip() for x in raw.get(key, []) if str(x).strip()]

    used = raw.get("used") if isinstance(raw.get("used"), dict) else {}
    data = {
        "enable": bool(raw.get("enable", True)),
        "api_base": str(raw.get("api_base") or defaults["api_base"]).rstrip("/"),
        "api_key": str(raw.get("api_key") or "").strip(),
        "model": str(raw.get("model") or "").strip(),
        "prompt": prompt,
        "recent_max": _as_int(raw.get("recent_max"), 3, 1, 8),
        "recent_chars": _as_int(raw.get("recent_chars"), 60, 20, 200),
        "include_last_bot": bool(raw.get("include_last_bot", True)),
        "max_tokens": _as_int(raw.get("max_tokens"), 2, 1, 8),
        "temperature": _as_float(raw.get("temperature"), 0.0, 0.0, 1.5),
        "budget_gate": bool(raw.get("budget_gate", True)),
        "use_reply_chance": bool(raw.get("use_reply_chance", False)),
        "reply_chance": _as_float(raw.get("reply_chance"), 1.0, 0.0, 1.0),
        "fallback_chance": _as_float(raw.get("fallback_chance"), 0.3, 0.0, 1.0),
        "cache_seconds": _as_int(raw.get("cache_seconds"), 30, 0, 3600),
        "judge_delay": _as_float(raw.get("judge_delay"), 2.0, 0.0, 10.0),
        "reply_gap": _as_int(raw.get("reply_gap"), 6, 0, 600),
        "inflight_ttl": _as_int(raw.get("inflight_ttl"), 45, 10, 600),
        "inflight_lock": bool(raw.get("inflight_lock", True)),
        "dup_window": _as_int(raw.get("dup_window"), 45, 0, 600),
        "dup_ratio": _as_float(raw.get("dup_ratio"), 0.75, 0.0, 1.0),
        "burst_enable": bool(raw.get("burst_enable", True)),
        "burst_gap": _as_int(raw.get("burst_gap"), 15, 0, 120),
        "burst_settle": _as_float(raw.get("burst_settle"), 3.5, 0.0, 10.0),
        "burst_reuse": _as_int(raw.get("burst_reuse"), 45, 0, 600),
        "break_words": _words("break_words"),
        "bot_names": _words("bot_names"),
        "break_follow": _as_int(raw.get("break_follow"), 30, 0, 300),
        "summon_gap": _as_int(raw.get("summon_gap"), 4, 0, 120),
        "daily_limit": _as_int(raw.get("daily_limit"), 50000, 0, 10_000_000),
        "used": {
            "date": str(used.get("date") or ""),
            "tokens": _as_int(used.get("tokens"), 0, 0, 10_000_000_000),
        },
        "ignore": _words("ignore"),
        "force_reply": _words("force_reply"),
        "force_patterns": _words("force_patterns"),
        "followup_patterns": _words("followup_patterns"),
        "summon": _words("summon"),
    }
    _judge_api_cache = {"mtime": stat.st_mtime, "data": data}
    return data


def current_provider_id() -> str:
    """Read the active chat provider id from AstrBot's config.

    Returns:
        Provider id such as ``deepseek`` or ``local-llama``; empty on failure.
    """
    global _provider_cache
    try:
        stat = PROVIDER_CONFIG_PATH.stat()
    except OSError:
        return ""
    if stat.st_mtime == _provider_cache["mtime"]:
        return _provider_cache["id"]
    try:
        cfg = json.loads(PROVIDER_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        pid = str(
            cfg.get("agent_runner", {})
            .get("config", {})
            .get("model", {})
            .get("provider_id", "")
        )
    except (json.JSONDecodeError, OSError, AttributeError):
        pid = ""
    _provider_cache = {"mtime": stat.st_mtime, "id": pid}
    return pid


def is_third_party_mode() -> bool:
    """Whether the chat model currently runs on a third-party provider."""
    return "deepseek" in current_provider_id().lower()


def _record_text(record) -> str:
    """Strip the ``[nickname/time]: `` prefix from a stored group message."""
    return re.sub(r"^\[[^\]]*\]:\s*", "", str(record)).strip()


def _similarity(left: str, right: str) -> float:
    """Character-level similarity of two short messages (0.0 - 1.0).

    Used only to decide whether two consecutive messages are the same thing
    said twice, so punctuation, spaces and emoji are dropped first.
    """
    def _norm(text: str) -> str:
        return re.sub(r"[\s\W_]+", "", str(text or "")).lower()

    a, b = _norm(left), _norm(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


class GroupChatContext:
    def __init__(self, acm: AstrBotConfigManager, context: star.Context) -> None:
        self.acm = acm
        self.context = context
        self._locks: dict[str, asyncio.Lock] = {}
        self.raw_records: dict[str, deque[str]] = defaultdict(deque)
        self._record_ids: dict[str, deque[str]] = defaultdict(deque)
        self._record_times: dict[str, deque[float]] = defaultdict(deque)
        self._reply_times: dict[str, deque[float]] = defaultdict(deque)
        # 第三方判官运行时状态
        self._last_bot: dict[str, str] = {}
        # 连发抑制：在途截止时间、刚回过话的冷却截止时间、上次触发回复的消息
        self._inflight_until: dict[str, float] = {}
        self._cool_until: dict[str, float] = {}
        self._last_trigger: dict[str, tuple[float, str]] = {}
        # 话段聚合：消息到达时间（判断同一口气说完了没）
        self._last_arrival: dict[str, float] = {}
        self._prev_arrival: dict[str, float] = {}
        # 它这次发言的区间（开始, 预计发完），用来判断「骂的是不是它」
        self._last_bot_span: dict[str, tuple[float, float]] = {}
        self._burst: dict[str, dict] = {}
        self._judge_cache_map: dict[tuple[str, str], tuple[float, bool]] = {}
        self._judge_fail = 0
        self._judge_cooldown_until = 0.0
        self._judge_usage = dict(load_judge_api_config()["used"])
        self._judge_usage_dirty = False
        self._judge_last_flush = 0.0

    def _get_lock(self, umo: str) -> asyncio.Lock:
        lock = self._locks.get(umo)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[umo] = lock
        return lock

    def cfg(self, event: AstrMessageEvent):
        cfg = self.context.get_config(umo=event.unified_msg_origin)
        group_context_cfg = cfg["provider_ltm_settings"]
        image_caption_prompt = cfg["provider_settings"]["image_caption_prompt"]
        image_caption_provider_id = group_context_cfg.get("image_caption_provider_id")
        image_caption = group_context_cfg["image_caption"] and bool(
            image_caption_provider_id
        )
        active_reply = group_context_cfg["active_reply"]
        enable_active_reply = active_reply.get("enable", False)
        ar_method = active_reply["method"]
        ar_possibility = active_reply["possibility_reply"]
        ar_prompt = active_reply.get("prompt", "")
        ar_whitelist = active_reply.get("whitelist", [])
        return {
            "group_message_max_cnt": _positive_int(
                group_context_cfg.get(
                    "group_message_max_cnt",
                    DEFAULT_GROUP_MESSAGE_MAX_CNT,
                ),
                DEFAULT_GROUP_MESSAGE_MAX_CNT,
            ),
            "image_caption": image_caption,
            "image_caption_prompt": image_caption_prompt,
            "image_caption_provider_id": image_caption_provider_id,
            "enable_active_reply": enable_active_reply,
            "ar_method": ar_method,
            "ar_possibility": ar_possibility,
            "ar_prompt": ar_prompt,
            "ar_whitelist": ar_whitelist,
        }

    async def get_image_caption(
        self,
        image_url: str,
        image_caption_provider_id: str,
        image_caption_prompt: str,
    ) -> str:
        if not image_caption_provider_id:
            provider = await self.context.get_using_provider_async()
        else:
            provider = self.context.get_provider_by_id(image_caption_provider_id)
            if not provider:
                raise Exception(f"没有找到 ID 为 {image_caption_provider_id} 的提供商")
        if not isinstance(provider, Provider):
            raise Exception(f"提供商类型错误({type(provider)})，无法获取图片描述")
        response = await provider.text_chat(
            prompt=image_caption_prompt,
            session_id=uuid.uuid4().hex,
            image_urls=[image_url],
            persist=False,
        )
        return response.completion_text

    @staticmethod
    def _mark_judge_wake(event: AstrMessageEvent) -> None:
        """标记这次回复是判官触发的主动接话（非召唤词/必答规则/艾特）。

        vision_context 据此收紧图描述注入：判官不看图也没人叫它，主动
        接话时只有当前这条话真的在谈图才需要历史图描述，否则 15 分钟
        前的图描述会被硬塞进一段无关闲聊里。
        """
        try:
            event.set_extra("vision_judge_wake", True)
        except Exception:  # noqa: BLE001 - extra 只是提示信息，失败不影响主流程
            pass

    async def need_active_reply(self, event: AstrMessageEvent) -> bool:
        cfg = self.cfg(event)
        if not cfg["enable_active_reply"]:
            return False
        if event.get_message_type() != MessageType.GROUP_MESSAGE:
            return False
        if event.is_at_or_wake_command:
            return False
        group_id = str(event.get_group_id() or "")
        if load_autoreply_config().get(group_id) is False:
            logger.debug(f"active_reply disabled for group {group_id}")
            return False
        # /群聊 接话关（access 插件 group_flags.json）：判官整体短路，
        # 连召唤词也不放行——接话关就是关，喊名字也不接（@ 走 peer 闸门同规则）
        flags = load_group_flags().get(group_id)
        if flags is not None and flags.get("reply_at") is False:
            logger.info(f"group judge | 接话关({group_id}) | {(event.message_str or '')[:30]}")
            return False
        if cfg["ar_whitelist"] and (
            event.unified_msg_origin not in cfg["ar_whitelist"]
            and (
                event.get_group_id() and event.get_group_id() not in cfg["ar_whitelist"]
            )
        ):
            return False
        # 喊名字 = 明确在叫它，直接接，不经过判官和概率闸
        judge_cfg = load_judge_config()
        api_cfg = load_judge_api_config()
        text = event.message_str or ""
        summon_words = list(judge_cfg.get("summon", []))
        for word in api_cfg.get("summon", []):
            if word not in summon_words:
                summon_words.append(word)
        summon_hit = ""
        for word in summon_words:
            if word and word in text:
                summon_hit = word
                break

        # 第三方模式走独立的一套：规则前置 + 短提示词 + 独立密钥/额度
        # 召唤词交给它处理：跳过静默等待、不吃「刚回过话」的冷却（叫了就该应），
        # 但仍然只允许一条回复在途，避免并发双发
        if is_third_party_mode():
            return await self._need_active_reply_api(event, cfg, api_cfg, summon_hit)

        if summon_hit:
            self._note_reply(event.unified_msg_origin)
            logger.info(f"group judge | 召唤词({summon_hit})直通 | {text[:30]}")
            return True

        match cfg["ar_method"]:
            case "possibility_reply":
                hit = random.random() < cfg["ar_possibility"]
                if hit:
                    self._mark_judge_wake(event)
                return hit
            case "judge":
                if not await self._judge_reply(event, cfg):
                    return False
                over, used = self._over_budget(event.unified_msg_origin)
                if over:
                    logger.info(f"group judge | 超出预算({used} 条)跳过 | {event.message_str[:30]}")
                    return False
                # 判官说接，再按概率收一次频率
                chance = load_reply_chance()
                if chance >= 1.0 or random.random() < chance:
                    self._note_reply(event.unified_msg_origin)
                    self._mark_judge_wake(event)
                    return True
                logger.info(f"group judge | 概率闸拦截 (chance={chance:.2f}) | {event.message_str[:30]}")
                return False
        return False

    async def _need_active_reply_api(
        self, event: AstrMessageEvent, cfg: dict, api_cfg: dict, summon_hit: str = ""
    ) -> bool:
        """Decide whether to chime in, one decision at a time per group.

        同一口气发来的几条消息会各自触发一次判定。如果并发执行，它们都会看到
        「还没有人认领这次回复」而全部放行，最后还是连发。所以整个判定按群串行。

        Args:
            event: Incoming group message.
            cfg: Active-reply config.
            api_cfg: Third-party judge profile.
            summon_hit: Matched wake-word, empty when the message did not summon.

        Returns:
            True when the bot should chime in.
        """
        umo = event.unified_msg_origin
        now = time.time()
        # 每条消息都记一次到达时间：话段聚合靠它判断「这一口气说完了没」。
        # 这个时间戳必须在锁外写，否则后续消息会被锁挡住、永远看不见。
        self._prev_arrival[umo] = self._last_arrival.get(umo, 0.0)
        self._last_arrival[umo] = now
        state = self._burst.get(umo)
        if state and now - state.get("last", 0.0) <= api_cfg["burst_gap"]:
            state["last"] = now

        # 召唤词要快：跳过静默等待，进锁后也只看「是不是真的正在发」
        if summon_hit:
            async with self._get_lock(umo):
                return await self._need_active_reply_api_inner(
                    event, cfg, api_cfg, summon_hit
                )

        # 等这一口气说完。等待期间又来消息就放弃，让最新那条去判——
        # 这样拆成两三句发的内容会被合成一段判一次，既不漏也不重复。
        settle = api_cfg["burst_settle"] if api_cfg.get("burst_enable", True) else 0
        if settle > 0 and (event.message_str or "").strip():
            await asyncio.sleep(settle)
            if self._last_arrival.get(umo, 0.0) != now:
                logger.info(
                    f"group judge | 话段未说完，交给最新一条 "
                    f"| {(event.message_str or '')[:30]}"
                )
                return False

        async with self._get_lock(umo):
            return await self._need_active_reply_api_inner(
                event, cfg, api_cfg, summon_hit
            )

    async def _need_active_reply_api_inner(
        self, event: AstrMessageEvent, cfg: dict, api_cfg: dict, summon_hit: str = ""
    ) -> bool:
        """第三方模式的接话判定：先挡连发，再看规则，最后才花 token。

        一条回复从判定到真正发出去要好几秒，这期间同一口气发来的后续消息
        如果各自都过一遍判定，就会连着发出几条语义差不多的回复。所以按
        「召唤词 → 回复在途 → 刚回过话的冷却 → 条数限制 → 规则层 →
        话段复用（省 token）→ 相似去重 → 模型」的顺序挡，越靠前越省 token。

        冷却和话段复用都不是硬墙：叫它名字、骂到它头上，规则会让它破例接一句。

        Args:
            event: Incoming group message.
            cfg: Active-reply config (probability fallback only).
            api_cfg: Third-party judge profile from ``judge_api.json``.
            summon_hit: Matched wake-word, empty when the message did not summon.

        Returns:
            True when the bot should chime in.
        """
        umo = event.unified_msg_origin
        message = (event.message_str or "").strip()
        if not message:
            return False
        # 指令不是聊天内容：别花判官的 token，也别算进回复预算
        if message[0] in "/／":
            return False

        # 1) 召唤词：不等静默窗口，也不吃「刚回过话」的冷却（叫了就该应），
        #    只挡「回复真的正在发」和「几秒内又叫了一次」
        if summon_hit:
            if self._inflight_for(umo) > 0:
                logger.info(f"group judge | 召唤词但回复在途 | {message[:30]}")
                return False
            prev = self._last_trigger.get(umo)
            if prev and time.time() - prev[0] < api_cfg["summon_gap"]:
                logger.info(f"group judge | 召唤词间隔过密 | {message[:30]}")
                return False
            if self._too_similar(umo, message, api_cfg):
                return False
            logger.info(f"group judge | 召唤词({summon_hit})直通 | {message[:30]}")
            self._mark_trigger(umo, message, api_cfg)
            self._mark_burst(umo, "answered", api_cfg)
            return True

        # 2) 回复正在生成/发送：并发会连发，先挡
        if self._inflight_for(umo) > 0:
            logger.info(f"group judge | 回复在途 | {message[:30]}")
            return False

        # 3) 刚回过话的冷却期：默认不接。叫名字直接放行；带脏话的也放行，
        #    但只是「让判官看一眼」，由它结合上下文判断在骂谁，不直接接
        remain = self._suppressed_for(umo)
        if remain > 0:
            if not self._break_allowed(umo, message, api_cfg, summon_hit):
                logger.info(
                    f"group judge | 连发抑制(剩{remain:.0f}s) | {message[:30]}"
                )
                return False
            if self._hard_break(umo, message, api_cfg, summon_hit):
                logger.info(
                    f"group judge | 点名打破冷却(剩{remain:.0f}s) | {message[:30]}"
                )
            else:
                logger.info(
                    f"group judge | 脏话待判(剩{remain:.0f}s)，交给判官看骂谁 "
                    f"| {message[:30]}"
                )

        # 4) 条数限制前处理：超了就不花 token（开关：budget_gate）
        if api_cfg.get("budget_gate", True):
            over, used = self._over_budget(umo)
            if over:
                logger.info(f"group judge | 条数限制({used})前置拦截 | {message[:30]}")
                return False

        for kw in api_cfg["ignore"]:
            if kw and kw in message:
                logger.info(f"group judge | API 免打扰({kw}) | {message[:40]}")
                return False
        for kw in api_cfg["force_reply"]:
            if kw and kw in message:
                logger.info(f"group judge | API 必答({kw}) | {message[:40]}")
                self._mark_trigger(umo, message, api_cfg)
                return True
        for pattern in api_cfg["force_patterns"]:
            try:
                if re.search(pattern, message):
                    logger.info(f"group judge | API 必答正则({pattern}) | {message[:40]}")
                    self._mark_trigger(umo, message, api_cfg)
                    return True
            except re.error:
                continue
        # 指向 bot 的追问/纠错：0 token 直通（“你不是猫吗怎么汪汪叫”）
        for pattern in api_cfg["followup_patterns"]:
            try:
                if re.search(pattern, message):
                    logger.info(f"group judge | 追问直通({pattern}) | {message[:40]}")
                    self._mark_trigger(umo, message, api_cfg)
                    return True
            except re.error:
                continue
        # 5) 话段复用：这一段已经判过/回过了，就不再送判官（省 token）。
        #    叫它名字直接放行；带脏话的放行给判官，由它判断在骂谁。
        if self._burst_blocked(umo, message, api_cfg):
            return False

        # 6) 过短：按合并后的话段长度判断。很多人把一句话拆成两三句发，
        #    「就是」「然后呢」单独看没意义，单独挡掉就等于不理人。
        merged = self._burst_text(umo, message, api_cfg)
        if len(merged) <= 3:
            logger.info(f"group judge | 过短不接 | {message[:20]}")
            return False

        records = list(self.raw_records.get(umo, []))
        if records and _record_text(records[-1]) == message:
            logger.info(f"group judge | 复读不接 | {message[:20]}")
            return False

        # 7) 相似去重：和刚触发过回复的那句几乎一样，就不再判一次
        if self._too_similar(umo, message, api_cfg):
            return False

        # 关掉第三方判官：不碰 8082，直接规则 + 概率兜底
        if not api_cfg["enable"]:
            logger.info("group judge | 第三方判官已关，走规则+概率")
            if random.random() < api_cfg["fallback_chance"]:
                self._mark_trigger(umo, message, api_cfg)
                self._mark_burst(umo, "answered", api_cfg)
                self._mark_judge_wake(event)
                return True
            return False

        verdict = await self._judge_api(
            umo,
            message,
            records,
            api_cfg,
            insult=self._insult_hit(message, api_cfg),
        )
        if verdict is None:
            # 失败/超限/熔断：概率兜底，不硬中断（也不标记话段，等下次重试）
            if random.random() < api_cfg["fallback_chance"]:
                self._mark_trigger(umo, message, api_cfg)
                self._mark_burst(umo, "answered", api_cfg)
                self._mark_judge_wake(event)
                return True
            return False
        if not verdict:
            # 判官说不接：这一段就别再反复送了，省下后面的 token
            self._mark_burst(umo, "judged", api_cfg)
            return False
        if api_cfg["use_reply_chance"] and random.random() >= api_cfg["reply_chance"]:
            logger.info(
                f"group judge | API 概率闸拦截 "
                f"(chance={api_cfg['reply_chance']:.2f}) | {message[:30]}"
            )
            self._mark_burst(umo, "judged", api_cfg)
            return False
        self._mark_trigger(umo, message, api_cfg)
        self._mark_burst(umo, "answered", api_cfg)
        self._mark_judge_wake(event)
        return True

    async def _judge_api(
        self,
        umo: str,
        message: str,
        records: list,
        api_cfg: dict,
        insult: bool = False,
    ) -> bool | None:
        """Ask the third-party judge model with a minimal prompt.

        Args:
            umo: Unified message origin.
            message: Incoming text.
            records: Recent group records.
            api_cfg: Third-party judge profile.
            insult: The message contains a swear word; ask the judge to work out
                who it is aimed at instead of guessing from rules.

        Returns:
            True/False for the verdict, None when the call failed, was cooling
            down, or hit the daily token cap (caller falls back to probability).
        """
        now = time.time()
        cache_key = (umo, message)
        cached = self._judge_cache_map.get(cache_key)
        if cached and now - cached[0] <= api_cfg["cache_seconds"]:
            logger.info(f"group judge | API 缓存命中 | {message[:30]}")
            return cached[1]
        if now < self._judge_cooldown_until:
            return None

        today = datetime.datetime.now().strftime("%Y%m%d")
        used = dict(self._judge_usage)
        if used.get("date") != today:
            used = {"date": today, "tokens": 0}
            self._judge_usage = used
        limit = api_cfg["daily_limit"]
        if limit and int(used.get("tokens") or 0) >= limit:
            logger.warning(
                f"group judge | API 判官日限额已满({used['tokens']})，走概率兜底"
            )
            return None

        base, api_key, model = self._judge_api_credentials(api_cfg)
        if not api_key:
            logger.warning("group judge | 没有可用的 API 密钥，走概率兜底")
            return None

        recent_lines = []
        for item in records[-api_cfg["recent_max"]:]:
            text = _record_text(item)
            if not text:
                continue
            if len(text) > api_cfg["recent_chars"]:
                text = text[: api_cfg["recent_chars"]] + "…"
            recent_lines.append(text)
        recent_text = "\n".join(recent_lines) or "(暂无更早消息)"
        last_bot = "(还没说过话)"
        if api_cfg["include_last_bot"]:
            last_bot = (self._last_bot.get(umo) or "")[:80] or "(还没说过话)"

        prompt = (
            api_cfg["prompt"]
            .replace("{recent}", recent_text)
            .replace("{last_bot}", last_bot)
            .replace("{message}", message)
        )
        if insult:
            # 规则只能看出「有脏话」，看不出骂的是谁；这一步交给能读上下文的判官
            said = (self._last_bot.get(umo) or "")[:30]
            if said:
                prompt += (
                    "\n\n注意：这句带脏话。先判断它在骂谁——"
                    f"如果是在接你刚才说的「{said}」，或者用「你」指的是你，回 1；"
                    "如果明显在骂群里另一个人、跟你无关，回 0。"
                )
            else:
                prompt += (
                    "\n\n注意：这句带脏话。只有明显在骂你（比如用「你」指向你）"
                    "才回 1；在骂群里其他人、跟你无关回 0。"
                )
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": api_cfg["max_tokens"],
            "temperature": api_cfg["temperature"],
            "thinking": {"type": "disabled"},
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            usage = data.get("usage") or {}
            self._judge_usage_add(int(usage.get("total_tokens") or 0))
            content = (data["choices"][0]["message"].get("content") or "").strip()
            verdict = content.startswith("1")
            self._judge_fail = 0
            if api_cfg["cache_seconds"] > 0:
                self._judge_cache_map[cache_key] = (now, verdict)
                self._trim_judge_cache()
            logger.info(
                f"group judge | API verdict={content[:2] or '?'} "
                f"tokens={usage.get('total_tokens', 0)} | {message[:30]}"
            )
            return verdict
        except Exception as exc:  # noqa: BLE001 - 失败就概率兜底
            self._judge_fail += 1
            if self._judge_fail >= 3:
                self._judge_cooldown_until = now + 300
                self._judge_fail = 0
                logger.warning("group judge | API 连续失败，暂停判官 5 分钟")
            logger.warning(f"group judge | API 判官失败，走概率兜底: {exc}")
            return None

    def _judge_api_credentials(self, api_cfg: dict) -> tuple[str, str, str]:
        """Resolve base/key/model, falling back to the active DeepSeek provider.

        Returns:
            (api_base, api_key, model) tuple; api_key is empty when unresolved.
        """
        base = str(api_cfg["api_base"] or "").rstrip("/")
        api_key = str(api_cfg["api_key"] or "").strip()
        model = str(api_cfg["model"] or "").strip()
        if base and api_key and model:
            return base, api_key, model
        try:
            cfg = json.loads(PROVIDER_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            return base, api_key, model
        sources = {
            str(s.get("id")): s
            for s in cfg.get("provider_sources", [])
            if isinstance(s, dict)
        }
        providers = {
            str(p.get("id")): p for p in cfg.get("provider", []) if isinstance(p, dict)
        }
        provider = providers.get("deepseek") or {}
        source = sources.get(str(provider.get("provider_source_id") or "")) or sources.get(
            "deepseek_source"
        ) or {}
        if not api_key:
            keys = source.get("key") if isinstance(source.get("key"), list) else []
            api_key = str(source.get("api_key") or (keys[0] if keys else "")).strip()
        if not model:
            model = str(provider.get("model") or "deepseek-flash").strip()
        if not base:
            base = str(source.get("api_base") or "https://api.deepseek.com/v1").rstrip("/")
        return base, api_key, model

    def _judge_usage_add(self, tokens: int) -> None:
        """Accumulate judge tokens into its own daily counter."""
        if tokens <= 0:
            return
        today = datetime.datetime.now().strftime("%Y%m%d")
        used = dict(self._judge_usage)
        if used.get("date") != today:
            used = {"date": today, "tokens": 0}
        used["tokens"] = int(used.get("tokens") or 0) + tokens
        self._judge_usage = used
        self._judge_usage_dirty = True
        if time.time() - self._judge_last_flush > 60:
            self._flush_judge_usage()

    def _flush_judge_usage(self) -> None:
        """Write the judge counter back without clobbering other fields."""
        if not self._judge_usage_dirty:
            return
        self._judge_usage_dirty = False
        self._judge_last_flush = time.time()
        try:
            raw = json.loads(JUDGE_API_CONFIG_PATH.read_text(encoding="utf-8-sig"))
            if not isinstance(raw, dict):
                raw = {}
            raw["used"] = dict(self._judge_usage)
            JUDGE_API_CONFIG_PATH.write_text(
                json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            _judge_api_cache["mtime"] = JUDGE_API_CONFIG_PATH.stat().st_mtime
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(f"group judge | 写用量失败: {exc}")

    def _trim_judge_cache(self) -> None:
        """Keep the verdict cache bounded."""
        if len(self._judge_cache_map) <= 200:
            return
        oldest = sorted(self._judge_cache_map.items(), key=lambda item: item[1][0])[:100]
        for key, _ in oldest:
            self._judge_cache_map.pop(key, None)

    def note_bot_reply(self, umo: str, text: str) -> None:
        """模型生成完了：先按「发送耗时上沿」把在途锁顶住。

        分段发送是 AstrBot 自带功能，每段之间都会 sleep，所以「生成完」不等于
        「发完」。这里只是**兜底**：真实发完会由 ``note_message_sent`` 立刻
        收敛，所以上沿取最坏情况（宁可多锁几秒，也不能提前放开）。

        Args:
            umo: Unified message origin.
            text: Full completion text of this reply.
        """
        # 本地模式保持最初行为：这套状态一个都不碰
        if not is_third_party_mode():
            return
        text = (text or "").strip()
        if not text:
            return
        now = time.time()
        est = _estimate_send_seconds(text, upper=True)
        self._last_bot[umo] = text[:200]
        # 记发言区间（开始 ~ 预计发完），判断「骂的是不是它」要用
        self._last_bot_span[umo] = (now, now + est)
        gap = load_judge_api_config()["reply_gap"]
        # 发送期间算「在途」（召唤词也要让路），发完之后才开始 reply_gap 冷却。
        # 真正的发完时刻由 after_message_sent 送进来（note_message_sent）。
        self._inflight_until[umo] = now + est
        self._cool_until[umo] = now + est + max(0, gap)
        logger.info(
            f"group judge | 发送耗时上沿 {est:.1f}s，等真实发完信号收敛"
        )

    def note_message_sent(self, umo: str, owned: bool = False) -> None:
        """消息真的发完了（``after_message_sent``）：立刻释放在途，冷却从此起算。

        这是「正在回复时完全锁死」的收尾：只要 ``after_message_sent`` 到了，
        说明所有分段都发完（它是分段循环与 sleep 之后才触发的），不需要再靠
        估算猜。

        Args:
            umo: Unified message origin.
            owned: 这条发送是否由本插件的接话/唤醒判定引起。防止别的插件
                推送消息时，把我们的在途锁提前放掉。
        """
        if not is_third_party_mode():
            return
        now = time.time()
        if self._inflight_until.get(umo, 0.0) <= now:
            # 没有在途：别顺手给群加冷却（别的插件发消息也会触发这个钩子）
            return
        if not owned:
            logger.debug(f"group judge | 非本插件触发的发送完成，保留在途锁 | {umo}")
            return
        gap = load_judge_api_config()["reply_gap"]
        self._inflight_until[umo] = 0.0
        self._cool_until[umo] = now + max(0, gap)
        span = self._last_bot_span.get(umo)
        if span:
            # 把「预计发完」收敛成真实发完，判断「骂的是不是它」才准
            self._last_bot_span[umo] = (span[0], now)
        logger.info(f"group judge | 发送完成，冷却从此刻起算 {max(0, gap)}s")

    def _inflight_for(self, umo: str) -> float:
        """Seconds until the in-flight reply slot frees up (strictly "sending now")."""
        return max(0.0, self._inflight_until.get(umo, 0.0) - time.time())

    def _suppressed_for(self, umo: str) -> float:
        """还有多少秒处于「回复在途 / 刚回过话」的抑制期。

        Args:
            umo: Unified message origin of the group.

        Returns:
            Remaining seconds; 0 when the bot may reply again.
        """
        now = time.time()
        return max(
            0.0,
            self._inflight_until.get(umo, 0.0) - now,
            self._cool_until.get(umo, 0.0) - now,
        )

    def _mark_trigger(self, umo: str, message: str, api_cfg: dict) -> None:
        """Reserve the slot: one reply per burst, and remember what triggered it."""
        now = time.time()
        self._note_reply(umo)
        self._inflight_until[umo] = now + api_cfg["inflight_ttl"]
        self._cool_until.pop(umo, None)
        self._last_trigger[umo] = (now, message[:200])

    def _mark_burst(self, umo: str, why: str, api_cfg: dict) -> None:
        """Mark this burst as already judged/answered so it stops costing tokens."""
        now = time.time()
        self._burst[umo] = {
            "last": now,
            "until": now + api_cfg["burst_reuse"],
            "why": why,
        }

    def _burst_blocked(self, umo: str, message: str, api_cfg: dict) -> bool:
        """同一话段已经判过/回过，就别再送判官（省 token）；强触发可打破。

        Args:
            umo: Unified message origin.
            message: Incoming text.
            api_cfg: Third-party judge profile.

        Returns:
            True when this message should be skipped without calling the judge.
        """
        state = self._burst.get(umo)
        if not state or not api_cfg.get("burst_enable", True):
            return False
        now = time.time()
        if now >= float(state.get("until") or 0):
            self._burst.pop(umo, None)
            return False
        if now - float(state.get("last") or 0) > api_cfg["burst_gap"]:
            # 中间冷场超过 burst_gap，算新的一段
            self._burst.pop(umo, None)
            return False
        # 省 token 不能省到「骂它也不吭声」：点名直接放行，脏话放行给判官
        if self._break_allowed(umo, message, api_cfg):
            reason = (
                "点名"
                if self._hard_break(umo, message, api_cfg)
                else "脏话待判"
            )
            logger.info(f"group judge | 话段内{reason}，打破复用 | {message[:30]}")
            self._burst.pop(umo, None)
            return False
        logger.info(
            f"group judge | 同话段已{state.get('why') or '判过'}，不再送判官 "
            f"| {message[:30]}"
        )
        return True

    def _burst_text(self, umo: str, message: str, api_cfg: dict) -> str:
        """把这一口气里的几句话拼起来，用于「是不是太短」的判断。"""
        cutoff = time.time() - max(1, api_cfg["burst_gap"])
        records = list(self.raw_records.get(umo, ()))
        times = list(self._record_times.get(umo, ()))
        parts = [message]
        for text, when in zip(reversed(records), reversed(times)):
            if when < cutoff:
                break
            stripped = _record_text(text)
            if stripped:
                parts.append(stripped)
            if len(parts) >= 6:
                break
        return "，".join(reversed(parts))

    def _bot_spoke_last(self, umo: str) -> bool:
        """上一条群消息是不是接着它这次发言说的。

        用「发言区间」判断，而不是「最后一次发言时间戳」：它一句话要分几段
        发出去，中间隔好几秒，只记一个时间点会漏掉「发送期间插话」的情况。

        Args:
            umo: Unified message origin.

        Returns:
            True when the previous group message fell inside (or just after)
            the bot's latest utterance window.
        """
        span = self._last_bot_span.get(umo)
        if not span:
            return False
        start, end = span
        prev = self._prev_arrival.get(umo, 0.0)
        return start - 1.5 <= prev <= end + 1.5

    def _insult_hit(self, message: str, api_cfg: dict) -> bool:
        """这句里有没有骂人的词（命中不代表骂的是它）。"""
        return any(w and w in message for w in api_cfg["break_words"])

    def _hard_break(
        self, umo: str, message: str, api_cfg: dict, summon_hit: str = ""
    ) -> bool:
        """0 token 就能确定是冲着它来的：召唤词 / 叫它的名字。"""
        if summon_hit:
            return True
        return any(n and n in message for n in api_cfg["bot_names"])

    def _break_allowed(
        self, umo: str, message: str, api_cfg: dict, summon_hit: str = ""
    ) -> bool:
        """冷却期/话段复用期间，这句值不值得再让判官看一眼。

        注意返回值不等于「直接回」：叫名字是直接回，骂人的话只是**放行给判官**
        去判断在骂谁——它能看到上下文和「你刚才说了什么」，规则看不到。

        Args:
            umo: Unified message origin.
            message: Incoming text.
            api_cfg: Third-party judge profile.
            summon_hit: Matched wake-word, empty when none.

        Returns:
            True when the message should bypass burst suppression.
        """
        if self._hard_break(umo, message, api_cfg, summon_hit):
            return True
        return self._insult_hit(message, api_cfg)

    def _too_similar(self, umo: str, message: str, api_cfg: dict) -> bool:
        """Whether this message is a near-repeat of the one that just got a reply.

        Args:
            umo: Unified message origin of the group.
            message: Incoming text.
            api_cfg: Third-party judge profile.

        Returns:
            True when it should be skipped instead of answered again.
        """
        window = api_cfg["dup_window"]
        ratio = api_cfg["dup_ratio"]
        if window <= 0 or ratio <= 0:
            return False
        prev = self._last_trigger.get(umo)
        if not prev:
            return False
        when, prev_text = prev
        if time.time() - when > window:
            return False
        score = _similarity(prev_text, message)
        if score < ratio:
            return False
        logger.info(
            f"group judge | 与上一条触发高度相似({score:.2f})不重复接 | {message[:30]}"
        )
        return True

    def _note_reply(self, umo: str) -> None:
        """记一次回复（@、召唤词、随机插话都算）。"""
        self._reply_times[umo].append(time.time())

    def _over_budget(self, umo: str) -> tuple[bool, int]:
        """当前窗口内回复数是否已超预算。

        Returns:
            tuple[bool, int]: (是否超预算, 窗口内条数)。
        """
        limit, window = load_reply_budget()
        cutoff = time.time() - window
        times = self._reply_times[umo]
        while times and times[0] < cutoff:
            times.popleft()
        return len(times) >= limit, len(times)


    async def _judge_with_main(self, prompt: str, model: str) -> bool | None:
        """用主模型（9B）复核一次判定。

        Args:
            prompt: 判官提示词。
            model: 主模型名。

        Returns:
            bool | None: True=同意回复，False=否决，None=调用失败（视为同意）。
        """
        if not model:
            return None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    MAIN_JUDGE_URL,
                    headers={"Authorization": f"Bearer {MAIN_JUDGE_KEY}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4,
                        "temperature": 0.2,
                        "grammar": 'root ::= "0" | "1"',
                        "chat_template_kwargs": {"enable_thinking": False},
                    },
                )
                resp.raise_for_status()
                verdict = resp.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"group judge | 9B 复核 verdict={verdict[:4]}")
            return verdict.startswith("1")
        except Exception as exc:  # noqa: BLE001 - 失败就放行
            logger.warning(f"group judge | 9B 复核失败，按同意处理: {exc}")
            return None

    async def _judge_reply(self, event: AstrMessageEvent, cfg: dict) -> bool:
        """Ask the tiny local judge model whether this group message deserves a reply.

        Rules from ``data/judge.json`` run first: a message matching an ignore
        keyword is dropped immediately, one matching a force keyword is always
        answered. Otherwise the 1.5B model decides.

        Args:
            event: The incoming group message event.
            cfg: Active-reply configuration, used for the probability fallback.

        Returns:
            True when the bot should chime in on its own.
        """
        import httpx

        umo = event.unified_msg_origin
        message = (event.message_str or "").strip()
        if not message:
            return False

        judge_cfg = load_judge_config()
        for kw in judge_cfg["ignore"]:
            if kw and kw in message:
                logger.info(f"group judge | 命中免打扰规则({kw}) | {message[:40]}")
                return False
        for kw in judge_cfg["force_reply"]:
            if kw and kw in message:
                logger.info(f"group judge | 命中必答规则({kw}) | {message[:40]}")
                return True

        # 正则规则优先：小模型判断不稳定，确定性的情况直接定
        for pattern in judge_cfg["force_patterns"]:
            try:
                if re.search(pattern, message):
                    logger.info(f"group judge | 命中必答正则({pattern}) | {message[:40]}")
                    return True
            except re.error:
                continue
        if len(message) <= 3:
            logger.info(f"group judge | 过短不接 | {message[:20]}")
            return False

        recent = list(self.raw_records.get(umo, []))[-8:]
        context = "\n".join(str(r) for r in recent) or "(暂无更早消息)"
        prompt = judge_cfg["prompt"].replace("{recent}", context).replace(
            "{message}", message
        )
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.post(
                    "http://127.0.0.1:8082/v1/chat/completions",
                    headers={"Authorization": "Bearer sk-judge-local"},
                    json={
                        "model": "Qwen3-1.7B",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4,
                        "temperature": 0.5,
                        "grammar": 'root ::= "0" | "1"',
                        "chat_template_kwargs": {"enable_thinking": False},
                    },
                )
                resp.raise_for_status()
                verdict = resp.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"group judge | verdict={verdict[:6]} | {message[:40]}")
            if not verdict.startswith("1"):
                return False
            dual = load_dual_judge()
            if dual["enable"]:
                second = await self._judge_with_main(prompt, dual["model"])
                if second is False:
                    logger.info(f"group judge | 9B 否决: {message[:30]}")
                    return False
            return True
        except Exception as exc:  # noqa: BLE001 - fall back to probability
            logger.warning(f"group judge unavailable, fallback to probability: {exc}")
            return random.random() < cfg["ar_possibility"]

    async def remove_session(self, event: AstrMessageEvent) -> int:
        umo = event.unified_msg_origin
        lock = self._get_lock(umo)
        async with lock:
            cnt = len(self.raw_records.get(umo, deque()))
            self.raw_records.pop(umo, None)
            self._record_ids.pop(umo, None)
            self._record_times.pop(umo, None)
            # 连发抑制/话段状态一并清掉，别让 /reset 后还带着旧冷却
            for store in (
                self._burst,
                self._last_arrival,
                self._prev_arrival,
                self._last_bot_span,
                self._inflight_until,
                self._cool_until,
                self._last_trigger,
                self._last_bot,
            ):
                store.pop(umo, None)
        self._locks.pop(umo, None)
        return cnt

    async def handle_message(self, event: AstrMessageEvent) -> None:
        if event.get_message_type() != MessageType.GROUP_MESSAGE:
            return

        umo = event.unified_msg_origin
        cfg = self.cfg(event)
        # @ 它的消息一定会回，也要计入预算
        if event.is_at_or_wake_command:
            self._note_reply(umo)
        final_message = await self._format_message(event, cfg)

        async with self._get_lock(umo):
            records = self.raw_records[umo]
            record_ids = self._record_ids[umo]
            record_id = uuid.uuid4().hex
            records.append(final_message)
            record_ids.append(record_id)
            times = self._record_times[umo]
            times.append(time.time())
            _trim_left(records, cfg["group_message_max_cnt"], record_ids)
            while len(times) > cfg["group_message_max_cnt"]:
                times.popleft()
            event.set_extra("_group_context_record_id", record_id)
            event.set_extra("_group_context_raw_idx", len(records) - 1)

        logger.debug(f"group_chat_context | {umo} | {final_message}")

    async def on_req_llm(self, event: AstrMessageEvent, req: ProviderRequest) -> None:
        umo = event.unified_msg_origin
        # 在途硬锁：正在回复（生成中或分段发送中）时，@ 它 / 唤醒前缀也不放行。
        #
        # 为什么必须在这里挡：``need_active_reply`` 第一句就是
        # ``if event.is_at_or_wake_command: return False``，@ 走的是 AstrBot
        # 内置回复通道，压根不经过那套判定，所以只靠判官挡不住「回复到一半
        # 又被 @ 一次」的双发。
        #
        # 这个钩子停掉事件，pipeline 会直接放弃本次 LLM 调用（见
        # ``process_stage`` 的 ``if await call_event_hook(...): return``）。
        if (
            event.is_at_or_wake_command
            and event.get_message_type() == MessageType.GROUP_MESSAGE
            and is_third_party_mode()
        ):
            api_cfg = load_judge_api_config()
            # 指令优先：@ 它 + /reset 这类明确指令不该被聊天锁吞掉
            is_command = bool(event.get_extra("handlers_parsed_params"))
            if api_cfg.get("inflight_lock", True) and not is_command:
                # 同一条消息可能多轮进这里（工具调用循环），只处理第一轮
                if not event.get_extra("_judge_inflight_owned"):
                    remain = self._inflight_for(umo)
                    if remain > 0:
                        logger.info(
                            f"group judge | 在途硬锁，@/唤醒被挡(剩{remain:.1f}s) "
                            f"| {(event.message_str or '')[:30]}"
                        )
                        event.stop_event()
                        return
                    # @ 的回复本身也要占住在途：否则它分段发送的这几秒里，
                    # 别人再喊它，判官会当成新话又回一条。
                    # 预算已由 handle_message 记过，这里不再重复计数。
                    now = time.time()
                    self._inflight_until[umo] = now + api_cfg["inflight_ttl"]
                    self._last_trigger[umo] = (now, (event.message_str or "")[:200])
                    event.set_extra("_judge_inflight_owned", True)
                    logger.info("group judge | 唤醒/点名已占在途锁")

        record_id = event.get_extra("_group_context_record_id", None)
        prompt_idx = event.get_extra("_group_context_raw_idx", -1)
        if not isinstance(record_id, str) and (
            not isinstance(prompt_idx, int) or prompt_idx < 0
        ):
            return

        async with self._get_lock(umo):
            records = self.raw_records.get(umo)
            if not records:
                return

            raw_list = list(records)
            id_list = list(self._record_ids.get(umo, deque()))
            if isinstance(record_id, str) and record_id in id_list:
                prompt_idx = id_list.index(record_id)

            if prompt_idx >= len(raw_list):
                return

            times = list(self._record_times.get(umo, deque()))
            times_to_inject = times[:prompt_idx]
            records_to_inject = raw_list[:prompt_idx]
            remaining = raw_list[prompt_idx + 1 :]
            remaining_ids = id_list[prompt_idx + 1 :] if id_list else []
            remaining_times = times[prompt_idx + 1 :]
            records.clear()
            records.extend(remaining)
            if id_list:
                record_ids = self._record_ids[umo]
                record_ids.clear()
                record_ids.extend(remaining_ids)
            time_deque = self._record_times[umo]
            time_deque.clear()
            time_deque.extend(remaining_times)

            # 只注入时间窗内的消息，太老的直接丢
            window = load_history_window()
            cutoff = time.time() - window
            kept = [
                rec
                for rec, ts in zip(records_to_inject, times_to_inject, strict=False)
                if ts >= cutoff
            ]
            # 窗内太空就按条数兜底：冷场后开新话题时，模型至少知道刚才在聊什么
            min_count, fallback_count = load_history_fallback()
            if len(kept) < min_count < len(records_to_inject):
                fallback = records_to_inject[-fallback_count:]
                logger.info(
                    f"group history window: {len(kept)} msg(s) in "
                    f"{int(window/60)}min (< {min_count}), "
                    f"fallback to last {len(fallback)}/{fallback_count}"
                )
                records_to_inject = fallback
            else:
                if len(kept) != len(records_to_inject):
                    logger.info(
                        f"group history window: kept {len(kept)}/"
                        f"{len(records_to_inject)} (window {int(window/60)}min)"
                    )
                records_to_inject = kept

        if records_to_inject:
            req.extra_user_content_parts.append(
                TextPart(text=_format_group_history_block(records_to_inject))
            )

    async def _format_message(self, event: AstrMessageEvent, cfg: dict) -> str:
        datetime_str = datetime.datetime.now().strftime("%H:%M:%S")
        parts = [f"[{event.message_obj.sender.nickname}/{datetime_str}]: "]

        for comp in event.get_messages():
            if isinstance(comp, Plain):
                parts.append(f" {comp.text}")
            elif isinstance(comp, Image):
                if cfg["image_caption"]:
                    try:
                        url = comp.url if comp.url else comp.file
                        if not url:
                            raise Exception("图片 URL 为空")
                        caption = await self.get_image_caption(
                            url,
                            cfg["image_caption_provider_id"],
                            cfg["image_caption_prompt"],
                        )
                        parts.append(f" [Image: {caption}]")
                    except Exception as e:
                        logger.error(f"获取图片描述失败: {e}")
                else:
                    parts.append(" [Image]")
            elif isinstance(comp, Json):
                card_data = comp.data
                if isinstance(card_data, dict) and isinstance(
                    card_data.get("data"), str
                ):
                    try:
                        nested_data = json.loads(card_data["data"])
                        if isinstance(nested_data, dict):
                            card_data = nested_data
                    except json.JSONDecodeError:
                        pass

                detail = {}
                if isinstance(card_data, dict):
                    meta = card_data.get("meta")
                    if isinstance(meta, dict):
                        candidate = meta.get("detail_1") or meta.get("news")
                        if isinstance(candidate, dict):
                            detail = candidate

                fields = []
                for label, value in (
                    ("Title", detail.get("title")),
                    ("Description", detail.get("desc")),
                    ("URL", detail.get("qqdocurl") or detail.get("jumpUrl")),
                ):
                    if isinstance(value, str) and value.strip():
                        normalized = " ".join(value.split())
                        fields.append(f"{label}: {_truncate_reply_text(normalized)}")
                suffix = f": {'; '.join(fields)}" if fields else ""
                parts.append(f" [Shared Card{suffix}]")
            elif isinstance(comp, At):
                is_at_self = str(comp.qq) in (
                    event.get_self_id(),
                    "all",
                )
                if is_at_self:
                    parts.insert(1, "⚠️[DIRECTED AT YOU] ")
                parts.append(f" [At: {comp.name}]")
            elif isinstance(comp, Reply):
                if comp.message_str:
                    parts.append(
                        f" [Quote({comp.sender_nickname}: {_truncate_reply_text(comp.message_str)})]"
                    )
                elif comp.chain:
                    chain_desc = _describe_chain(comp.chain)
                    parts.append(f" [Quote({comp.sender_nickname}: {chain_desc})]")
                else:
                    parts.append(" [Quote]")

        return "".join(parts)


_MAX_REPLY_TEXT_LENGTH = 200


def _describe_chain(chain: list) -> str:
    """Summarize message chain content for quoted reply display."""
    desc = []
    for c in chain:
        if isinstance(c, Plain) and getattr(c, "text", None):
            desc.append(c.text)
        elif isinstance(c, Image):
            desc.append("[Image]")
        elif isinstance(c, At):
            name = getattr(c, "name", "") or getattr(c, "qq", "")
            desc.append(f"[At: {name}]")
        elif isinstance(c, Record):
            desc.append("[Voice]")
        elif isinstance(c, Video):
            desc.append("[Video]")
        elif isinstance(c, File):
            desc.append(f"[File: {getattr(c, 'name', '') or ''}]")
        elif isinstance(c, Forward):
            desc.append("[Forward]")
        elif isinstance(c, AtAll):
            desc.append("[At: All]")
        elif isinstance(c, Face):
            desc.append(f"[Sticker: {getattr(c, 'id', '')}]")
        elif isinstance(c, Reply):
            desc.append("[Quote]")
        else:
            desc.append(f"[{c.__class__.__name__}]")
    return "".join(desc) or "[Unknown]"


def _truncate_reply_text(text: str) -> str:
    """Truncate overly long quoted reply text."""
    if len(text) <= _MAX_REPLY_TEXT_LENGTH:
        return text
    return text[:_MAX_REPLY_TEXT_LENGTH] + "..."


def _positive_int(value, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _trim_left(
    records: deque[str],
    max_records: int,
    record_ids: deque[str] | None = None,
) -> None:
    while len(records) > max_records:
        records.popleft()
        if record_ids:
            record_ids.popleft()


def _format_group_history_block(records: list[str]) -> str:
    return GROUP_HISTORY_HEADER + "\n".join(records) + GROUP_HISTORY_FOOTER
