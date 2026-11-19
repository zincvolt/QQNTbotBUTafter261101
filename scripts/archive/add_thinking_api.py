from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

block = '''@app.get("/api/thinking")
def get_thinking() -> JSONResponse:
    """Return the thinking switch and token budget."""
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    body = cfg["provider"][0].get("custom_extra_body", {})
    kwargs = body.get("chat_template_kwargs", {}) or {}
    return JSONResponse(
        {
            "enable": bool(kwargs.get("enable_thinking", False)),
            "budget": int(body.get("max_tokens", 80)),
        }
    )


@app.post("/api/thinking")
async def save_thinking(request: Request) -> JSONResponse:
    """Toggle the model thinking chain and set its token budget (restarts AstrBot)."""
    body = await request.json()
    enable = bool(body.get("enable"))
    try:
        budget = int(body.get("budget", 800))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "msg": "预算格式不对"})
    budget = max(200, min(4000, budget))

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    extra = cfg["provider"][0].setdefault("custom_extra_body", {})
    extra["chat_template_kwargs"] = {"enable_thinking": enable}
    extra["max_tokens"] = budget if enable else min(budget, 120)
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    restart_bot()
    state = "开启" if enable else "关闭"
    return JSONResponse(
        {"ok": True, "msg": f"{state}思考链，预算 {budget} tokens，AstrBot 重启中"}
    )


@app.get("/api/reply")'''
s = s.replace('@app.get("/api/reply")', block, 1)
p.write_text(s, encoding="utf-8")
print("thinking api added")
