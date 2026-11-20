from __future__ import annotations

# 聊天内权限管理：/私聊（白名单）与 /管理员（admins_id）。
#
# 权限分组（两级）：
#   2 = 超级管理员 —— plugin 配置 super_admins（默认 1154487120），可做一切
#   1 = 管理员     —— AstrBot admins_id，只能管 /私聊（白名单）
#   0 = 其他人     —— 只能看帮助和列表
#
# 白名单条目用 AstrBot 原生格式：私聊 = qq:FriendMessage:<qq>，群号原样存。
# 改动直接原地修改 self.context.astrbot_config 里的同一个 list/bool，
# whitelist_check 阶段（已改为实时读）立刻生效，save_config 落盘。

from astrbot.api import logger, star
from astrbot.api.event import AstrMessageEvent, filter

PRIV_HELP = (
    "私聊权限指令（管理员可用）：\n"
    "/私聊 列表 —— 看当前白名单\n"
    "/私聊 允许 <QQ号> —— 允许对方私聊我\n"
    "/私聊 拒绝 <QQ号> —— 取消对方私聊权限\n"
    "/私聊 检查开 / 检查关 —— 开关白名单检查\n"
    "（管理员本人本来就能私聊我）"
)

ADMIN_HELP = (
    "管理员指令（仅最高管理员可用）：\n"
    "/管理员 列表 —— 看管理员名单\n"
    "/管理员 添加 <QQ号> —— 提升为管理员\n"
    "/管理员 移除 <QQ号> —— 撤掉管理员\n"
    "/管理员 <QQ号> —— 等价于 添加\n"
    "最高管理员名单在 WebUI 插件配置里改"
)


def _norm_qq(qq: str) -> str:
    """Strip a QQ number argument down to digits."""
    return str(qq or "").strip()


class MyPlugin(star.Star):
    def __init__(self, context: star.Context) -> None:
        super().__init__(context)

    # ---------- 权限分组 ----------

    def _super_admins(self) -> list[str]:
        try:
            return [str(x) for x in (self.config or {}).get("super_admins", [])]
        except Exception:  # noqa: BLE001 - 配置坏了按空处理
            return []

    def _admins(self) -> list[str]:
        try:
            return [str(x) for x in self.context.astrbot_config.get("admins_id", [])]
        except Exception:  # noqa: BLE001
            return []

    def _level(self, event: AstrMessageEvent) -> int:
        """2=超级管理员 1=管理员 0=普通用户。"""
        uid = str(event.get_sender_id() or "")
        if uid and uid in self._super_admins():
            return 2
        if uid and uid in self._admins():
            return 1
        if getattr(event, "role", "") == "admin":
            return 1
        return 0

    # ---------- /私聊 ----------

    @filter.command("私聊")
    async def private_chat(
        self, event: AstrMessageEvent, action: str = "", target: str = ""
    ) -> None:
        """Manage the private-chat whitelist."""
        level = self._level(event)
        action = (action or "").strip()
        target = _norm_qq(target)

        if not action or action in ("帮助", "help"):
            yield event.plain_result(PRIV_HELP)
            return
        if action == "列表":
            yield event.plain_result(self._wl_text())
            return
        if level < 1:
            yield event.plain_result("这个指令只有管理员能用喵。")
            return

        cfg = self.context.astrbot_config
        wl: list = cfg["platform_settings"]["id_whitelist"]

        if action == "允许":
            if not target.isdigit():
                yield event.plain_result("用法：/私聊 允许 <QQ号>")
                return
            entry = f"qq:FriendMessage:{target}"
            if entry in wl or target in wl:
                yield event.plain_result(f"{target} 本来就在白名单里。")
                return
            wl.append(entry)
            cfg.save_config()
            logger.info(f"[access] whitelist + {entry} (by {event.get_sender_id()})")
            yield event.plain_result(f"好了，{target} 现在可以私聊我了。")
            return

        if action == "拒绝":
            if not target.isdigit():
                yield event.plain_result("用法：/私聊 拒绝 <QQ号>")
                return
            entry = f"qq:FriendMessage:{target}"
            removed = [x for x in (entry, target) if x in wl]
            if not removed:
                yield event.plain_result(f"白名单里本来就没有 {target}。")
                return
            for x in removed:
                wl.remove(x)
            cfg.save_config()
            logger.info(f"[access] whitelist - {target} (by {event.get_sender_id()})")
            yield event.plain_result(f"行，{target} 的私聊权限收回了。")
            return

        if action in ("检查开", "检查关", "开", "关"):
            enable = action in ("检查开", "开")
            old = bool(cfg["platform_settings"].get("enable_id_white_list"))
            if old == enable:
                yield event.plain_result(
                    f"白名单检查本来就是{'开着' if enable else '关着'}的。"
                )
                return
            cfg["platform_settings"]["enable_id_white_list"] = enable
            cfg.save_config()
            logger.info(f"[access] whitelist check -> {enable} (by {event.get_sender_id()})")
            yield event.plain_result(
                ("白名单检查已开启，不在名单里的私聊会被拦。" if enable
                 else "白名单检查已关闭，现在谁都能私聊我。")
            )
            return

        yield event.plain_result(PRIV_HELP)

    def _wl_text(self) -> str:
        try:
            wl = [str(x) for x in self.context.astrbot_config["platform_settings"]["id_whitelist"]]
        except Exception:  # noqa: BLE001
            return "白名单是空的。"
        if not wl:
            return "白名单是空的。"
        friends = [x for x in wl if x.startswith("qq:FriendMessage:")]
        others = [x for x in wl if not x.startswith("qq:FriendMessage:")]
        lines = []
        if friends:
            lines.append("私聊：" + "、".join(x.rsplit(":", 1)[-1] for x in friends))
        if others:
            lines.append("群/其他：" + "、".join(others))
        return "当前白名单：\n" + "\n".join(lines)

    # ---------- /管理员 ----------

    @filter.command("管理员")
    async def admin_cmd(
        self, event: AstrMessageEvent, action: str = "", target: str = ""
    ) -> None:
        """Manage the admin list (super admin only)."""
        level = self._level(event)
        action = (action or "").strip()
        target = _norm_qq(target)

        if not action or action in ("帮助", "help"):
            yield event.plain_result(ADMIN_HELP)
            return
        if level < 2:
            yield event.plain_result("这个指令只有我的最高管理员能用。")
            return

        cfg = self.context.astrbot_config
        admins: list = cfg["admins_id"]

        if action == "列表":
            if not admins:
                yield event.plain_result("管理员名单是空的。")
            else:
                yield event.plain_result(
                    "管理员：" + "、".join(admins)
                    + f"\n最高管理员：{'、'.join(self._super_admins())}"
                )
            return

        # /管理员 <QQ号> 等价于 /管理员 添加 <QQ号>
        if action.isdigit() and not target:
            action, target = "添加", action

        if action == "添加":
            if not target.isdigit():
                yield event.plain_result("用法：/管理员 添加 <QQ号>")
                return
            if target in admins:
                yield event.plain_result(f"{target} 本来就是管理员。")
                return
            admins.append(target)
            cfg.save_config()
            logger.info(f"[access] admin + {target} (by {event.get_sender_id()})")
            yield event.plain_result(f"{target} 现在是管理员了。")
            return

        if action == "移除":
            if not target.isdigit():
                yield event.plain_result("用法：/管理员 移除 <QQ号>")
                return
            if target in self._super_admins():
                yield event.plain_result("最高管理员不能在这里移除，去 WebUI 插件配置改。")
                return
            if target not in admins:
                yield event.plain_result(f"{target} 本来就不是管理员。")
                return
            admins.remove(target)
            cfg.save_config()
            logger.info(f"[access] admin - {target} (by {event.get_sender_id()})")
            yield event.plain_result(f"{target} 的管理员撤掉了。")
            return

        yield event.plain_result(ADMIN_HELP)
