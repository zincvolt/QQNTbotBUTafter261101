# -*- coding: utf-8 -*-
"""QQNTbot 外部看门狗 —— AstrBot 挂了也能报信

监控（每 30s 一轮）：
  1. AstrBot 面板端口 6185 是否存活（主判据）
  2. astrbot.log 是否停更（端口活着但 >30min 没写日志 = 疑似卡死，报一次）

报警通道：NapCat HTTP API（127.0.0.1:6198，已在 onebot11 配置里启用，
本机回环监听、无鉴权，只用于本机内部调用），直接 POST /send_private_msg
私信创造者。AstrBot 死了不影响这条路。

防轰炸：挂掉报一次，之后每 30min 重报一次；恢复时报一次。
标准库实现，无任何 AstrBot 依赖。

用法：python scripts/watchdog.py（start-all.ps1 已带起）
"""
import socket
import sys
import time
import urllib.request
from pathlib import Path

CREATOR = 1154487120
NAPCAT_HTTP = "http://127.0.0.1:6198"
ASTBOT_PORT = 6185
LOG_FILE = Path(r"D:\QQNTBOT\apps\AstrBot\data\logs\astrbot.log")
CHECK_INTERVAL = 30          # 秒
RE_ALERT_EVERY = 30 * 60     # 挂着时每 30min 重报
STALE_AFTER = 30 * 60        # 日志超过 30min 没更新视为卡死疑点


def send_private(uid: int, text: str) -> bool:
    try:
        req = urllib.request.Request(
            NAPCAT_HTTP + "/send_private_msg",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": uid, "message": text}).encode(),
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:  # noqa: BLE001
        print(f"[watchdog] send failed: {e}", file=sys.stderr)
        return False


def port_alive(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return True
    except OSError:
        return False


def log_stale() -> bool:
    try:
        return time.time() - LOG_FILE.stat().st_mtime > STALE_AFTER
    except OSError:
        return True


def main() -> None:
    print("[watchdog] started: astrbot:6185 + log freshness -> creator dm")
    down_since = 0.0
    last_alert = 0.0
    stale_alerted = False
    while True:
        alive = port_alive(ASTBOT_PORT)
        now = time.time()
        if not alive:
            if down_since == 0.0:
                down_since = now
            if now - last_alert > RE_ALERT_EVERY:
                dur = int((now - down_since) / 60)
                send_private(
                    CREATOR,
                    f"🔴 看门狗：AstrBot(6185) 无响应 {dur} 分钟了，去看看面板。"
                    if dur
                    else "🔴 看门狗：AstrBot(6185) 刚刚无响应了。",
                )
                last_alert = now
        else:
            if down_since:
                send_private(CREATOR, "🟢 看门狗：AstrBot 恢复在线了。")
                down_since = 0.0
                last_alert = 0.0
            if log_stale() and not stale_alerted:
                if send_private(
                    CREATOR,
                    f"⚠ 看门狗：AstrBot 端口活着，但日志已 {STALE_AFTER // 60} 分钟没更新，疑似卡死。",
                ):
                    stale_alerted = True
            elif not log_stale():
                stale_alerted = False
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
