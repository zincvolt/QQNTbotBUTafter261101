import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]
anchor = "- 淋语的内核是反讽、拿腔拿调、装客气，用来阴阳和玩梗，不是卖萌"
add = "\n- 频率极低：整场对话用一两次就到顶了，大多数消息一个淋语词都别带"
if "频率极低" not in text:
    text = text.replace(anchor, anchor + add)
p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("ok, chars:", len(text))
print([l for l in text.splitlines() if "频率极低" in l])
