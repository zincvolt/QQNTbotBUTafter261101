"""Serve a always-fresh QQ login QR pulled from NapCat's WebUI API.

Why: NapCat rotates the QR URL every couple of minutes. Writing it to a file
races with image viewers and goes stale, so we render it on demand instead.

Endpoints:
    GET /qr.png   current QR image
    GET /status   login status JSON
    GET /         tiny page that refreshes the QR every 3 seconds
"""

from __future__ import annotations

import hashlib
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import qrcode

WEBUI = Path(r"D:\QQNTBOT\apps\NapCat\config\webui.json")
PORT = 6191

PAGE = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8">
<title>QQ 登录</title>
<style>
 body{background:#14161c;color:#e8e8ee;font-family:system-ui;text-align:center;padding:24px}
 img{width:460px;height:460px;image-rendering:pixelated;background:#fff;border-radius:12px}
 #s{margin-top:12px;color:#9aa0ae}
</style>
<h2>QQ 登录二维码</h2>
<img id="q" src="/qr.png">
<div id="s">加载中…</div>
<script>
async function tick(){
  const r = await fetch('/status?_=' + Date.now());
  const d = await r.json();
  document.getElementById('s').textContent =
    d.isLogin ? '已登录：' + (d.uin || '') : ('等待扫码… ' + (d.loginPhase || ''));
  if (!d.isLogin) document.getElementById('q').src = '/qr.png?_=' + Date.now();
}
tick(); setInterval(tick, 3000);
</script></html>
"""


def webui_credential() -> str:
    """Return a NapCat WebUI credential.

    Returns:
        The credential string.

    Raises:
        RuntimeError: When the WebUI refuses the token.
    """
    cfg = json.loads(WEBUI.read_text(encoding="utf-8-sig"))
    token = cfg["token"]
    digest = hashlib.sha256((token + ".napcat").encode()).hexdigest()
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            f"http://127.0.0.1:{cfg['port']}/api/auth/login", json={"hash": digest}
        )
        data = resp.json()
    cred = (data.get("data") or {}).get("Credential")
    if not cred:
        raise RuntimeError(f"webui login failed: {data}")
    return cred


def login_status() -> dict:
    """Fetch the current login status from NapCat.

    Returns:
        The ``data`` object of the status response.
    """
    cfg = json.loads(WEBUI.read_text(encoding="utf-8-sig"))
    cred = webui_credential()
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            f"http://127.0.0.1:{cfg['port']}/api/QQLogin/CheckLoginStatus",
            headers={"Authorization": f"Bearer {cred}"},
            json={},
        )
    return resp.json().get("data") or {}


def render_qr(url: str) -> bytes:
    """Render a QR code PNG for the login URL.

    Args:
        url: The QQ login URL.

    Returns:
        PNG bytes.
    """
    img = qrcode.make(url).resize((460, 460))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    """Serve the QR page, image and status."""

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        """Handle GET requests for page, image and status."""
        try:
            if self.path.startswith("/status"):
                data = login_status()
                body = json.dumps({
                    "isLogin": data.get("isLogin"),
                    "loginPhase": data.get("loginPhase"),
                    "uin": (data.get("QQLoginInfo") or {}).get("uin", ""),
                    "error": data.get("loginError", ""),
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path.startswith("/qr.png"):
                data = login_status()
                if data.get("isLogin"):
                    body = b""
                else:
                    url = data.get("qrcodeurl") or ""
                    body = render_qr(url) if url else b""
                self.send_response(200 if body else 204)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if body:
                    self.wfile.write(body)
                return

            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:  # noqa: BLE001
            body = f"error: {exc}".encode()
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        """Silence per-request logging."""
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"QR page on http://127.0.0.1:{PORT}/")
    server.serve_forever()
