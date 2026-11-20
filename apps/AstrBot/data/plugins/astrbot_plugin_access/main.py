from __future__ import annotations

# 权限闸门：统一斜线指令鉴权 + 主动回复冲突仲裁 + 指令权限表管理。
#
# 权限分组（三级，全插件统一判定）：
#   2 = 超级管理员 —— plugin 配置 super_admins（默认 1154487120）
#   1 = 管理员     —— AstrBot admins_id ∪ FURCON_ADMINS（兼容兽聚旧名单）
#   0 = 普通用户   —— 其他人
#
# 三条职责：
#   1. 鉴权闸门：斜线/唤醒指令最先过这里，级别不够直接拦（stop_event），
#      鉴权通过则放行给各插件自己的 handler——各插件不用改
#   2. 防冲突：加载时把 handler 优先级分档（闸门 > 指令 > 纯监听），
#      指令永远抢在主动回复/复读机之前跑完并 stop_event，替代各插件
#      自己的 maxsize 力大砖飞
#   3. 指令权限表：/权限 查看与编辑「哪些指令谁可用」，落盘 cmd_perm.json
#
# 配置读取用 self.context.get_config()（Context 没有 astrbot_config 属性，
# 第一版就栽在这里，测试桩 mock 了错的属性没测出来）。

import ast
import json
import os
import re
import sys
import time
from pathlib import Path

from astrbot.api import logger, star
from astrbot.api.event import AstrMessageEvent, filter

# ---------- 级别 ----------

LV_USER, LV_ADMIN, LV_SUPER = 0, 1, 2
LV_LABEL = {LV_USER: "公开", LV_ADMIN: "管理", LV_SUPER: "超管"}
LV_FROM_WORD = {
    "user": LV_USER, "公开": LV_USER, "普通": LV_USER, "普通用户": LV_USER,
    "admin": LV_ADMIN, "管理": LV_ADMIN, "管理员": LV_ADMIN,
    "super": LV_SUPER, "超管": LV_SUPER, "最高": LV_SUPER, "超级": LV_SUPER,
}

# ---------- 优先级分档（防主动回复冲突） ----------
# 数字越大越先跑。闸门最前；指令 handler 次之（含兽聚/骰子这类手写
# 指令匹配的 listener）；纯监听（内置主动回复/复读机/群聊上下文）最后。
GATE_PRIORITY = sys.maxsize
CMD_BAND = sys.maxsize - 10
LISTENER_BAND = sys.maxsize - 100

# 手写指令匹配（非 CommandFilter）的插件模块名——它们必须排在主动回复前
_CMD_LISTENER_MODS = (
    "astrbot_plugin_furcon",
    "astrbot_plugin_dice",
    "astrbot_plugin_apimode",
)

# 本插件自声明指令（单拎时帮助/权限表自动读这里）
DECLARED_COMMANDS = {
    "/指令": ("所有人可用的指令列表（一图流）", "公开"),
    "/权限 列表": ("看全部指令和级别", "公开"),
    "/权限 检查 <指令>": ("看某指令当前级别", "超管"),
    "/权限 设置 <指令> <级别>": ("改指令级别", "超管"),
    "/权限 重置 <指令>": ("恢复默认级别", "超管"),
    "/私聊 列表": ("看白名单（对个人）", "公开"),
    "/私聊 允许/拒绝 <QQ号>": ("聊天功能开关（对个人）", "管理"),
    "/私聊 检查开/检查关": ("白名单检查总闸", "管理"),
    "/管理员 列表": ("看管理员名单", "超管"),
    "/管理员 添加/移除 <QQ号>": ("管管管理员名单", "超管"),
}

# ---------- 指令权限表默认值 ----------
# prefix=前缀匹配（带参数指令）; exact=全等（短/泛用词防误伤）; contains=包含
# （仅唤醒时判定，全部为公开级，误命中无害）。级别一律以表为准，可在线改。
#
# 【两套开关必须分清作用域】
#   兽聚功能开关（对群）：启用/关闭族 → furcon_enabled.json 按 group_id 存
#   聊天功能开关（对个人）：/私聊 允许/拒绝 → id_whitelist 按 QQ 存 + 总闸
#   两者状态独立、互不影响，指令表里也分列标注。
DEFAULT_PERM: dict = {
    "prefix": {
        # 内置——astr /help 含有的框架指令全部管理员（2026-11-20）：
        # 框架自带的指令清单不对外暴露，普通用户看 /指令 那张公开卡
        "help": "admin", "sid": "admin", "name": "admin",
        "reset": "admin", "stop": "admin", "new": "admin",
        "stats": "admin", "provider": "admin",
        "dashboard_update": "admin", "set": "admin", "unset": "admin",
        # 本插件（细粒度动作由各 handler 内部再判）
        # 「私聊」= 聊天功能开关，对个人生效（id_whitelist 按 QQ 存）
        "私聊": "user", "管理员": "user", "权限": "super",
        # 本插件：公开指令列表
        "指令": "user",
        # ltm
        "记忆": "user", "忘记": "user",
        # dice
        "r": "user", "roll": "user", "dice": "user",
        "骰": "user", "掷骰": "user", "投骰": "user",
        # meme_manager 子指令带 ADMIN 过滤器
        "表情管理": "admin",
        # 兽聚（管理员类；查询类在 exact/contains）
        "兽聚help": "user", "兽聚指令": "user", "兽聚功能": "user", "兽聚用法": "user",
        "关心": "admin", "特别关心": "admin", "关注": "admin",
        "取消关心": "admin", "不关心了": "admin", "取消关注": "admin",
        # apimode——全插件管理员可用（2026-11-20）
        "切换": "admin", "省token": "admin", "审查": "admin", "判官": "admin",
        "额度": "admin", "思维链": "admin",
    },
    "exact": {
        "用量": "admin", "额度查询": "admin",
        # 兽聚功能开关，对群生效（furcon_enabled.json 按 group_id 存）
        "启用": "admin", "启用功能": "admin", "开启功能": "admin", "打开功能": "admin",
        "关闭": "admin", "关闭功能": "admin", "停用功能": "admin", "禁用功能": "admin",
    },
    "contains": {
        "运势": "user", "运气": "user", "抽个签": "user", "求签": "user",
        "吉凶": "user", "今日份": "user", "转运": "user", "人品": "user",
        "jrrp": "user", "jrys": "user",
        "群统计": "user", "发言统计": "user", "谁最活跃": "user",
        "水群榜": "user", "活跃度": "user", "话最多": "user", "谁话多": "user",
    },
    "unknown_slash": "user",
}

PERM_FILE = Path(__file__).parent / "cmd_perm.json"
DENY_TEXT = {
    LV_ADMIN: "这个指令只有管理员能用喵。",
    LV_SUPER: "这个指令只有我的最高管理员能用。",
}

# ---------- 一图流绘卡（惰性导入，与权限功能彻底解耦） ----------
# 绘卡是锦上添花，绝不能影响权限加载。import 全放函数内部。
def _render_card(title: str, lines: list[str], footer: str = ""):
    """惰性渲染图卡，失败返回 None。"""
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from card_render import render_text_card
        return render_text_card(title, lines, footer=footer)
    except Exception:  # noqa: BLE001 - 绘卡坏了不影响权限
        return None

def _help_result(event, title: str, lines: list[str]) -> "object":
    """帮助/列表输出：绘卡可用给图，否则降级纯文字。"""
    path = _render_card(title, lines)
    if path is not None:
        try:
            return event.image_result(str(path))
        except Exception:  # noqa: BLE001
            pass
    text = title + "\n" + "\n".join(l for l in lines if l and not l.startswith("#"))
    return event.plain_result(text)

PRIV_HELP_LINES = [
    "## 聊天功能开关（对个人）",
    "/私聊 列表 —— 看当前白名单",
    "/私聊 允许 <QQ号> —— 允许对方私聊我",
    "/私聊 拒绝 <QQ号> —— 取消对方私聊权限",
    "/私聊 检查开 / 检查关 —— 开关白名单检查",
    "> 管理员本人本来就能私聊我",
    "> 存储在 id_whitelist（按 QQ 号），与兽聚开关（对群）分开管理",
]

ADMIN_HELP_LINES = [
    "## 管理员名单（仅最高管理员）",
    "/管理员 列表 —— 看管理员名单",
    "/管理员 添加 <QQ号> —— 提升为管理员",
    "/管理员 移除 <QQ号> —— 撤掉管理员",
    "/管理员 <QQ号> —— 等价于 添加",
    "> 最高管理员名单在 WebUI 插件配置里改",
]

PERM_HELP_LINES = [
    "## 指令权限表（仅最高管理员可改）",
    "/权限 列表 —— 按插件分组看全部指令",
    "/权限 列表 <插件名> —— 只看某个插件",
    "/权限 检查 <指令> —— 看某指令当前级别",
    "/权限 设置 <指令> <公开|管理|超管> —— 改级别",
    "/权限 重置 <指令> —— 恢复默认",
    "级别：公开=谁都能用 管理=管理员 超管=只有最高管理员",
]


def _norm_qq(qq: str) -> str:
    """Strip a QQ number argument down to digits."""
    return str(qq or "").strip()


def _furcon_admins() -> set[str]:
    """兼容兽聚的 FURCON_ADMINS 环境变量名单。"""
    raw = os.environ.get("FURCON_ADMINS", "")
    return {x.strip() for x in re.split(r"[,\s]+", raw) if x.strip()}


class MyPlugin(star.Star):
    def __init__(self, context: star.Context, config=None) -> None:
        # star_manager 以 config=plugin_config 关键字实例化；签名不收 config 会
        # 抛 TypeError 被框架静默降级为无 config 构造，super_admins 读空（踩过）。
        super().__init__(context, config=config)
        self.config = config
        self._perm: dict = self._load_perm()
        self._declared: dict = self._load_declared()
        # 热加载/启动都跑一遍分档；on_astrbot_loaded 时全插件就位再终跑
        self._enforce_bands()

    # ================= 分档仲裁（替代 maxsize 力大砖飞） =================

    @filter.on_astrbot_loaded()
    async def on_loaded(self) -> None:
        self._enforce_bands()

    def _enforce_bands(self) -> None:
        """把 AdapterMessageEvent 的 handler 按职责分档排序。

        闸门 > 指令类（CommandFilter + 兽聚/骰子/apimode 手写指令）> 纯监听。
        同档保持原有相对顺序（sort 稳定）。分档后各插件自己写的 priority
        （包括兽聚的 maxsize）全部失效，冲突仲裁权归本插件。
        """
        try:
            from astrbot.core.star.filter.command import CommandFilter
            from astrbot.core.star.filter.command_group import CommandGroupFilter
            from astrbot.core.star.star_handler import (
                EventType,
                star_handlers_registry,
            )
        except Exception as e:  # noqa: BLE001 - 框架结构变化时降级不分档
            logger.warning(f"[access] band skip: {e}")
            return

        def is_cmd_handler(h) -> bool:
            return any(
                isinstance(f, (CommandFilter, CommandGroupFilter))
                for f in h.event_filters
            )

        changed = 0
        for h in star_handlers_registry._handlers:  # noqa: SLF001 - 框架无公开重排 API
            if getattr(h, "event_type", None) != EventType.AdapterMessageEvent:
                continue
            mod = h.handler_module_path or ""
            if is_cmd_handler(h):
                want = CMD_BAND
            elif "astrbot_plugin_access" in mod:
                want = GATE_PRIORITY
            elif any(m in mod for m in _CMD_LISTENER_MODS):
                want = CMD_BAND
            else:
                want = LISTENER_BAND
            if h.extras_configs.get("priority") != want:
                h.extras_configs["priority"] = want
                changed += 1

        star_handlers_registry._handlers.sort(  # noqa: SLF001
            key=lambda h: -h.extras_configs.get("priority", 0)
        )
        if changed:
            logger.info(f"[access] priority bands enforced ({changed} handlers moved)")

    # ================= 指令权限表 =================

    def _load_perm(self) -> dict:
        data = json.loads(json.dumps(DEFAULT_PERM))  # deep copy
        try:
            if PERM_FILE.exists():
                raw = PERM_FILE.read_text(encoding="utf-8").strip()
                if raw:
                    saved = json.loads(raw)
                    for section in ("prefix", "exact", "contains"):
                        if isinstance(saved.get(section), dict):
                            data[section].update(saved[section])
                    if saved.get("unknown_slash") in ("user", "admin", "super"):
                        data["unknown_slash"] = saved["unknown_slash"]
        except Exception as e:  # noqa: BLE001 - 文件坏了按默认走
            logger.warning(f"[access] cmd_perm.json broken, using defaults: {e}")
        self._autodiscover(data)
        return data

    def _save_perm(self) -> None:
        try:
            PERM_FILE.write_text(
                json.dumps(self._perm, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"[access] save cmd_perm failed: {e}")

    def _autodiscover(self, data: dict) -> None:
        """把注册在册的 CommandFilter 指令补进表（已有的不覆盖用户编辑）。"""
        try:
            from astrbot.core.star.filter.command import CommandFilter
            from astrbot.core.star.filter.command_group import CommandGroupFilter
            from astrbot.core.star.filter.permission import PermissionType
            from astrbot.core.star.star_handler import star_handlers_registry
        except Exception:  # noqa: BLE001
            return
        for h in star_handlers_registry._handlers:  # noqa: SLF001
            names: set[str] = set()
            admin_filtered = False
            for f in h.event_filters:
                if isinstance(f, CommandFilter):
                    names.add(f.command_name)
                    names.update(f.alias or set())
                elif isinstance(f, CommandGroupFilter):
                    names.update(f.get_complete_command_names())
                elif (
                    getattr(f, "permission_type", None) == PermissionType.ADMIN
                ):
                    admin_filtered = True
            default_lv = "admin" if admin_filtered else "user"
            for n in names:
                n = str(n).strip()
                if n and n not in data["prefix"]:
                    data["prefix"][n] = default_lv

    def _perm_level(self, cmd: str) -> int:
        for section in ("prefix", "exact", "contains"):
            if cmd in self._perm.get(section, {}):
                word = self._perm[section][cmd]
                return LV_FROM_WORD.get(word, LV_USER)
        if cmd == "__unknown__":
            return LV_FROM_WORD.get(self._perm.get("unknown_slash", "user"), LV_USER)
        return LV_USER

    def _match_cmd(self, event: AstrMessageEvent) -> str | None:
        """识别消息是否是指令，返回表里的指令名（未知斜线→__unknown__）。"""
        text = (event.message_str or "").strip()
        if not text:
            return None
        raw = ""
        msg_obj = getattr(event, "message_obj", None)
        raw_msg = getattr(msg_obj, "raw_message", None)
        if isinstance(raw_msg, dict):
            raw = str(raw_msg.get("raw_message") or "")
        elif isinstance(raw_msg, str):
            raw = raw_msg
        slashed = raw.lstrip().startswith(("/", "／")) or text.startswith(
            ("/", "／")
        )
        woken = bool(getattr(event, "is_at_or_wake_command", False))
        if not slashed and not woken:
            return None  # 群里普通闲聊不拦

        body = re.sub(r"^\s*[/／]\s*", "", text).strip()
        if not body:
            return None

        # 1. 前缀匹配（长的优先，避免「兽聚」遮住「兽聚help」）
        for key in sorted(self._perm.get("prefix", {}), key=len, reverse=True):
            if body == key or body.startswith(key + " ") or body.startswith(key + "\t"):
                return key
        # 2. 全等
        for key in self._perm.get("exact", {}):
            if body == key:
                return key
        # 3. 未知斜线指令
        if slashed:
            return "__unknown__"
        # 4. 唤醒后的包含词（furcon 查询类；均为公开级，误命中无害）
        if woken:
            for key in self._perm.get("contains", {}):
                if key in body:
                    return key
        return None

    # ================= 权限分组 =================

    def _super_admins(self) -> list[str]:
        try:
            return [str(x) for x in (self.config or {}).get("super_admins", [])]
        except Exception:  # noqa: BLE001 - 配置坏了按空处理
            return []

    def _admins(self) -> list[str]:
        try:
            cfg = self.context.get_config()
            ids = [str(x) for x in (cfg.get("admins_id") or [])]
        except Exception:  # noqa: BLE001
            ids = []
        return ids

    def _level(self, event: AstrMessageEvent) -> int:
        """2=超级管理员 1=管理员 0=普通用户。统一口径，全插件共用。"""
        uid = str(event.get_sender_id() or "")
        if not uid:
            return LV_USER
        if uid in self._super_admins():
            return LV_SUPER
        if uid in self._admins() or uid in _furcon_admins():
            return LV_ADMIN
        if getattr(event, "role", "") == "admin":
            return LV_ADMIN
        return LV_USER

    # ================= 鉴权闸门 =================
    # gate 是唯一入口（GATE_PRIORITY 最先跑），三个指令直接在这里处理。
    # 不依赖 @filter.command 分派——避免被其他 listener 抢先（踩过）。

    @filter.event_message_type(filter.EventMessageType.ALL, priority=GATE_PRIORITY)
    async def gate(self, event: AstrMessageEvent) -> None:
        """指令最先过闸：级别不够直接拦，够了就放行；access 自己的指令直接处理。永不崩溃。"""
        try:
            cmd = self._match_cmd(event)
            if not cmd:
                return

            # ---- access 自己的指令直接处理，不走 CommandFilter ----
            if cmd in ("权限", "私聊", "管理员", "指令"):
                level = self._level(event)
                body = re.sub(r"^\s*[/／]\s*", "", (event.message_str or "")).strip()
                rest = body[len(cmd):].strip()
                parts = rest.split(None, 2) if rest else []
                action = parts[0] if parts else ""
                target = parts[1] if len(parts) > 1 else ""
                lv = parts[2] if len(parts) > 2 else ""
                # 直接 send 发送（furcon 同款通道）：yield 通道会被 peer 的
                # decorate_result 误杀——图卡链无纯文本被判「空回复」清空并停事件，
                # respond 阶段永不执行（踩过，2026-11-20）。send 不走 result 处理。
                if cmd == "权限":
                    async for r in self._do_perm(event, level, action, target, lv):
                        await event.send(r)
                elif cmd == "指令":
                    async for r in self._do_cmds(event):
                        await event.send(r)
                elif cmd == "私聊":
                    async for r in self._do_private(event, level, action, target):
                        await event.send(r)
                else:
                    async for r in self._do_admin(event, level, action, target):
                        await event.send(r)
                event.stop_event()
                return

            # ---- 其他指令：只做鉴权，放行给各插件 ----
            need = self._perm_level(cmd)
            level = self._level(event)
            if level >= need:
                try:
                    extra = event.get_extra("handlers_parsed_params", None)
                    if extra is not None and not extra:
                        extra["__access_cmd__"] = {"cmd": cmd}
                except Exception:  # noqa: BLE001
                    pass
                return
            await event.send(
                event.plain_result(DENY_TEXT.get(need, "这个指令你用不了喵。"))
            )
            event.stop_event()
        except Exception as exc:  # noqa: BLE001 - gate 绝不崩溃，放行让其他插件处理
            logger.warning(f"[access] gate error (pass-through): {exc}")

    # ================= /指令（公开指令列表） =================

    def _is_public_row(self, key: str, declared_lvl: str) -> bool:
        """一行声明是否对所有人真的可用。

        双重判定：闸门级别（权限表实际值）与声明级别都为公开才算——
        只看声明会漏掉 handler 内部再拦的（/读图），只看闸门会漏掉
        内部细粒度动作（/私聊 允许）。取两者更严的一档。
        """
        if LV_FROM_WORD.get((declared_lvl or "公开").strip(), LV_USER) != LV_USER:
            return False
        head = key.lstrip("/／").strip().split()[0] if key.strip() else ""
        if not head:
            return False
        found = self._find_perm(head)
        word = found[2] if found else self._perm.get("unknown_slash", "user")
        return LV_FROM_WORD.get(word, LV_USER) == LV_USER

    def _public_lines(self) -> list[str]:
        """公开指令列表的卡面内容，按模块分类。"""
        lines: list[str] = []
        for short, info in sorted(self._declared.items()):
            rows = []
            for key, item in sorted(info["commands"].items()):
                desc, lvl = (
                    item if isinstance(item, tuple) else (str(item), "公开")
                )
                if not self._is_public_row(key, lvl):
                    continue
                rows.append(f"  {key} —— {desc}")
            if rows:
                lines.append(f"## {short}")
                lines.extend(rows)
                lines.append("")

        # 没被声明认领的公开键：斜杠别名 + 唤醒词
        claimed: set[str] = set()
        for info in self._declared.values():
            for key in info["commands"]:
                head = key.lstrip("/／").strip().split()[0] if key.strip() else ""
                if head:
                    claimed.add(head)
        alias = [
            f"/{key}"
            for section in ("prefix", "exact")
            for key, word in sorted(self._perm.get(section, {}).items())
            if key not in claimed and LV_FROM_WORD.get(word, 0) == LV_USER
        ]
        wake = sorted(
            key
            for key, word in self._perm.get("contains", {}).items()
            if key not in claimed and LV_FROM_WORD.get(word, 0) == LV_USER
        )
        if alias:
            lines.append("## 别名")
            lines.append("  " + "  ".join(alias))
            lines.append("")
        if wake:
            lines.append("## 唤醒词（不用斜杠也能触发）")
            lines.append("  " + "、".join(wake))
            lines.append("")
        if not lines:
            lines = ["（现在没有对所有人开放的指令）"]
        return lines

    async def _do_cmds(self, event: AstrMessageEvent) -> None:
        """所有人可用的指令列表，一图流按模块分类。"""
        try:
            lines = self._public_lines()
        except Exception as exc:  # noqa: BLE001 - 列表挂了给一句兜底
            logger.warning(f"[access] public cmd list failed: {exc}")
            await event.send(event.plain_result("指令列表生成失败了，稍后再试。"))
            return
        path = _render_card("指令列表·所有人可用", lines, footer="管理类指令不在此列")
        if path is not None:
            yield event.image_result(str(path))
            return
        # 绘卡不可用：降级纯文字
        text = "指令列表（所有人可用）：\n" + "\n".join(
            l for l in lines if not l.startswith("## ")
        )
        yield event.plain_result(text)

    # ================= /权限（指令权限表） =================

    async def _do_perm(
        self, event: AstrMessageEvent, level: int, action: str, target: str = "", lv: str = ""
    ) -> None:
        """Manage the per-command permission table."""
        action = (action or "").strip()
        target = (target or "").strip().lstrip("/／").strip()
        lv = (lv or "").strip()

        if not action or action in ("帮助", "help"):
            yield _help_result(event, "权限指令帮助", PERM_HELP_LINES)
            return
        if action == "列表":
            try:
                yield event.image_result(str(self._perm_card(target)))
            except Exception:  # noqa: BLE001 - 绘卡失败降级文字
                yield event.plain_result(self._perm_text_fallback())
            return
        if level < LV_SUPER:
            yield event.plain_result("这个指令只有我的最高管理员能用。")
            return

        if action == "检查":
            if not target:
                yield event.plain_result("用法：/权限 检查 <指令>")
                return
            found = self._find_perm(target)
            if not found:
                yield event.plain_result(f"「{target}」不在权限表里。")
                return
            section, key, word = found
            yield event.plain_result(
                f"{key}（{section}）当前级别：{LV_LABEL.get(LV_FROM_WORD.get(word, 0), word)}"
            )
            return

        if action == "设置":
            if not target or lv not in LV_FROM_WORD:
                yield event.plain_result("用法：/权限 设置 <指令> <公开|管理|超管>")
                return
            word = {
                LV_USER: "user", LV_ADMIN: "admin", LV_SUPER: "super",
            }[LV_FROM_WORD[lv]]
            found = self._find_perm(target)
            if found:
                section, key, _ = found
                self._perm[section][key] = word
            else:
                self._perm["prefix"][target] = word
            self._save_perm()
            logger.info(f"[access] perm set {target} -> {word} (by {event.get_sender_id()})")
            yield event.plain_result(
                f"{target} 现在是「{LV_LABEL[LV_FROM_WORD[lv]]}」级指令了。"
            )
            return

        if action == "重置":
            if not target:
                yield event.plain_result("用法：/权限 重置 <指令>")
                return
            found = self._find_perm(target)
            if found:
                section, key, _ = found
                default = DEFAULT_PERM.get(section, {}).get(key)
                if default is not None:
                    self._perm[section][key] = default
                else:
                    del self._perm[section][key]  # 自动发现的，删了回落 user
            else:
                yield event.plain_result(f"「{target}」不在权限表里。")
                return
            self._save_perm()
            yield event.plain_result(f"{target} 已恢复默认级别。")
            return

        yield _help_result(event, "权限指令帮助", PERM_HELP_LINES)

    def _find_perm(self, name: str) -> tuple[str, str, str] | None:
        """定位指令在表里的 (section, key, word)，三个区都找。"""
        for section in ("prefix", "exact", "contains"):
            if name in self._perm.get(section, {}):
                return section, name, self._perm[section][name]
        return None

    def _perm_text_fallback(self) -> str:
        """绘卡失败时的纯文字权限表。"""
        lines = []
        for section, title in (
            ("prefix", "带参数指令"),
            ("exact", "固定指令"),
            ("contains", "包含词（唤醒时）"),
        ):
            entries = self._perm.get(section, {})
            if not entries:
                continue
            lines.append(f"【{title}】")
            for key in sorted(entries, key=lambda k: (LV_FROM_WORD.get(entries[k], 0), k)):
                word = entries[key]
                lines.append(f"  {key} → {LV_LABEL.get(LV_FROM_WORD.get(word, 0), word)}")
        word = self._perm.get("unknown_slash", "user")
        lines.append(f"未知斜线指令 → {LV_LABEL.get(LV_FROM_WORD.get(word, 0), '公开')}")
        return "指令权限表：\n" + "\n".join(lines)

    def _load_declared(self) -> dict[str, dict]:
        """扫描全部插件目录，ast 提取 DECLARED_COMMANDS / DECLARED_BEHAVIOR。

        ast.literal_eval 只取字面量、不执行插件代码；解析失败的插件跳过。
        返回 {短名: {"commands": {...}, "behavior": str, "declared": bool}}。
        """
        out: dict[str, dict] = {}
        plugins_dir = Path(__file__).parent.parent
        for d in sorted(plugins_dir.iterdir()):
            if not d.is_dir():
                continue
            main_py = d / "main.py"
            if not main_py.exists():
                continue
            info = {"commands": {}, "behavior": "", "declared": False}
            try:
                tree = ast.parse(main_py.read_text(encoding="utf-8", errors="ignore"))
            except Exception:  # noqa: BLE001 - 语法坏文件不影响其余插件
                continue
            for node in tree.body:
                # 兼容两种赋值：DECLARED_X = ...（Assign）与
                # DECLARED_X: dict[...] = ...（AnnAssign，带类型注解）
                if isinstance(node, ast.Assign):
                    tgt = node.targets[0] if node.targets else None
                elif isinstance(node, ast.AnnAssign):
                    tgt = node.target
                else:
                    continue
                if not (isinstance(tgt, ast.Name)
                        and tgt.id in ("DECLARED_COMMANDS", "DECLARED_BEHAVIOR")):
                    continue
                try:
                    val = ast.literal_eval(node.value)
                except Exception:  # noqa: BLE001
                    continue
                info["declared"] = True
                if tgt.id == "DECLARED_COMMANDS" and isinstance(val, dict):
                    info["commands"] = val
                elif tgt.id == "DECLARED_BEHAVIOR" and isinstance(val, str):
                    info["behavior"] = val
            out[d.name.replace("astrbot_plugin_", "")] = info
        return out

    def _perm_card(self, only: str = "") -> Path:
        """指令权限表按插件分组渲染成一图流；only 非空只看该插件。"""
        lines: list[str] = []
        only_n = (only or "").replace("astrbot_plugin_", "").strip().lower()

        # 声明键的指令头（去斜杠第一段），用于识别权限表里「无归属」的指令
        claimed_heads: set[str] = set()
        missing: list[str] = []
        for short, info in sorted(self._declared.items()):
            if only_n and only_n != short.lower():
                continue
            cmds = info["commands"]
            if not cmds and not info.get("behavior"):
                missing.append(short)
                continue
            lines.append(f"## {short}")
            if cmds:
                for key, item in sorted(cmds.items()):
                    desc, lvl = (item if isinstance(item, tuple) else (str(item), "公开"))
                    claimed_heads.add(key.lstrip("/／").split()[0] if key.lstrip("/／") else "")
                    lines.append(f"  {key} —— {desc} [{lvl}]")
            else:
                lines.append(f"  （无斜线指令）{info['behavior']}")
            lines.append("")

        if not only_n:
            # 权限表里有、但没有任何插件声明的指令 → 归「内置/未分组」
            ungrouped: list[tuple[str, str]] = []
            for section in ("prefix", "exact", "contains"):
                for key, word in self._perm.get(section, {}).items():
                    if key not in claimed_heads:
                        ungrouped.append(
                            (key, LV_LABEL.get(LV_FROM_WORD.get(word, 0), word))
                        )
            if ungrouped:
                lines.append("## 内置指令与别名")
                for key, label in sorted(ungrouped):
                    lines.append(f"  /{key} [{label}]")
                lines.append("")
            if missing:
                lines.append("## ⚠ 未声明指令（不符合插件规范）")
                lines.append("  " + "、".join(missing))
                lines.append("")
            word = self._perm.get("unknown_slash", "user")
            lines.append(
                f"未知斜线指令默认 → {LV_LABEL.get(LV_FROM_WORD.get(word, 0), '公开')}"
            )
        return _render_card(
            "指令权限表·按插件" + (f"·{only_n}" if only_n else ""),
            lines,
            footer="只看单个插件：/权限 列表 <插件名>",
        )

    # ================= /私聊（白名单） =================

    async def _do_private(
        self, event: AstrMessageEvent, level: int, action: str, target: str = ""
    ) -> None:
        """Manage the private-chat whitelist."""
        action = (action or "").strip()
        target = _norm_qq(target)

        if not action or action in ("帮助", "help"):
            yield _help_result(event, "私聊权限帮助", PRIV_HELP_LINES)
            return
        if action == "列表":
            yield event.plain_result(self._wl_text())
            return
        if level < LV_ADMIN:
            yield event.plain_result("这个指令只有管理员能用喵。")
            return

        cfg = self.context.get_config()
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

        yield _help_result(event, "私聊权限帮助", PRIV_HELP_LINES)

    def _wl_text(self) -> str:
        try:
            cfg = self.context.get_config()
            wl = [str(x) for x in cfg["platform_settings"]["id_whitelist"]]
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

    # ================= /管理员 =================

    async def _do_admin(
        self, event: AstrMessageEvent, level: int, action: str, target: str = ""
    ) -> None:
        """Manage the admin list (super admin only)."""
        action = (action or "").strip()
        target = _norm_qq(target)

        if not action or action in ("帮助", "help"):
            yield _help_result(event, "管理员帮助", ADMIN_HELP_LINES)
            return
        if level < LV_SUPER:
            yield event.plain_result("这个指令只有我的最高管理员能用。")
            return

        cfg = self.context.get_config()
        admins: list = cfg["admins_id"]

        if action == "列表":
            if not admins:
                yield event.plain_result("管理员名单是空的。")
            else:
                yield event.plain_result(
                    "管理员：" + "、".join(str(a) for a in admins)
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
            if target in [str(a) for a in admins]:
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
            if target not in [str(a) for a in admins]:
                yield event.plain_result(f"{target} 本来就不是管理员。")
                return
            admins.remove(target)
            cfg.save_config()
            logger.info(f"[access] admin - {target} (by {event.get_sender_id()})")
            yield event.plain_result(f"{target} 的管理员撤掉了。")
            return

        yield _help_result(event, "管理员帮助", ADMIN_HELP_LINES)
