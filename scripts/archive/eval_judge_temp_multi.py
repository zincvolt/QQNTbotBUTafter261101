import json, sqlite3, urllib.request
from pathlib import Path

db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
msgs = []
for (c,) in con.execute("SELECT content FROM platform_message_history ORDER BY id DESC LIMIT 50").fetchall():
    try:
        d = json.loads(c)
        t = " ".join(str(p.get("text","")) for p in d.get("message",[]) if p.get("type")=="plain").strip()
    except Exception:
        continue
    if t and len(t) > 2:
        msgs.append(t[:80])
msgs = msgs[:20]
tpl = json.loads(Path(r"D:\QQNTBOT\data\judge.json").read_text(encoding="utf-8"))["prompt"]

def judge(msg, temp):
    body = {"model":"Qwen3-1.7B","messages":[{"role":"user","content":tpl.replace("{recent}","(略)").replace("{message}",msg)}],
            "max_tokens":4,"temperature":temp,"grammar":'root ::= "0" | "1"',
            "chat_template_kwargs":{"enable_thinking":False}}
    req = urllib.request.Request("http://127.0.0.1:8082/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-judge-local"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

for temp in (0.0, 0.5, 0.7, 1.0):
    rates = []
    for rep in range(3):
        hits = sum(1 for m in msgs if judge(m,temp) == "1")
        rates.append(round(hits/len(msgs)*100))
    print(f"temp={temp}: 判1比例 {rates}  (平均 {sum(rates)//3}%)")
