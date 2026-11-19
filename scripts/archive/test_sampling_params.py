import json, urllib.request
body = {
 "model": "x", "messages":[{"role":"user","content":"说一句你好"}], "max_tokens": 20,
 "temperature": 0.65, "top_p": 0.9, "frequency_penalty": 0.3, "presence_penalty": 0.2,
}
req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
try:
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
        print("OK ->", d["choices"][0]["message"]["content"][:40])
except Exception as e:
    print("FAIL / params not supported:", e)
