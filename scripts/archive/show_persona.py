import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]
print("=== 当前人格 ===")
print(text)
print("=== 结尾 ===")
print(repr(text[-60:]))
