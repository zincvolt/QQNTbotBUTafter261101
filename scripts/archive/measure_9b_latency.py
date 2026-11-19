import json, time, urllib.request
from pathlib import Path

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
persona = json.loads(Path(r"D:\QQNTBOT\data\persona.json").read_text(encoding="utf-8"))["text"]
hint = ("\n\n（回答要求，优先于上面的写法偏好：一次最多两句、总共不超过50字；"
        "不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字；"
        "你确实能发表情包，别声称自己没有）")

def call(messages, max_tokens, grammar=None, tag=""):
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "temperature": 0.5, "top_p": 0.9, "repeat_penalty": 1.12}
    if grammar: body["grammar"] = grammar
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    dt = time.time() - t0
    msg = d["choices"][0]["message"]
    usage = d.get("usage", {})
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    print(f"[{tag}] {dt:.2f}s | prompt_tok={usage.get('prompt_tokens')} "
          f"completion_tok={usage.get('completion_tokens')} | 正文 {len(content)} 字"
          f" | 思维链 {len(reasoning)} 字")
    return content, reasoning, dt

print("=== A. 9B 做一次 0/1 判定（带 grammar） ===")
for i in range(2):
    call([{"role":"user","content":"判断这句群聊要不要回，只答 1 或 0：今天好累啊"}], 4,
         grammar='root ::= "0" | "1"', tag="judge")

print("\n=== B. 9B 正常回一句（当前生产参数） ===")
for i in range(2):
    call([{"role":"system","content":persona+hint},
          {"role":"user","content":"今天好累啊"}], 80, tag="chat")
