import json, sqlite3, urllib.request, random, time
from pathlib import Path

# 取最近 40 条真实群消息
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute(
    "SELECT content FROM platform_message_history ORDER BY id DESC LIMIT 60"
).fetchall()
msgs = []
for (c,) in rows:
    try:
        d = json.loads(c)
        txt = " ".join(str(p.get("text","")) for p in d.get("message",[]) if p.get("type")=="plain").strip()
    except Exception:
        continue
    if txt and len(txt) > 2:
        msgs.append(txt[:80])
msgs = msgs[:40]
print("样本消息:", len(msgs))

prompt_cfg = json.loads(Path(r"D:\QQNTBOT\data\judge.json").read_text(encoding="utf-8"))
template = prompt_cfg["prompt"]

def judge(msg, temp):
    body = {"model": "Qwen3-1.7B", "messages": [{"role":"user","content":template.replace("{recent}","(略)").replace("{message}",msg)}],
            "max_tokens":4, "temperature":temp, "grammar": 'root ::= "0" | "1"',
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request("http://127.0.0.1:8082/v1/chat/completions",
        data=json.dumps(body).encode(), headers={"Content-Type":"application/json","Authorization":"Bearer sk-judge-local"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

for temp in (0.0, 0.7):
    hits = 0
    for m in msgs:
        try:
            if judge(m, temp) == "1":
                hits += 1
        except Exception:
            pass
    print(f"temperature={temp}: 判 1 的有 {hits}/{len(msgs)} = {hits/len(msgs)*100:.0f}%")
