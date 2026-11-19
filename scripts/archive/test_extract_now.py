import json, re, urllib.request
from pathlib import Path
s = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_ltm\main.py").read_text(encoding="utf-8")
tpl = re.search(r'EXTRACT_PROMPT = """(.*?)"""', s, re.S).group(1)
prompt = tpl.replace("{user}", "我叫阿凯，今年 28，在成都做前端。最近在学画画。").replace("{bot}", "哦哦，画画好啊")
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
body = {"model": cfg["provider"][0]["model"], "messages":[{"role":"user","content":prompt}],
        "max_tokens": 300, "temperature": 0.3, "chat_template_kwargs": {"enable_thinking": False}}
req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
with urllib.request.urlopen(req, timeout=240) as r:
    out = json.load(r)["choices"][0]["message"]["content"]
print("原始输出:", out[:300])
m = re.search(r"\[[\s\S]*\]", out)
print("解析:", json.loads(m.group(0)) if m else "没找到 JSON")
