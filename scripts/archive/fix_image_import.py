from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
s = s.replace("from astrbot.api.message_components import Plain",
              "from astrbot.api.message_components import Image, Plain", 1)
p.write_text(s, encoding="utf-8")
print([l for l in s.splitlines() if "message_components" in l][:2])
