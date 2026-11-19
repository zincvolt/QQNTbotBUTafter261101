import json, urllib.request
base = {"model":"x","messages":[{"role":"user","content":"说一句你好"}],"max_tokens":16}
variants = {
    "temp+top_p": {"temperature":0.7,"top_p":0.9},
    "top_k": {"top_k":40},
    "repeat_penalty": {"repeat_penalty":1.1},
    "frequency_penalty": {"frequency_penalty":0.3},
    "presence_penalty": {"presence_penalty":0.2},
    "min_p": {"min_p":0.05},
}
for name, extra in variants.items():
    body = dict(base); body.update(extra)
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            json.load(r)
        print(f"{name}: OK")
    except Exception as e:
        print(f"{name}: FAIL {e}")
