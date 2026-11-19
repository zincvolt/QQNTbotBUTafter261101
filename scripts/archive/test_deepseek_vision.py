import base64, json, io
from pathlib import Path
import httpx
from PIL import Image, ImageDraw

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
src_cfg = [s for s in cfg["provider_sources"] if s["id"] == "deepseek_source"][0]
key = (src_cfg.get("key") or [src_cfg.get("api_key")])[0]
base = src_cfg.get("api_base", "https://api.deepseek.com/v1")

img = Image.new("RGB", (240, 120), (220, 30, 30))
ImageDraw.Draw(img).text((10, 50), "HELLO-42", fill=(255, 255, 255))
buf = io.BytesIO(); img.save(buf, format="PNG")
data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

payload = {
    "model": "deepseek-flash",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "图里是什么颜色？上面写的字是什么？只回答这两点。"},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]}],
    "max_tokens": 60,
    "thinking": {"type": "disabled"},
}
r = httpx.post(f"{base}/chat/completions",
               headers={"Authorization": f"Bearer {key}"},
               json=payload, timeout=90)
print("status", r.status_code)
print(r.text[:500])
