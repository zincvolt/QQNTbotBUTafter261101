from pathlib import Path

# 1) 历史块说明改成中文 + 强调说话人
p = Path(r"D:\QQNTBOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py")
s = p.read_text(encoding="utf-8")
old = '''GROUP_HISTORY_HEADER = (
    "<system_reminder>"
    "You are in a group chat. "
    "Belows are group chat context after your last reply:\\n"
    "--- BEGIN CONTEXT---\\n"
)'''
new = '''GROUP_HISTORY_HEADER = (
    "<system_reminder>"
    "你在一个 QQ 群里。下面是自你上次发言以来的群聊记录，"
    "每行开头的方括号是【说话人昵称/时间】，不同昵称是不同的人，"
    "不要把别人的话当成同一个人说的。\\n"
    "--- BEGIN CONTEXT---\\n"
)'''
if old in s:
    s = s.replace(old, new, 1)
    s = s.replace(
        'GROUP_HISTORY_FOOTER = "\\n--- END CONTEXT ---\\n</system_reminder>"',
        'GROUP_HISTORY_FOOTER = ('
        '"\\n--- END CONTEXT ---\\n"'
        "（以上每行方括号里是说话人，请区分不同的人；"
        "只有最后一条 user 消息是要你回的）"
        "</system_reminder>\"",
    )
    p.write_text(s, encoding="utf-8")
    print("历史块说明已改中文并强调说话人")
else:
    print("MISS header")

# 2) peer：当前消息前面加说话人昵称 + 系统提示说明
q = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
t = q.read_text(encoding="utf-8")
old2 = '''        req.system_prompt = (req.system_prompt or "") + STRICT_HINT'''
new2 = '''        # 群聊里给当前消息标上说话人，和历史块的格式保持一致
        group_id = str(event.get_group_id() or "")
        if group_id and not (req.prompt or "").startswith("["):
            nick = event.get_sender_name() or event.get_sender_id() or "群友"
            req.prompt = f"[{nick}]: {req.prompt}"
        if group_id:
            req.system_prompt = (
                (req.system_prompt or "")
                + "\\n\\n（群聊格式：每条消息前 [昵称] 表示说话人，"
                "不同昵称是不同的人；你自己是 assistant）"
            )
        req.system_prompt = (req.system_prompt or "") + STRICT_HINT'''
if old2 in t:
    t = t.replace(old2, new2, 1)
    q.write_text(t, encoding="utf-8")
    print("peer 已加说话人前缀")
else:
    print("MISS peer")
