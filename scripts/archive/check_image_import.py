from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
# 确认 Image 已导入
if "from astrbot.api.message_components import" in s:
    print("看导入:", [l for l in s.splitlines() if "message_components" in l][:2])
else:
    print("缺导入")
