from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
old = '''        if req.image_urls:
            logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
            req.image_urls = []'''
new = '''        # 本地 9B 不支持图片输入，会 500；第三方 DeepSeek 支持，放行
        if req.image_urls and not _third_party_mode():
            logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
            req.image_urls = []'''
if old in s:
    s = s.replace(old, new, 1)
    helper = '''def _third_party_mode() -> bool:
    """Return True when the bot is switched to the third-party API.

    Returns:
        Whether ``data/api_mode.json`` says ``third_party``.
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
    if "_third_party_mode" not in s.split("if req.image_urls")[0]:
        anchor = "class Main("
        idx = s.index(anchor)
        s = s[:idx] + helper + s[idx:]
    p.write_text(s, encoding="utf-8")
    print("peer image strip now mode-aware")
else:
    print("MISS")
