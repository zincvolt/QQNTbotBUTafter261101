import re
from pathlib import Path
h = Path(r"D:\QQNTBOT\dashboard\index.html").read_text(encoding="utf-8")
scripts = re.findall(r"<script>(.*?)</script>", h, re.S)
Path(r"D:\QQNTBOT\_backup\dash_inline.js").write_text("\n".join(scripts), encoding="utf-8")
print("提取脚本块:", len(scripts), "总字符:", sum(len(s) for s in scripts))
