"""一图流文字卡片渲染——长文本输出（帮助列表、权限表等）改为单张图卡。

参考 astrbot_plugin_furcon 的绘卡风格：暗底 + CJK 字体 + PIL。
各插件用法（单拎也能用，不依赖 access 插件加载）：

    from card_render import render_text_card   # 或自己拷一份
    path = render_text_card("标题", ["第一行", "第二行"], footer="脚注")
    yield event.image_result(str(path))

缓存：生成前先算内容 SHA256，文件名即内容哈希——内容没变直接复用，不重新渲染。
短确认语（"好了 XX 可以私聊了"）仍用 plain_result，只把长列表/帮助改图。
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------- 字体（与 furcon 同源，CJK 优先） ----------

_BUNDLED = (
    Path(__file__).resolve().parent.parent
    / "astrbot_plugin_furcon"
    / "fonts"
    / "NotoSansSC-Bold.ttf"
)
_FONT_CANDIDATES = [
    str(_BUNDLED),
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------- 调色板（与 furcon 暗色卡片一致） ----------

BG = (24, 26, 32)
PANEL = (34, 38, 48)
TITLE_C = (220, 224, 234)
HEADER_C = (120, 180, 255)
BODY_C = (200, 204, 214)
DIM_C = (120, 126, 140)
ACCENT_C = (255, 200, 80)

# ---------- 缓存目录 ----------

CARD_DIR = Path(r"D:\QQNTBOT\data\access_cards")


def render_text_card(
    title: str,
    lines: list[str],
    footer: str = "",
) -> Path:
    """渲染一张文字卡，返回 PNG 路径。

    lines 支持前缀标记：
      "## xxx"   → 小节标题（蓝色加粗）
      "! xxx"    → 重点行（黄色）
      "> xxx"    → 注释行（灰色小字）
      其余        → 正文

    缓存策略：生成前算内容 SHA256，文件名 = 标题 + 哈希前 12 位。
    内容没变 → 文件已存在 → 直接跳过不重新渲染。
    """
    # SHA256 内容指纹：内容没变就不重画
    content_blob = (title + "\x00" + "\n".join(lines) + "\x00" + footer).encode("utf-8")
    content_sha = hashlib.sha256(content_blob).hexdigest()[:12]
    safe = re.sub(r"[^0-9A-Za-z_-]+", "_", title)[:16].strip("_") or "x"
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    path = CARD_DIR / f"{safe}_{content_sha}.png"
    if path.exists():
        return path  # SHA 一致 → 内容没变，跳过渲染

    # --- 字体 ---
    f_title = _font(36)
    f_header = _font(26)
    f_body = _font(22)
    f_dim = _font(18)

    # --- 排版：先量高度 ---
    pad_x, pad_y = 48, 40
    line_gap = 10
    wrapped: list[tuple[str, str]] = []  # (text, style)  style: header/body/dim/hi

    def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        """简单换行：每字累加宽度，超了就断。"""
        if not text:
            return [""]
        out, cur, cur_w = [], "", 0
        probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        for ch in text:
            w = probe.textlength(ch, font=font)
            if cur_w + w > max_w and cur:
                out.append(cur)
                cur, cur_w = ch, w
            else:
                cur += ch
                cur_w += w
        if cur:
            out.append(cur)
        return out

    width = 800
    max_text_w = width - pad_x * 2

    for raw in lines:
        if raw.startswith("## "):
            text = raw[3:].strip()
            wrapped.append((text, "header"))
        elif raw.startswith("! "):
            text = raw[2:].strip()
            for w in _wrap(text, f_body, max_text_w):
                wrapped.append((w, "hi"))
        elif raw.startswith("> "):
            text = raw[2:].strip()
            for w in _wrap(text, f_dim, max_text_w):
                wrapped.append((w, "dim"))
        else:
            text = raw.strip()
            if not text:
                wrapped.append(("", "gap"))
            else:
                for w in _wrap(text, f_body, max_text_w):
                    wrapped.append((w, "body"))

    # 量总高度
    y = pad_y + 48 + 16  # 标题区
    for text, style in wrapped:
        if style == "gap":
            y += 8
        elif style == "header":
            y += 36 + line_gap
        elif style == "dim":
            y += 24 + line_gap
        else:
            y += 30 + line_gap
    if footer:
        y += 40
    height = y + pad_y

    # --- 绘制 ---
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # 标题
    draw.text((pad_x, pad_y), title, font=f_title, fill=TITLE_C)
    # 标题下划线
    draw.line(
        (pad_x, pad_y + 50, width - pad_x, pad_y + 50),
        fill=(70, 74, 84),
        width=2,
    )

    y = pad_y + 66
    for text, style in wrapped:
        if style == "gap":
            y += 8
        elif style == "header":
            y += 8
            draw.text((pad_x, y), text, font=f_header, fill=HEADER_C)
            y += 36 + line_gap
        elif style == "dim":
            draw.text((pad_x, y), text, font=f_dim, fill=DIM_C)
            y += 24 + line_gap
        elif style == "hi":
            draw.text((pad_x, y), text, font=f_body, fill=ACCENT_C)
            y += 30 + line_gap
        else:
            draw.text((pad_x, y), text, font=f_body, fill=BODY_C)
            y += 30 + line_gap

    if footer:
        draw.text((pad_x, height - pad_y + 4), footer, font=f_dim, fill=DIM_C)

    img.save(path)
    return path
