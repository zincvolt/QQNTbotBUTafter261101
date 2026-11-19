import json, time, urllib.request
from pathlib import Path

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]

# 真实规模的判官 prompt：人格 + 若干上下文 + 待判消息
persona = json.loads(Path(r"D:\QQNTBOT\data\persona.json").read_text(encoding="utf-8"))["text"]
ctx = "\n".join([f"[群友/10:{i:02d}]: 今天这个群好热闹啊，有人打游戏吗" for i in range(20)])
prompt = f"{persona}\n\n最近群聊：\n{ctx}\n\n新消息：这游戏好玩吗\n\n只回 1 或 0。"

def call(messages, max_tokens, grammar=None, kwargs=None, tag=""):
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "temperature": 0.5, "top_p": 0.9}
    if grammar: body["grammar"] = grammar
    if kwargs: body["chat_template_kwargs"] = kwargs
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    t0=time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    dt=time.time()-t0
    m=d["choices"][0]["message"]; u=d.get("usage",{})
    reasoning = m.get("reasoning_content") or ""
    print(f"[{tag}] {dt:.2f}s prompt={u.get('prompt_tokens')} out={u.get('completion_tokens')} "
          f"思维链={len(reasoning)}字 正文={(m.get('content') or '')[:20]!r}")
    return dt

print("=== 真实规模 9B 判定（约 600 token 上下文） ===")
for i in range(3):
    call([{"role":"user","content":prompt}], 4, grammar='root ::= "0" | "1"', tag=f"judge{i+1}")

print("\n=== 开启思考链看长度 ===")
for i in range(2):
    call([{"role":"user","content":prompt}], 400, kwargs={"enable_thinking": True}, tag=f"think{i+1}")
