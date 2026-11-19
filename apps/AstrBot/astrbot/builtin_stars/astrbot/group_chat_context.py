import asyncio
import datetime
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

# 按群的自动接话开关，缺省等于全开
MAIN_JUDGE_URL = "http://127.0.0.1:8080/v1/chat/completions"
MAIN_JUDGE_KEY = "sk-llm-7d41c9e2"

AUTOREPLY_CONFIG_PATH = Path(r"D:\QQNTBOT\data\autoreply.json")
_autoreply_cache: dict = {"mtime": 0.0, "data": None}



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


class GroupChatContext:
    def __init__(self, acm: AstrBotConfigManager, context: star.Context) -> None:
        self.acm = acm
        self.context = context
        self._locks: dict[str, asyncio.Lock] = {}
        self.raw_records: dict[str, deque[str]] = defaultdict(deque)
        self._record_ids: dict[str, deque[str]] = defaultdict(deque)
        self._record_times: dict[str, deque[float]] = defaultdict(deque)
        self._reply_times: dict[str, deque[float]] = defaultdict(deque)

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
        if cfg["ar_whitelist"] and (
            event.unified_msg_origin not in cfg["ar_whitelist"]
            and (
                event.get_group_id() and event.get_group_id() not in cfg["ar_whitelist"]
            )
        ):
            return False
        # 喊名字 = 明确在叫它，直接接，不经过判官和概率闸
        judge_cfg = load_judge_config()
        text = event.message_str or ""
        for word in judge_cfg.get("summon", []):
            if word and word in text:
                self._note_reply(event.unified_msg_origin)
                logger.info(f"group judge | 召唤词({word})直通 | {text[:30]}")
                return True

        match cfg["ar_method"]:
            case "possibility_reply":
                return random.random() < cfg["ar_possibility"]
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
                    return True
                logger.info(f"group judge | 概率闸拦截 (chance={chance:.2f}) | {event.message_str[:30]}")
                return False
        return False


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
            if len(kept) != len(records_to_inject):
                logger.info(
                    f"group history window: kept {len(kept)}/{len(records_to_inject)} "
                    f"(window {int(window/60)}min)"
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
