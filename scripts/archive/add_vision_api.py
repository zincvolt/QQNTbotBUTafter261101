from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

old = '''    groups = cfg.get("platform_settings", {}).get("groups", {}).get("id", [])'''
new = '''    whitelist = (
        cfg.get("platform_settings", {}).get("id_whitelist", []) or []
    )
    groups = [x for x in whitelist if str(x).isdigit()]'''
if old in s:
    s = s.replace(old, new, 1)
    print("groups 解析修正")

vm = '''VISION_STATE = ROOT / "data" / "vision_mode.json"
VL_PORT = 8085


def read_vision_state() -> dict:
    """Return the vision mode settings.

    Returns:
        Dict with mode, port and model.
    """
    try:
        data = json.loads(VISION_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    data.setdefault("mode", "local")
    data.setdefault("port", VL_PORT)
    data.setdefault("model", "Qwen3VL-4B-Instruct")
    return data


@app.get("/api/visionmode")
def get_visionmode() -> JSONResponse:
    """Return the vision backend choice and whether the local VL is running."""
    state = read_vision_state()
    return JSONResponse(
        {
            "mode": state["mode"],
            "port": state["port"],
            "model": state["model"],
            "up": port_open(int(state["port"])),
            "api_mode": api_mode(),
        }
    )


@app.post("/api/visionmode")
async def save_visionmode(request: Request) -> JSONResponse:
    """Switch the vision backend: local, third_party or off."""
    body = await request.json()
    mode = str(body.get("mode", "")).strip()
    if mode not in ("local", "third_party", "off"):
        return JSONResponse({"ok": False, "msg": "模式只能是 local / third_party / off"})
    state = read_vision_state()
    state["mode"] = mode
    VISION_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    names = {"local": "本地 VL", "third_party": "第三方看图", "off": "不读图"}
    return JSONResponse({"ok": True, "msg": f"已切换：{names[mode]}（立即生效）"})


@app.post("/api/vl/{action}")
async def vl_control(action: str) -> JSONResponse:
    """Start or stop the local VL server."""
    if action not in ("start", "stop"):
        return JSONResponse({"ok": False, "msg": "只支持 start / stop"})
    if action == "start":
        if port_open(VL_PORT):
            return JSONResponse({"ok": True, "msg": "本地 VL 已在运行"})
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ROOT / "scripts" / "start-vl.ps1")],
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        return JSONResponse({"ok": True, "msg": "本地 VL 启动中，约 20 秒后可用"})
    for pid in _pids_on_port(VL_PORT):
        try:
            import psutil

            psutil.Process(pid).terminate()
        except Exception:  # noqa: BLE001
            continue
    return JSONResponse({"ok": True, "msg": "本地 VL 已停止"})


def _pids_on_port(port: int) -> list[int]:
    """Return PIDs listening on a port (empty when psutil is unavailable).

    Args:
        port: TCP port.

    Returns:
        List of process ids.
    """
    try:
        import psutil
    except ImportError:
        return []
    pids: list[int] = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            if conn.pid and conn.pid not in pids:
                pids.append(conn.pid)
    return pids


'''
if "/api/visionmode" not in s:
    s = s.replace('@app.get("/api/guard")', vm + '@app.get("/api/guard")', 1)
    p.write_text(s, encoding="utf-8")
    print("识图接口已加")
