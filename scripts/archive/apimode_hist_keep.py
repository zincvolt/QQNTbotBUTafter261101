from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")
s = p.read_text(encoding="utf-8")
old = '''        if state.get("save_token") and getattr(req, "contexts", None):
            # 省 token：只留最近 10 条上下文，长对话不再整段回放
            if len(req.contexts) > 10:
                req.contexts = req.contexts[-10:]'''
new = '''        if state.get("save_token") and getattr(req, "contexts", None):
            # 省 token：保留条数由控制台滑块决定
            keep = int(state.get("history_keep", 10) or 10)
            if len(req.contexts) > keep:
                req.contexts = req.contexts[-keep:]'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("apimode 历史条数可配置")
else:
    print("MISS")
