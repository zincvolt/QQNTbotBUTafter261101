import json, urllib.request
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
base = {"model":model,"messages":[{"role":"user","content":"说一句你好"}],"max_tokens":16}
variants = {
    "baseline": {},
    "temp+top_p": {"temperature":0.7,"top_p":0.9},
    "repeat_penalty": {"repeat_penalty":1.1},
    "frequency_penalty": {"frequency_penalty":0.3},
    "min_p": {"min_p":0.05},
}
for name, extra in variants.items():
    body = dict(base); body.update(extra)
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            d = json.load(r)
        print(f"{name}: OK -> {d['choices'][0]['message']['content'][:30]!r}")
    except Exception as e:
        print(f"{name}: FAIL {e}")
