from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

block = '''@app.get("/api/sampling")
def get_sampling() -> JSONResponse:
    """Return the sampling parameters used for chat."""
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    body = cfg["provider"][0].get("custom_extra_body", {})
    return JSONResponse(
        {
            "temperature": float(body.get("temperature", 0.7)),
            "top_p": float(body.get("top_p", 0.9)),
            "repeat_penalty": float(body.get("repeat_penalty", 1.0)),
            "max_tokens": int(body.get("max_tokens", 90)),
        }
    )


@app.post("/api/sampling")
async def save_sampling(request: Request) -> JSONResponse:
    """Save sampling parameters and restart AstrBot so they take effect."""
    body = await request.json()
    try:
        temperature = round(float(body.get("temperature", 0.7)), 2)
        top_p = round(float(body.get("top_p", 0.9)), 2)
        repeat_penalty = round(float(body.get("repeat_penalty", 1.0)), 3)
        max_tokens = int(body.get("max_tokens", 90))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "msg": "参数格式不对"})

    if not 0.0 <= temperature <= 2.0:
        return JSONResponse({"ok": False, "msg": "温度要在 0~2 之间"})
    if not 1.0 <= repeat_penalty <= 2.0:
        return JSONResponse({"ok": False, "msg": "重复惩罚要在 1.0~2.0 之间"})

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    extra = cfg["provider"][0].setdefault("custom_extra_body", {})
    extra["temperature"] = temperature
    extra["top_p"] = top_p
    extra["repeat_penalty"] = repeat_penalty
    extra["max_tokens"] = max_tokens
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    restart_bot()
    return JSONResponse(
        {
            "ok": True,
            "msg": f"已保存：温度 {temperature}、重复惩罚 {repeat_penalty}，AstrBot 重启中",
        }
    )


@app.get("/api/contexts")'''

s = s.replace('@app.get("/api/contexts")', block, 1)
p.write_text(s, encoding="utf-8")
print("added sampling endpoints")
