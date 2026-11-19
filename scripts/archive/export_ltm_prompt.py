import re
from pathlib import Path
plugin = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py").read_text(encoding="utf-8")
m = re.search(r'EXTRACT_PROMPT = """(.*?)"""', plugin, re.S)
prompt = m.group(1)
out = Path(r"D:\QQNTBOT\data\ltm_prompt.txt")
if not out.exists():
    out.write_text(prompt, encoding="utf-8")
    print("已导出默认提示词:", out, len(prompt), "字符")
else:
    print("已存在，不覆盖")
