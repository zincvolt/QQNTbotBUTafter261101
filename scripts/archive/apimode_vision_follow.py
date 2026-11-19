from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")
s = p.read_text(encoding="utf-8")

helper = '''VISION_STATE = ROOT / "data" / "vision_mode.json"


def set_vision_mode(mode: str) -> str:
    """Point the vision backend at local or third-party to match the API mode.

    Args:
        mode: ``local`` or ``third_party``.

    Returns:
        The previous vision mode for logging.
    """
    try:
        state = json.loads(VISION_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = {}
    previous = state.get("mode", "local")
    state["mode"] = mode
    state.setdefault("port", 8085)
    state.setdefault("model", "Qwen3VL-4B-Instruct")
    VISION_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return previous


'''
if "def set_vision_mode(" not in s:
    s = s.replace("def unload_local_models()", helper + "def unload_local_models()", 1)

# 切 API 时识图跟着切第三方；切回本地时恢复
s = s.replace(
    '''                stopped = unload_local_models()''',
    '''                set_vision_mode("third_party")
                stopped = unload_local_models()''',
    1,
)
s = s.replace(
    '''                start_local_models()''',
    '''                set_vision_mode("local")
                start_local_models()''',
    1,
)
# watcher 同理
s = s.replace(
    '''                if is_api and not was_api:
                    stopped = unload_local_models()''',
    '''                if is_api and not was_api:
                    set_vision_mode("third_party")
                    stopped = unload_local_models()''',
    1,
)
s = s.replace(
    '''                elif was_api and not is_api:
                    start_local_models()''',
    '''                elif was_api and not is_api:
                    set_vision_mode("local")
                    start_local_models()''',
    1,
)
p.write_text(s, encoding="utf-8")
print("识图随模式联动")
