import json, time, urllib.request
from pathlib import Path

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
tpl = json.loads(Path(r"D:\QQNTBOT\data\judge.json").read_text(encoding="utf-8"))["prompt"]
msgs = ["这游戏好玩吗", "今天好累啊", "哈哈哈哈", "你们在聊啥", "周末去哪玩"]

def j15(prompt):
    body={"model":"Qwen3-1.7B","messages":[{"role":"user","content":prompt}],"max_tokens":4,
          "temperature":0.5,"grammar":'root ::= "0" | "1"',"chat_template_kwargs":{"enable_thinking":False}}
    req=urllib.request.Request("http://127.0.0.1:8082/v1/chat/completions",data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-judge-local"})
    with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)["choices"][0]["message"]["content"].strip()

def j9(prompt):
    body={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":4,
          "temperature":0.2,"grammar":'root ::= "0" | "1"',"chat_template_kwargs":{"enable_thinking":False}}
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)["choices"][0]["message"]["content"].strip()

print(f"{'消息':<12} {'1.5B':>4} {'9B':>4} {'最终':>4}  1.5B耗时  9B耗时")
for m in msgs:
    prompt = tpl.replace("{recent}","(略)").replace("{message}",m)
    t0=time.time(); v1=j15(prompt); t1=time.time()-t0
    if v1=="1":
        t0=time.time(); v2=j9(prompt); t2=time.time()-t0
    else:
        v2="-"; t2=0
    final = "1" if (v1=="1" and (v2=="1" or v2=="-")) else "0"
    print(f"{m:<12} {v1:>4} {v2:>4} {final:>4}  {t1:>6.2f}s {t2:>6.2f}s")
