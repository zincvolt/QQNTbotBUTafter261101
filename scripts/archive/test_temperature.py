import json, urllib.request
from pathlib import Path

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
persona = json.loads(Path(r"D:\QQNTBOT\data\persona.json").read_text(encoding="utf-8"))["text"]
msgs = [{"role":"system","content":persona},
        {"role":"user","content":"开个新话题吧阿灰"},
        {"role":"assistant","content":"行，那说点正经的。"},
        {"role":"user","content":"随便，你说"}]

def ask(t, rp=None):
    body = {"model":model,"messages":msgs,"max_tokens":90,"temperature":t,"top_p":0.9}
    if rp: body["repeat_penalty"]=rp
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

for t, rp in ((0.85, None), (0.6, None), (0.6, 1.12)):
    print(f"=== temp={t} repeat_penalty={rp} ===")
    for i in range(3):
        print("  ", ask(t, rp).replace("\n"," | ")[:150])
