"""Update the default period rule to cover trailing parenthetical actions."""

import json
from pathlib import Path

NEW_PATTERN = "。(?=\\s|$|[（(\\[【「『])"
NEW_RULE = [{"pattern": NEW_PATTERN, "to": "~"}]

reply = Path(r"D:\QQNTBOT\data\reply.json")
data = json.loads(reply.read_text(encoding="utf-8"))
data["text_rules"] = NEW_RULE
reply.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("reply.json rules:", data["text_rules"])

html = Path(r"D:\QQNTBOT\dashboard\index.html")
s = html.read_text(encoding="utf-8")
old_line = "const line = '。(?=\\\\s|$) => ~';"
new_line = "const line = '。(?=\\\\s|$|[（(\\\\[【「『]) => ~';"
if old_line in s:
    s = s.replace(old_line, new_line, 1)
    print("default-rule button updated")
else:
    print("button line not found, current:", [l.strip() for l in s.splitlines() if "fillDefaultRule" in l or "const line" in l][:3])
html.write_text(s, encoding="utf-8")
