import json, urllib.request
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
persona = json.loads(Path(r"D:\QQNTBOT\data\persona.json").read_text(encoding="utf-8"))["text"]
tools = [{
  "type": "function",
  "function": {
    "name": "send_meme",
    "description": "从表情库里挑一张表情包发出去",
    "parameters": {"type": "object", "properties": {
        "category": {"type": "string", "description": "分类，比如 害羞、开心、无语"}},
        "required": ["category"]},
  },
}]
body = {"model": model, "messages": [
    {"role": "system", "content": persona},
    {"role": "user", "content": "发个表情包卖萌"}],
    "tools": tools, "max_tokens": 120, "temperature": 0.55}
req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
with urllib.request.urlopen(req, timeout=240) as r:
    d = json.load(r)
msg = d["choices"][0]["message"]
print("content:", (msg.get("content") or "")[:120])
print("tool_calls:", json.dumps(msg.get("tool_calls"), ensure_ascii=False)[:300])
