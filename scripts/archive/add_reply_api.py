from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

block = '''@app.get("/api/reply")
def get_reply() -> JSONResponse:
    """Return meme chance and text replacement rules."""
    data = read_json(REPLY_FILE, {"meme_chance": 0.3, "text_rules": []})
    return JSONResponse(
        {
            "meme_chance": float(data.get("meme_chance", 0.3)),
            "text_rules": data.get("text_rules", []),
        }
    )


@app.post("/api/reply")
async def save_reply(request: Request) -> JSONResponse:
    """Save meme chance and text rules. Picked up without a restart."""
    body = await request.json()
    try:
        chance = round(float(body.get("meme_chance", 0.3)), 2)
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "msg": "概率格式不对"})
    if not 0.0 <= chance <= 1.0:
        return JSONResponse({"ok": False, "msg": "概率要在 0~1 之间"})
    rules = []
    for item in body.get("text_rules", []):
        find = str(item.get("find", ""))
        to = str(item.get("to", ""))
        if find:
            rules.append({"find": find, "to": to})
    write_json(REPLY_FILE, {"meme_chance": chance, "text_rules": rules})
    return JSONResponse(
        {"ok": True, "msg": f"已保存：表情概率 {int(chance * 100)}%，替换规则 {len(rules)} 条"}
    )


@app.get("/api/sampling")'''

s = s.replace('@app.get("/api/sampling")', block, 1)
p.write_text(s, encoding="utf-8")
print("added reply api")
