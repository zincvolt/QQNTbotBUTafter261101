"""Unload local models when switching to third-party, and reboot them when back."""

from pathlib import Path

APIMODE = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")
s = APIMODE.read_text(encoding="utf-8")

helper = '''LOCAL_PORTS = (8080, 8083, 8085)   # 聊天 / OCR / 识图；判官 8082 与嵌入 8097 保留
LOCAL_SCRIPTS = {
    8080: r"D:\\LLM\\scripts\\start-router.ps1",
    8083: r"D:\\QQNTBOT\\scripts\\start-ocr.ps1",
    8085: r"D:\\LLM\\scripts\\start-vl.ps1",
}


def _port_pids(port: int) -> list[int]:
    """Return PIDs listening on a local port.

    Args:
        port: TCP port to inspect.

    Returns:
        List of process ids.
    """
    import psutil

    pids: list[int] = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            if conn.pid and conn.pid not in pids:
                pids.append(conn.pid)
    return pids


def unload_local_models() -> list[str]:
    """Stop the local chat, OCR and vision servers.

    Returns:
        Names of the ports that were shut down.
    """
    import psutil

    stopped: list[str] = []
    for port in LOCAL_PORTS:
        for pid in _port_pids(port):
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                stopped.append(f"{port}({proc.name()})")
            except Exception:  # noqa: BLE001
                continue
    logger.info(f"[apimode] unloaded local models: {stopped or 'none'}")
    return stopped


def start_local_models() -> None:
    """Start the local chat, OCR and vision servers again (detached)."""
    import subprocess

    for port, script in LOCAL_SCRIPTS.items():
        if _port_pids(port):
            continue
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    logger.info("[apimode] requested local model startup")


'''

if "def unload_local_models(" not in s:
    anchor = "def set_provider_mode("
    s = s.replace(anchor, helper + anchor, 1)
    print("helper 已插入")

# 切第三方：卸载本地；切回本地：拉起
s = s.replace(
    '''                set_provider_mode("third_party")
                tune_reply_for_mode("third_party")
                set_thinking("off")''',
    '''                set_provider_mode("third_party")
                tune_reply_for_mode("third_party")
                set_thinking("off")
                stopped = unload_local_models()''',
    1,
)
s = s.replace(
    '''                await event.send(event.plain_result(
                    "已切到第三方 API，8 秒后重启生效；本地大模型已停用"
                ))''',
    '''                detail = "、".join(stopped) if stopped else "无运行中的本地模型"
                await event.send(event.plain_result(
                    f"已切到第三方 API，8 秒后重启生效；已卸载本地模型：{detail}"
                ))''',
    1,
)
s = s.replace(
    '''                set_provider_mode("local")
                tune_reply_for_mode("local")''',
    '''                set_provider_mode("local")
                tune_reply_for_mode("local")
                start_local_models()''',
    1,
)

APIMODE.write_text(s, encoding="utf-8")
print("apimode 卸载/拉起逻辑已加")
