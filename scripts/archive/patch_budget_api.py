from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '''            "history_minutes": float(data.get("history_minutes", 30)),''',
    '''            "history_minutes": float(data.get("history_minutes", 30)),
            "reply_budget": int(data.get("reply_budget", 8)),
            "reply_budget_minutes": float(data.get("reply_budget_minutes", 10)),''',
)
s = s.replace(
    '''            "history_minutes": float(body.get("history_minutes", 30)),''',
    '''            "history_minutes": float(body.get("history_minutes", 30)),
            "reply_budget": int(body.get("reply_budget", 8)),
            "reply_budget_minutes": float(body.get("reply_budget_minutes", 10)),''',
)
p.write_text(s, encoding="utf-8")
print("api budget:", "reply_budget" in s)
