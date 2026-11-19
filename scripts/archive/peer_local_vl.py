"""Wire the local VL captioning path into the peer plugin."""

from pathlib import Path

PEER = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = PEER.read_text(encoding="utf-8")

helpers = '''def _vision_mode() -> str:
    """Return the configured vision backend: local, third_party or off.

    Returns:
        The mode string from ``data/vision_mode.json``.
    """
    import json
    from pathlib import Path as _Path

    state = _Path(r"D:\\QQNTBOT\\data\\vision_mode.json")
    if not state.exists():
        return "local"
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("mode", "local")
    except Exception:  # noqa: BLE001
        return "local"


async def _caption_local(url: str) -> str:
    """Caption one image with the local VL server.

    Args:
        url: Data URL or local file path of the image.

    Returns:
        Caption text, or an explicit unavailable marker.
    """
    import base64
    from pathlib import Path as _Path

    import httpx

    port = 8085
    state_path = _Path(r"D:\\QQNTBOT\\data\\vision_mode.json")
    try:
        import json as _json

        port = int(_json.loads(state_path.read_text(encoding="utf-8")).get("port", 8085))
    except Exception:  # noqa: BLE001
        pass

    if not url.startswith("data:"):
        try:
            raw = _Path(url).read_bytes()
        except OSError:
            return "（读图能力不可用）"
        url = "data:image/png;base64," + base64.b64encode(raw).decode()

    payload = {
        "model": "Qwen3VL-4B-Instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "用中文简短描述这张图：有文字就照抄要点，再说画面是什么，不超过 80 字。"},
                {"type": "image_url", "image_url": {"url": url}},
            ],
        }],
        "max_tokens": 160,
        "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"http://127.0.0.1:{port}/v1/chat/completions", json=payload
            )
            resp.raise_for_status()
            text = (resp.json()["choices"][0]["message"].get("content") or "").strip()
        return text or "（读图能力不可用）"
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[peer] local VL failed: {exc}")
        return "（读图能力不可用）"


'''

if "_caption_local" not in s:
    idx = s.index("class Main(")
    s = s[:idx] + helpers + s[idx:]

old = '''        if req.image_urls:
            if not _third_party_mode():
                logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
                req.image_urls = []
            elif not _should_read_images(event.message_str or "", req.image_urls):
                logger.info(f"[peer] vision skipped: {len(req.image_urls)} image(s), likely sticker")
                req.image_urls = []'''

new = '''        if req.image_urls:
            if not _third_party_mode():
                logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
                req.image_urls = []
            else:
                mode = _vision_mode()
                if mode == "off" or not _should_read_images(
                    event.message_str or "", req.image_urls
                ):
                    logger.info(f"[peer] vision skipped ({mode}): {len(req.image_urls)} image(s)")
                    req.image_urls = []
                elif mode == "local":
                    # 本地 VL 转文字，第三方模型完全接触不到图片
                    captions = []
                    for url in req.image_urls[:2]:
                        captions.append(await _caption_local(url))
                    req.prompt = (req.prompt or "") + "\\n[图片内容] " + " / ".join(captions)
                    req.image_urls = []
                    logger.info(f"[peer] local VL captioned {len(captions)} image(s)")
                # mode == third_party: 原样发给 DeepSeek 看'''

if old in s:
    s = s.replace(old, new, 1)
    PEER.write_text(s, encoding="utf-8")
    print("peer local VL path wired")
else:
    print("MISS")
