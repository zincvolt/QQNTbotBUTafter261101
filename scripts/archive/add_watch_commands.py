from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

# 1) 小时按北京时间统计（DB 里是 UTC 字符串）
old = '''        if created and len(created) >= 13:
            hours[created[11:13]] += 1'''
new = '''        if created and len(created) >= 19:
            try:
                utc = datetime.strptime(str(created)[:19], "%Y-%m-%d %H:%M:%S")
                hours[str((utc + timedelta(hours=8)).hour).zfill(2)] += 1
            except ValueError:
                pass'''
if old in s:
    s = s.replace(old, new, 1)
    print("hour -> CST")

# 2) 特别关心命令（仅管理员）
cmds = '''    ("watch_off", re.compile(r"(取消关心|不关心了|取消关注)")),
    ("watch", re.compile(r"^(关心|特别关心|关注)\\s*(.*)$")),
'''
s = s.replace('    ("fortune", re.compile(', cmds + '    ("fortune", re.compile(', 1)

handler = '''            if key in ("watch", "watch_off"):
                if str(event.get_sender_id()) not in ADMINS:
                    await event.send(event.plain_result("这个只有管理员能设"))
                    event.stop_event()
                    return
                if key == "watch_off":
                    WATCH_FILE.write_text(json.dumps({"enabled": False},
                                                     ensure_ascii=False), encoding="utf-8")
                    await event.send(event.plain_result("已取消特别关心"))
                    event.stop_event()
                    return
                rest = re.sub(r"^\\s*[/／]?\\s*(关心|特别关心|关注)\\s*", "", text).strip()
                if not rest:
                    await event.send(event.plain_result("用法：/关心 展会名 [HH:MM]"))
                    event.stop_event()
                    return
                bits = rest.split()
                name = bits[0]
                at = bits[1] if len(bits) > 1 else "09:00"
                WATCH_FILE.write_text(json.dumps({
                    "enabled": True,
                    "event": name,
                    "time": at,
                    "targets": [event.unified_msg_origin],
                }, ensure_ascii=False, indent=2), encoding="utf-8")
                await event.send(event.plain_result(f"已关心「{name}」，每天 {at} 播报"))
                event.stop_event()
                return

            if key == "help":'''
s = s.replace('            if key == "help":', handler, 1)

# 3) 管理员名单 + 帮助文案
s = s.replace('NAME_CALL = r"(阿灰|小灰|灰狼)"',
              'NAME_CALL = r"(阿灰|小灰|灰狼)"\nADMINS = {"1154487120"}', 1)
s = s.replace('''/兽聚help  这张说明''', '''/兽聚help  这张说明

管理员：
/关心 <展会名> [HH:MM]  设为特别关心，每天定时播报倒计时
/取消关心  关掉播报''', 1)

p.write_text(s, encoding="utf-8")
print("watch commands added")
