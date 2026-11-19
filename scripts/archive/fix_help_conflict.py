from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")
old = '("help", re.compile(r"^(帮助|help|兽聚help|指令|能干什么|功能列表|用法)$", re.I)),'
new = '("help", re.compile(r"^(兽聚help|兽聚指令|兽聚功能|兽聚用法)$", re.I)),'
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("furcon 不再抢占 /help")
else:
    print("MISS")
