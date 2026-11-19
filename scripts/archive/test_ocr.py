import base64, json, time, urllib.request
p = r"D:\QQNTBOT\_backup\ocr_test.png"
b64 = base64.b64encode(open(p, "rb").read()).decode()
body = {
    "model": "PaddleOCR-VL-1.6",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "图上写了什么？只输出文字内容。"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
    ]}],
    "max_tokens": 120,
    "temperature": 0,
}
req = urllib.request.Request(
    "http://127.0.0.1:8080/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer sk-llm-7d41c9e2"},
)
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    print("elapsed: %.1fs" % (time.time() - t0))
    print("answer :", data["choices"][0]["message"]["content"][:200])
except Exception as e:
    print("FAIL:", e)
