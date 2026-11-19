from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

# GET 增加 reply_chance
s = s.replace(
    '''            "meme_chance": float(data.get("meme_chance", 0.3)),
            "text_rules": data.get("text_rules", []),''',
    '''            "meme_chance": float(data.get("meme_chance", 0.3)),
            "reply_chance": float(data.get("reply_chance", 1.0)),
            "text_rules": data.get("text_rules", []),''',
)
# POST 保存 reply_chance
s = s.replace(
    '''    rules = []
    for item in body.get("text_rules", []):''',
    '''    try:
        reply_chance = round(float(body.get("reply_chance", 1.0)), 2)
    except (TypeError, ValueError):
        reply_chance = 1.0
    reply_chance = max(0.0, min(1.0, reply_chance))
    rules = []
    for item in body.get("text_rules", []):''',
)
s = s.replace(
    '''    write_json(REPLY_FILE, {"meme_chance": chance, "text_rules": rules})
    return JSONResponse(
        {"ok": True, "msg": f"已保存：表情概率 {int(chance * 100)}%，替换规则 {len(rules)} 条"}
    )''',
    '''    write_json(
        REPLY_FILE,
        {
            "meme_chance": chance,
            "reply_chance": reply_chance,
            "text_rules": rules,
        },
    )
    return JSONResponse(
        {
            "ok": True,
            "msg": (
                f"已保存：回复概率 {int(reply_chance * 100)}%、"
                f"表情概率 {int(chance * 100)}%、替换规则 {len(rules)} 条"
            ),
        }
    )''',
)
p.write_text(s, encoding="utf-8")
print("api patched")
