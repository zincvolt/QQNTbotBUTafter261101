import json
from pathlib import Path
p = Path(r"D:\QQNTBOT\data\persona.json")
text = json.loads(p.read_text(encoding="utf-8"))["text"]
add = "\n- 损人不骂人：可以阴阳、可以损，但别骂\"弱智\"\"闭嘴\"这种，那不像损像翻脸"
if "损人不骂人" not in text:
    text = text.replace("- 懒散、爱损人、偶尔犯傻，反应慢半拍", "- 懒散、爱损人、偶尔犯傻，反应慢半拍" + add)
p.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
print("chars:", len(text))
