from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

old = '''        req.system_prompt = (req.system_prompt or "") + STRICT_HINT'''
new = '''        # 主模型是纯文本的：把图片转成文字，别让 9B 收到 image 参数（会 500）
        if req.image_urls:
            logger.info(f"[peer] stripped {len(req.image_urls)} image(s) from request")
            req.image_urls = []

        req.system_prompt = (req.system_prompt or "") + STRICT_HINT'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("image strip added")
else:
    print("pattern missing")
