"""统一权限判定模块——供 access 外的插件共用，取消各自独立权限组。

与 astrbot_plugin_access 的 _level() 同口径：
  2=超管（access 插件配置 super_admins，WebUI 可改）
  1=管理（AstrBot admins_id ∪ FURCON_ADMINS 环境变量 ∪ 群管理员角色）
  0=普通用户

用法（在各插件 main.py 顶部）：
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "astrbot_plugin_access"))
    from unified_perm import is_admin, is_super

不要再各自维护 ADMINS 名单——谁是管理员归 access 统一管理。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

LV_USER, LV_ADMIN, LV_SUPER = 0, 1, 2

_ACCESS_CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\config\astrbot_plugin_access_config.json")
_ASTRBOT_CFG = Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json")


def _super_admins() -> list[str]:
    try:
        raw = json.loads(_ACCESS_CFG.read_text(encoding="utf-8"))
        return [str(x) for x in raw.get("super_admins", [])]
    except Exception:
        return []


def _admins() -> list[str]:
    try:
        raw = json.loads(_ASTRBOT_CFG.read_text(encoding="utf-8"))
        return [str(x) for x in raw.get("admins_id") or []]
    except Exception:
        return []


def _furcon_admins() -> set[str]:
    raw = os.environ.get("FURCON_ADMINS", "")
    return {x.strip() for x in re.split(r"[,\s]+", raw) if x.strip()}


def get_level(event) -> int:
    """2=超管 1=管理 0=普通。统一口径，全插件共用。"""
    uid = str(event.get_sender_id() or "")
    if not uid:
        return LV_USER
    if uid in _super_admins():
        return LV_SUPER
    if uid in _admins() or uid in _furcon_admins():
        return LV_ADMIN
    if getattr(event, "role", "") == "admin":
        return LV_ADMIN
    return LV_USER


def is_admin(event) -> bool:
    return get_level(event) >= LV_ADMIN


def is_super(event) -> bool:
    return get_level(event) >= LV_SUPER


def admin_qqs() -> list[str]:
    """管理员 QQ 列表（含超管），用于提示文案。"""
    seen: list[str] = []
    for x in _super_admins() + _admins() + sorted(_furcon_admins()):
        if x and x not in seen:
            seen.append(x)
    return seen
