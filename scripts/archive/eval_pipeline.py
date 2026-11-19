import json, re, sqlite3, urllib.request
from pathlib import Path

# 1) 取今天所有群消息文本（去重、去机器人自己）
db = r"D:\QQNTBOT\apps\AstrBot\data\data_v4.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
msgs = []
for (c, name) in con.execute(
    "SELECT content, sender_name FROM platform_message_history ORDER BY id DESC LIMIT 400"
).fetchall():
    try:
        d = json.loads(c)
        t = " ".join(str(p.get("text","")) for p in d.get("message",[]) if p.get("type")=="plain").strip()
    except Exception:
        continue
    if t and len(t) >= 2 and name != "阿灰":
        msgs.append(t[:80])
print("样本:", len(msgs), "条群友消息")

cfg = json.loads(Path(r"D:\QQNTBOT\data\judge.json").read_text(encoding="utf-8"))
force_pat = [re.compile(p) for p in cfg.get("force_patterns", [])]
tpl = cfg["prompt"]
chance = json.loads(Path(r"D:\QQNTBOT\data\reply.json").read_text(encoding="utf-8"))["reply_chance"]

def judge(msg):
    body = {"model":"Qwen3-1.7B","messages":[{"role":"user","content":tpl.replace("{recent}","(略)").replace("{message}",msg)}],
            "max_tokens":4,"temperature":0.5,"grammar":'root ::= "0" | "1"',
            "chat_template_kwargs":{"enable_thinking":False}}
    req = urllib.request.Request("http://127.0.0.1:8082/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-judge-local"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

rule_hit = gate_pass = judge_pass = short = 0
for m in msgs:
    if len(m) <= 3:
        short += 1
        continue
    if any(p.search(m) for p in force_pat):
        rule_hit += 1
        gate_pass += 1
        continue
    try:
        if judge(m) == "1":
            judge_pass += 1
    except Exception:
        pass

expected = gate_pass + judge_pass * chance
passed_judge = rule_hit + judge_pass
print(f"规则必答 {rule_hit} | 判官通过 {judge_pass} | 太短跳过 {short}")
print(f"判官通过率(非短) {passed_judge/max(1,len(msgs)-short)*100:.0f}%")
print(f"加上概率闸 {chance}: 预计回复 {expected:.0f} 条 / {len(msgs)} 条 = {expected/len(msgs)*100:.0f}%")
print(f"若概率闸=1.0: {passed_judge/len(msgs)*100:.0f}%")
