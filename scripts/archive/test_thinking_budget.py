import json, time, urllib.request
from pathlib import Path
cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]

def call(kwargs, tag):
    body = {"model": model, "messages":[{"role":"user","content":"用一句话说说猫"}],
            "max_tokens": 120, "temperature": 0.6, "chat_template_kwargs": kwargs}
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    t0=time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d=json.load(r)
        dt=time.time()-t0
        m=d["choices"][0]["message"]
        print(f"[{tag}] {dt:.1f}s 思维链={len(m.get('reasoning_content') or '')}字 正文={(m.get('content') or '')[:40]!r}")
    except Exception as e:
        print(f"[{tag}] FAIL {e}")

call({"enable_thinking": False}, "关闭")
call({"enable_thinking": True, "thinking_budget": 128}, "开启+预算128")
call({"enable_thinking": True, "thinking_budget": 512}, "开启+预算512")
