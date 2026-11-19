import json, urllib.request
from pathlib import Path

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
persona = json.loads(Path(r"D:\QQNTBOT\data\persona.json").read_text(encoding="utf-8"))["text"]

META = "\n\n（回答要求：一次最多两句，总共不超过50字；不要写括号里的动作和神态；不确定的事实直接说不确定，不要编名字）"

def ask(t, meta):
    sys_prompt = persona + (META if meta else "")
    msgs = [{"role":"system","content":sys_prompt},
            {"role":"user","content":"开个新话题吧阿灰"}]
    body = {"model":model,"messages":msgs,"max_tokens":70,"temperature":t,"top_p":0.9}
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

for label, t, meta in (("temp0.55 无附加", 0.55, False), ("temp0.55 + 要求", 0.55, True)):
    print(f"=== {label} ===")
    for i in range(3):
        out = ask(t, meta).replace("\n", " | ")
        print(f"   [{len(out)}字] {out[:120]}")
