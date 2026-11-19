import json, urllib.request
from pathlib import Path

cfg = json.loads(Path(r"D:\QQNTBOT\apps\AstrBot\data\cmd_config.json").read_text(encoding="utf-8-sig"))
model = cfg["provider"][0]["model"]
extra = cfg["provider"][0]["custom_extra_body"]
persona = json.loads(Path(r"D:\QQNTBOT\data\persona.json").read_text(encoding="utf-8"))["text"]
hint = ("\n\n（回答要求，优先于上面的写法偏好：一次最多两句、总共不超过50字；"
        "不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字；"
        "你确实能发表情包，别声称自己没有）")

cases = ["LS-5 是啥", "今天好累啊", "你们觉得这游戏好玩吗", "晚安"]
for msg in cases:
    body = {"model": model, "messages": [
        {"role": "system", "content": persona + hint},
        {"role": "user", "content": msg}],
        "max_tokens": 80, **{k: extra[k] for k in ("temperature","top_p","repeat_penalty") if k in extra}}
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer sk-llm-7d41c9e2"})
    with urllib.request.urlopen(req, timeout=240) as r:
        out = json.load(r)["choices"][0]["message"]["content"].strip()
    print(f"[{msg}] {len(out)}字 -> {out.replace(chr(10),' | ')}")
