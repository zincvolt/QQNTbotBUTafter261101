from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

# GET 带上 summon
s = s.replace(
    '''            "reply_chance": float(data.get("reply_chance", 1.0)),
            "text_rules": data.get("text_rules", []),''',
    '''            "reply_chance": float(data.get("reply_chance", 1.0)),
            "history_minutes": float(data.get("history_minutes", 30)),
            "summon": read_json(JUDGE_FILE, {}).get("summon", []),
            "text_rules": data.get("text_rules", []),''',
)
# POST 保存 summon（写进 judge.json，保留其它字段）
s = s.replace(
    '''    write_json(
        REPLY_FILE,
        {
            "meme_chance": chance,
            "reply_chance": reply_chance,
            "text_rules": rules,
        },
    )''',
    '''    summon = [str(x).strip() for x in body.get("summon", []) if str(x).strip()]
    if summon:
        judge_cfg = read_json(JUDGE_FILE, {})
        judge_cfg["summon"] = summon
        write_json(JUDGE_FILE, judge_cfg)
    write_json(
        REPLY_FILE,
        {
            "meme_chance": chance,
            "reply_chance": reply_chance,
            "history_minutes": float(body.get("history_minutes", 30)),
            "text_rules": rules,
        },
    )''',
)
p.write_text(s, encoding="utf-8")
print("api patched:", "summon" in s)
