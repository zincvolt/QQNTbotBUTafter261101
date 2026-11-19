import base64, json, time, urllib.request
p = r"D:\QQNTBOT\_backup\ocr_test.png"
b64 = base64.b64encode(open(p,"rb").read()).decode()
body = {"model":"PaddleOCR-VL-1.6","messages":[{"role":"user","content":[
    {"type":"text","text":"图上写了什么？只输出文字内容。"},
    {"type":"image_url","image_url":{"url":"data:image/png;base64,"+b64}}]}],"max_tokens":120}
for i in range(3):
    req = urllib.request.Request("http://127.0.0.1:8084/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-ocr-local"})
    t0=time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        d=json.load(r)
    print(f"run{i+1}: {time.time()-t0:.3f}s cached={d.get('cached')} -> {d['choices'][0]['message']['content'][:40]}")
