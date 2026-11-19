from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
old = '''        thinking = body.get("thinking") or {}
        enable = str(thinking.get("type", "disabled")) == "enabled"
        effort = str(body.get("reasoning_effort", "high"))
        budget_map = {"low": 600, "high": 1200, "max": 2000}
        return JSONResponse(
            {
                "enable": enable,
                "budget": budget_map.get(effort, int(body.get("max_tokens", 1200))),
                "mode": "third_party",
                "effort": effort,
            }
        )'''
new = '''        thinking = body.get("thinking") or {}
        enable = str(thinking.get("type", "disabled")) == "enabled"
        effort = str(body.get("reasoning_effort", "high"))
        budget_map = {"low": 600, "high": 1200, "max": 2000}
        budget = (
            budget_map.get(effort, int(body.get("max_tokens", 800)))
            if enable
            else int(body.get("max_tokens", 400))
        )
        return JSONResponse(
            {
                "enable": enable,
                "budget": budget,
                "mode": "third_party",
                "effort": effort if enable else "",
            }
        )'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("get_thinking 关闭时显示真实 max_tokens")
else:
    print("MISS")
