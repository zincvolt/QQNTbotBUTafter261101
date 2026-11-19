from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")

old = '''    summon = [str(x).strip() for x in body.get("summon", []) if str(x).strip()]
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
            "reply_budget": int(body.get("reply_budget", 8)),
            "reply_budget_minutes": float(body.get("reply_budget_minutes", 10)),
            "text_rules": rules,
        },
    )'''
new = '''    # 合并保存：只覆盖这次真的传上来的字段，避免空值把旧配置冲掉
    current = read_json(REPLY_FILE, {})
    summon = [str(x).strip() for x in body.get("summon", []) if str(x).strip()]
    if summon:
        judge_cfg = read_json(JUDGE_FILE, {})
        judge_cfg["summon"] = summon
        write_json(JUDGE_FILE, judge_cfg)

    current["meme_chance"] = chance
    current["reply_chance"] = reply_chance
    if "history_minutes" in body:
        current["history_minutes"] = float(body["history_minutes"])
    if "reply_budget" in body:
        current["reply_budget"] = int(body["reply_budget"])
    if "reply_budget_minutes" in body:
        current["reply_budget_minutes"] = float(body["reply_budget_minutes"])
    # 正则规则：空列表视为"这次没传"，只有显式 clear_rules 才清空
    if rules or body.get("clear_rules"):
        current["text_rules"] = rules
    current.setdefault("history_minutes", 30)
    current.setdefault("reply_budget", 8)
    current.setdefault("reply_budget_minutes", 10)
    current.setdefault("text_rules", [{"pattern": "。(?=\\\\s|$)", "to": "~"}])
    write_json(REPLY_FILE, current)'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("merge save")
else:
    print("pattern missing")
