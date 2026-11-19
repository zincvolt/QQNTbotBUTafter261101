from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
s = s.replace('(("卖萌", "可爱", "萌"), "害羞"),', '(("卖萌", "可爱", "萌"), "开心"),')
p.write_text(s, encoding="utf-8")
print("害羞" in s, "卖萌映射已改")
