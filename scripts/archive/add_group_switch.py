"""Add a per-group switch and admin enable/disable commands."""

from pathlib import Path

PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = PLUGIN.read_text(encoding="utf-8")

# 1) 开关文件路径
s = s.replace(
    'WATCH_FILE = ROOT / "data" / "furcon_watch.json"',
    'WATCH_FILE = ROOT / "data" / "furcon_watch.json"\n'
    'ENABLE_FILE = ROOT / "data" / "furcon_enabled.json"',
    1,
)

# 2) 读取开关
loader = '''def group_enabled(group_id: str) -> bool:
    """Return whether the feature set is enabled for one group."""
    if not ENABLE_FILE.exists():
        return False
    try:
        data = json.loads(ENABLE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    groups = data.get("groups") or {}
    return bool(groups.get(str(group_id), False))


def set_group_enabled(group_id: str, enabled: bool) -> None:
    """Enable or disable the feature set for one group."""
    data = {"groups": {}}
    if ENABLE_FILE.exists():
        try:
            data = json.loads(ENABLE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"groups": {}}
    data.setdefault("groups", {})[str(group_id)] = bool(enabled)
    ENABLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENABLE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")


'''
if "def group_enabled(" not in s:
    s = s.replace("def match_command(", loader + "def match_command(", 1)

# 3) 新命令：启用/关闭
s = s.replace(
    '    ("watch_off", re.compile(r"(取消关心|不关心了|取消关注)")),',
    '    ("enable_on", re.compile(r"^(启用功能|开启功能|打开功能|启用)$")),\n'
    '    ("enable_off", re.compile(r"^(关闭功能|停用功能|禁用功能|关闭)$")),\n'
    '    ("watch_off", re.compile(r"(取消关心|不关心了|取消关注)")),',
    1,
)

# 4) 处理器最前面加开关检查 + 管理员开关命令
old_head = '''        key, city = match_command(text, slash=slash)
        logger.info(f"[furcon] recv slash={slash} key={key or '-'} text={text[:24]}")
        if not key:
            return'''
new_head = '''        key, city = match_command(text, slash=slash)
        logger.info(f"[furcon] recv slash={slash} key={key or '-'} text={text[:24]}")
        if not key:
            return

        group_id = str(event.get_group_id() or "")
        sender = str(event.get_sender_id() or "")

        # 管理员开关命令（私聊/群聊都能用）
        if key in ("enable_on", "enable_off"):
            if sender not in ADMINS:
                await event.send(event.plain_result("只有管理员能改开关"))
                event.stop_event()
                return
            if not group_id:
                await event.send(event.plain_result("请在要开启的群里发这条指令"))
                event.stop_event()
                return
            set_group_enabled(group_id, key == "enable_on")
            state = "已启用" if key == "enable_on" else "已关闭"
            await event.send(event.plain_result(f"本群功能{state}"))
            event.stop_event()
            return

        # 未启用的群：只回一句提示，不做任何事
        if group_id and not group_enabled(group_id):
            if key == "help":
                pass
            else:
                await event.send(
                    event.plain_result("未启用请联系本机管理员1154487120 owo")
                )
                event.stop_event()
                return'''
if old_head in s:
    s = s.replace(old_head, new_head, 1)
    print("switch wired")

# 5) 帮助追加
s = s.replace(
    "/兽聚help  这张说明",
    "/兽聚help  这张说明\n\n管理员：\n/启用功能  开启本群功能\n/关闭功能  关闭本群功能",
    1,
)

PLUGIN.write_text(s, encoding="utf-8")
print("done")
