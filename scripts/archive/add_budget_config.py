from pathlib import Path
import json

# 1) @ 消息也计入预算
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")
old = '''        umo = event.unified_msg_origin
        cfg = self.cfg(event)
        final_message = await self._format_message(event, cfg)'''
new = '''        umo = event.unified_msg_origin
        cfg = self.cfg(event)
        # @ 它的消息一定会回，也要计入预算
        if event.is_at_or_wake_command:
            self._note_reply(umo)
        final_message = await self._format_message(event, cfg)'''
if old in s and "一定会回，也要计入预算" not in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("at-mention counted")

# 2) 配置默认值
rp = Path(r"D:\QQNTBOT\data\reply.json")
d = json.loads(rp.read_text(encoding="utf-8"))
d.setdefault("reply_budget", 8)
d.setdefault("reply_budget_minutes", 10)
rp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(d, ensure_ascii=False))
