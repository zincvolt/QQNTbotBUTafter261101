"""Add optimization presets and the editable LTM prompt to the dashboard."""

from pathlib import Path

APP = Path(r"D:\QQNTBOT\dashboard\app.py")
s = APP.read_text(encoding="utf-8")

block = '''PROFILE_DEFAULT_RULE = {"pattern": "。(?=\\\\s|$|[（(\\\\[【「『])", "to": "~"}
LTM_PROMPT = ROOT / "data" / "ltm_prompt.txt"


@app.get("/api/profile")
def get_profile() -> JSONResponse:
    """Return which local-only optimizations are active."""
    cfg = json.loads(REPLY.read_text(encoding="utf-8"))
    rules = cfg.get("text_rules") or []
    return JSONResponse(
        {
            "mode": api_mode(),
            "meme_on": float(cfg.get("meme_chance", 0)) > 0,
            "rules_on": bool(rules),
            "meme_chance": float(cfg.get("meme_chance", 0)),
            "rule_count": len(rules),
            "reply_chance": float(cfg.get("reply_chance", 0.3)),
        }
    )


@app.post("/api/profile")
async def save_profile(request: Request) -> JSONResponse:
    """Apply a local/third-party preset or toggle individual optimizations."""
    body = await request.json()
    cfg = json.loads(REPLY.read_text(encoding="utf-8"))
    preset = str(body.get("preset", "")).strip()

    if preset == "local":
        cfg["meme_chance"] = float(body.get("meme_chance", 0.3) or 0.3)
        if not (cfg.get("text_rules") or []):
            cfg["text_rules"] = [dict(PROFILE_DEFAULT_RULE)]
        msg = "已套用本地优化：表情附带 + 文本替换"
    elif preset == "third":
        cfg["meme_chance"] = 0
        cfg["text_rules"] = []
        msg = "已套用第三方精简：关闭表情附带与文本替换"
    else:
        if "meme_on" in body:
            cfg["meme_chance"] = 0.3 if body["meme_on"] else 0
        if "rules_on" in body:
            cfg["text_rules"] = [dict(PROFILE_DEFAULT_RULE)] if body["rules_on"] else []
        msg = "已更新本地优化开关"

    REPLY.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True, "msg": msg})


@app.get("/api/ltm/prompt")
def get_ltm_prompt() -> JSONResponse:
    """Return the memory extraction prompt."""
    try:
        text = LTM_PROMPT.read_text(encoding="utf-8")
    except OSError:
        text = ""
    return JSONResponse({"text": text, "has_placeholders": "{user}" in text and "{bot}" in text})


@app.post("/api/ltm/prompt")
async def save_ltm_prompt(request: Request) -> JSONResponse:
    """Save the memory extraction prompt (requires {user} and {bot})."""
    body = await request.json()
    text = str(body.get("text", ""))
    if "{user}" not in text or "{bot}" not in text:
        return JSONResponse({"ok": False, "msg": "必须同时包含 {user} 和 {bot} 占位符"})
    LTM_PROMPT.write_text(text, encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "已保存，下一轮提取生效"})


'''

if "/api/profile" not in s:
    s = s.replace('@app.get("/api/guard")', block + '@app.get("/api/guard")', 1)
    APP.write_text(s, encoding="utf-8")
    print("app.py: profile / ltm prompt 接口已加")
else:
    print("已存在")
