import time
from collections.abc import AsyncGenerator

from astrbot.api.message_components import (
    File,
    Image,
    Plain,
    Record,
)
from astrbot.core import logger
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.platform.message_type import MessageType

from ..context import PipelineContext
from ..stage import Stage, register_stage

# 未授权私聊的自动回复（同一发送者 5 分钟内只回一次，避免刷屏）
_UNAUTHORIZED_NOTICE = "未授权：这个号只给我的主人用，不接外客"
_NOTICE_COOLDOWN_SECONDS = 300
_last_notice_at: dict[str, float] = {}


def _has_real_content(event: AstrMessageEvent) -> bool:
    """Whether the event carries deliberate user content.

    QQ 会把聊天精灵引导、在线状态等系统事件转成「空文本」的私聊消息
    事件（一秒好几条），戳一戳和合并转发也没有文字。这些不该回
    「未授权」骚扰对方——只有真的说了话/发了图/发了语音文件才算数。

    Args:
        event: The incoming friend-message event.

    Returns:
        True when at least one component is a Plain with text, an Image,
        a voice Record or a File.
    """
    for comp in event.get_messages():
        if isinstance(comp, Plain) and (comp.text or "").strip():
            return True
        if isinstance(comp, (Image, Record, File)):
            return True
    return False


@register_stage
class WhitelistCheckStage(Stage):
    """检查是否在群聊/私聊白名单"""

    async def initialize(self, ctx: PipelineContext) -> None:
        # 保存配置引用：白名单/开关由 /私聊 指令在线改，这里实时读才即时生效
        self._cfg = ctx.astrbot_config
        self.enable_whitelist_check = self._cfg["platform_settings"][
            "enable_id_white_list"
        ]
        self.whitelist = self._cfg["platform_settings"]["id_whitelist"]
        self.whitelist = [
            str(i).strip() for i in self.whitelist if str(i).strip() != ""
        ]
        self.wl_ignore_admin_on_group = self._cfg["platform_settings"][
            "wl_ignore_admin_on_group"
        ]
        self.wl_ignore_admin_on_friend = self._cfg["platform_settings"][
            "wl_ignore_admin_on_friend"
        ]
        self.wl_log = self._cfg["platform_settings"]["id_whitelist_log"]

    async def process(
        self,
        event: AstrMessageEvent,
    ) -> None | AsyncGenerator[None, None]:
        # /私聊 指令会在线改白名单和开关，每次都取最新值
        ps = self._cfg["platform_settings"]
        self.enable_whitelist_check = bool(ps["enable_id_white_list"])
        self.whitelist = [
            str(i).strip()
            for i in ps["id_whitelist"]
            if str(i).strip() != ""
        ]
        self.wl_ignore_admin_on_group = ps["wl_ignore_admin_on_group"]
        self.wl_ignore_admin_on_friend = ps["wl_ignore_admin_on_friend"]
        if not self.enable_whitelist_check:
            # 白名单检查未启用
            return

        if len(self.whitelist) == 0:
            # 白名单为空，不检查
            return

        if event.get_platform_name() == "webchat":
            # WebChat 豁免
            return

        # 检查是否在白名单
        if self.wl_ignore_admin_on_group:
            if (
                event.role == "admin"
                and event.get_message_type() == MessageType.GROUP_MESSAGE
            ):
                return
        if self.wl_ignore_admin_on_friend:
            if (
                event.role == "admin"
                and event.get_message_type() == MessageType.FRIEND_MESSAGE
            ):
                return
        if (
            event.unified_msg_origin not in self.whitelist
            and str(event.get_group_id()).strip() not in self.whitelist
        ):
            if self.wl_log:
                logger.info(
                    f"Session ID {event.unified_msg_origin} is not in the session "
                    "allowlist, so event propagation was stopped. Add this session "
                    "ID in WebUI: Config -> Access Control -> Whitelist -> "
                    "Whitelist ID List, using the profile assigned to this bot.",
                )
            if (
                event.get_message_type() == MessageType.FRIEND_MESSAGE
                and _has_real_content(event)
            ):
                sender = str(event.get_sender_id())
                now = time.time()
                if now - _last_notice_at.get(sender, 0.0) > _NOTICE_COOLDOWN_SECONDS:
                    _last_notice_at[sender] = now
                    try:
                        await event.send(MessageChain().message(_UNAUTHORIZED_NOTICE))
                    except Exception as exc:  # noqa: BLE001 - notice is best effort
                        logger.warning(f"Failed to send unauthorized notice: {exc}")
            event.stop_event()
