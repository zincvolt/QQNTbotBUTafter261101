import json, re
from pathlib import Path

# 新规则：句号后面是 空白/结尾/开括号 都算句末
PATTERN = r"。(\s|$|[（(\[【「『])"
cands = [
    "行吧。那我先躺一会。",
    "你好。（歪头）",
    "真的吗。（歪头）晚安。",
    "说完了。 （动作）",
    "第一句。第二句。第三句。",
    "好的。。",
    "（揉眼）行吧。",
]
for t in cands:
    print(repr(t), "->", repr(re.sub(PATTERN, "~", t)))
