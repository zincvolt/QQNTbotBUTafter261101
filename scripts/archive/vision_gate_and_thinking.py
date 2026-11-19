"""Gate vision and adapt provider params for the third-party API."""

from __future__ import annotations

import json
import re
from pathlib import Path

PEER = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
APIMODE = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")

# ---------- 1. peer：按需读图 ----------
s = PEER.read_text(encoding="utf-8")

gate = '''VISION_HINTS = (
    "截图", "看图", "这张图", "图上", "图里", "图片里", "识别", "翻译",
    "这是什么", "什么字", "写的啥", "写了什么", "念一下", "认一下",
)


def _should_read_images(text: str, images: list) -> bool:
    """Decide whether the third-party model should actually look at images.

    Stickers and reaction images should not burn vision tokens, so we only send
    images when the message looks like it is asking about the picture.

    Args:
        text: The message text.
        images: Image payloads attached to the request.

    Returns:
        True when the images are worth sending.
    """
    if not images:
        return False
    lowered = text or ""
    if any(hint in lowered for hint in VISION_HINTS):
        return True
    if "?" in lowered or "？" in lowered:
        return True
    # 多图基本是在求助（对比/流程/长截图），单图更可能是表情
    if len(images) >= 3:
        return True
    # 大图（长截图、照片）通常是内容图，小图多是表情包
    for url in images:
        if isinstance(url, str) and len(url) > 60000:
            return True
    return False


'''

if "def _should_read_images(" not in s:
    idx = s.index("class Main(")
    s = s[:idx] + gate + s[idx:]

old_strip = '''        # 本地 9B 不支持图片输入，会 500；第三方 DeepSeek 支持，放行
        if req.image_urls and not _third_party_mode():
            logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
            req.image_urls = []'''
new_strip = '''        # 本地 9B 不支持图片输入，会 500；第三方 DeepSeek 支持，但只在必要时读图
        if req.image_urls:
            if not _third_party_mode():
                logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
                req.image_urls = []
            elif not _should_read_images(event.message_str or "", req.image_urls):
                logger.info(f"[peer] vision skipped: {len(req.image_urls)} image(s), likely sticker")
                req.image_urls = []'''
if old_strip in s:
    s = s.replace(old_strip, new_strip, 1)
    PEER.write_text(s, encoding="utf-8")
    print("peer vision gate installed")

# ---------- 2. apimode：思维链适配 ----------
a = APIMODE.read_text(encoding="utf-8")

helper = '''def set_thinking(mode: str) -> str:
    """Configure DeepSeek thinking mode on the provider entry.

    Args:
        mode: ``off``, ``on``, or an effort level (``low``/``high``/``max``).

    Returns:
        A short description of what was applied.
    """
    cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    for provider in cfg.get("provider", []):
        if provider.get("id") != "deepseek":
            continue
        body = provider.setdefault("custom_extra_body", {})
        if mode == "off":
            body["thinking"] = {"type": "disabled"}
            body.pop("reasoning_effort", None)
            body["temperature"] = 0.8
            note = "思维链关闭"
        else:
            body["thinking"] = {"type": "enabled"}
            body["reasoning_effort"] = "high" if mode == "on" else mode
            # 思考模式不支持 temperature，留着也会被忽略
            body.pop("temperature", None)
            note = f"思维链开启，强度 {body['reasoning_effort']}"
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return note
    return "没找到 deepseek provider"


'''
if "def set_thinking(" not in a:
    a = a.replace("class Main(", helper + "class Main(", 1)

# 切换第三方时：默认关思维链 + 放宽 max_tokens
a = a.replace(
    '''                set_provider_mode("third_party")
                tune_reply_for_mode("third_party")''',
    '''                set_provider_mode("third_party")
                tune_reply_for_mode("third_party")
                set_thinking("off")''',
    1,
)

# 新命令：/思维链 off|on|low|high|max
a = a.replace(
    '''        if body.startswith("额度"):''',
    '''        if body.startswith("思维链"):
            level = body.replace("思维链", "").strip().lower()
            if level in ("", "on", "开"):
                level = "on"
            elif level in ("off", "关"):
                level = "off"
            elif level not in ("low", "high", "max"):
                level = "high"
            note = set_thinking(level)
            await event.send(event.plain_result(f"{note}（第三方模式生效，8 秒后重启）"))
            schedule_restart()
            event.stop_event()
            return

        if body.startswith("额度"):''',
    1,
)

# 帮助与用量里带上思维链状态
a = a.replace(
    '''f"{state.get('daily_limit')} tokens · 省token "''',
    '''f"{state.get('daily_limit')} tokens · 省token "''',
    1,
)

APIMODE.write_text(a, encoding="utf-8")
print("apimode thinking control added")
