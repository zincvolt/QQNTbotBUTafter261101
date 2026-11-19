from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py")
s = p.read_text(encoding="utf-8")
if "_api_mode_is_third_party" not in s:
    helper = '''def _api_mode_is_third_party() -> bool:
    """Return True when the bot runs on the third-party API.

    Local big models must not be used in that mode, so memory extraction is
    skipped entirely.

    Returns:
        Whether the bot is currently on the third-party API.
    """
    import json
    from pathlib import Path as _Path

    state = _Path(r"D:\\QQNTBOT\\data\\api_mode.json")
    if not state.exists():
        return False
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("mode") == "third_party"
    except Exception:  # noqa: BLE001
        return False


'''
    anchor = "async def _scan_once(self) -> None:"
    idx = s.index(anchor)
    s = s[:idx] + helper + s[idx:]
    # 在 _scan_once 文档串之后插入跳过逻辑
    doc_end = s.index('"""', s.index('"""', idx) + 3) + 3
    s = s[:doc_end] + '''
        if _api_mode_is_third_party():
            logger.info("[ltm] third-party mode: memory scan skipped")
            return
''' + s[doc_end:]
    p.write_text(s, encoding="utf-8")
    print("ltm guard inserted")
else:
    print("already patched")
