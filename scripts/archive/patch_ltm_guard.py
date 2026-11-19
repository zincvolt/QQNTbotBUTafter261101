from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py")
s = p.read_text(encoding="utf-8")
guard = '''    async def _scan_once(self):
        """One scan pass over recent group messages."""'''
if "_api_mode_is_third_party" not in s:
    helper = '''def _api_mode_is_third_party() -> bool:
    """Return True when the bot is running on the third-party API.

    Local big models must not be touched in that mode, so memory extraction is
    skipped entirely.
    """
    import json
    from pathlib import Path as _P

    state = _P(r"D:\\QQNTBOT\\data\\api_mode.json")
    if not state.exists():
        return False
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("mode") == "third_party"
    except Exception:
        return False


'''
    if guard in s:
        s = s.replace(guard, helper + guard, 1)
        s = s.replace(guard, guard + '''
        if _api_mode_is_third_party():
            logger.info("[ltm] third-party mode: memory scan skipped")
            return''', 1)
        p.write_text(s, encoding="utf-8")
        print("ltm guard added")
    else:
        print("ltm 扫描入口没找到")
