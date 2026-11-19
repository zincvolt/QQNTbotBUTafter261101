import json, time, urllib.request
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]

def call(extra, tag):
    body = {"model": model, "messages":[{"role":"user","content":"用一句话说说猫"}],
            "max_tokens": 300, "temperature": 0.6,
            "chat_template_kwargs": {"enable_thinking": True}}
    body.update(extra)
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    t0=time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d=json.load(r)
        dt=time.time()-t0
        m=d["choices"][0]["message"]
        print(f"[{tag}] {dt:.1f}s 思维链={len(m.get('reasoning_content') or '')}字 正文长度={len(m.get('content') or '')}")
    except Exception as e:
        print(f"[{tag}] FAIL {str(e)[:80]}")

call({"reasoning_budget": 128}, "reasoning_budget=128")
call({"reasoning_budget": 0}, "reasoning_budget=0")
