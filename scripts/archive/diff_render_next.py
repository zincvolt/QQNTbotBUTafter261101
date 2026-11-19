import re
from pathlib import Path
cur = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py").read_text(encoding="utf-8")
bak = Path(r"D:\QQNTBOT\_backup\furcon_main_before_multi.py").read_text(encoding="utf-8")

def grab(text, name):
    m = re.search(rf"def {name}\([\s\S]*?(?=\ndef |\nclass )", text)
    return m.group(0) if m else "(missing)"

for name in ("render_next", "_draw_banner"):
    a, b = grab(cur, name), grab(bak, name)
    print(f"=== {name}: 当前 {len(a)} 字符 / 备份 {len(b)} 字符 一致={a.strip()==b.strip()}")
