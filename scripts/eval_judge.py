"""Compare judge models on a fixed set of real group-chat messages."""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request

# (message, recent context, expected verdict)
CASES = [
    ("什么鬼？", "A：在吗  B：刚下班", "1"),
    ("这个AI好像只回你消息", "A：在吗  B：刚下班", "1"),
    ("我先切这个号说话", "A：我换个号", "0"),
    ("那吃面吧", "A：今天吃啥  B：随便", "0"),
    ("今天好累啊", "A：加班到十点", "1"),
    ("这图啥意思", "A：[图片]", "1"),
    ("哈哈哈哈", "A：太离谱了", "0"),
    ("方舟这期活动啥时候结束", "A：最近在玩方舟", "1"),
    ("我刚下班", "A：在吗", "0"),
    ("你们谁在", "B：都睡了？", "1"),
    ("机器人怎么不回话", "A：艾特它试试", "1"),
    ("别理他", "A：他一直在刷", "0"),
    ("这个尾巴设定你画的？", "A：[图片]", "1"),
    ("晚安", "A：困了", "0"),
    ("gore那种图你敢看吗", "A：我口味重", "1"),
    ("我换个号", "B：行", "0"),
    ("吃饭了吗", "A：刚回来", "0"),
    ("你能不能别刷屏", "A：刷屏了", "1"),
    ("好无聊啊", "A：没人说话", "1"),
    ("明天几点集合", "A：打球", "1"),
]

GRAMMAR = 'root ::= "0" | "1"'


def ask(url: str, key: str, model: str, prompt: str) -> tuple[str, float]:
    """Send one judgement request and return (verdict, seconds)."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4,
        "temperature": 0,
        "grammar": GRAMMAR,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    started = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    text = data["choices"][0]["message"]["content"].strip()
    return text, time.time() - started


def build_prompt(cfg_path: str, message: str, recent: str) -> str:
    """Render the judge prompt from data/judge.json."""
    cfg = json.loads(open(cfg_path, encoding="utf-8").read())
    return (
        cfg["prompt"]
        .replace("{recent}", recent or "(暂无更早消息)")
        .replace("{message}", message)
    )


def run(label: str, url: str, key: str, model: str) -> None:
    """Evaluate one endpoint and print a summary."""
    cfg_path = r"D:\QQNTBOT\data\judge.json"
    hits = 0
    total_time = 0.0
    detail = []
    for message, recent, expected in CASES:
        prompt = build_prompt(cfg_path, message, recent)
        try:
            verdict, secs = ask(url, key, model, prompt)
        except Exception as exc:  # noqa: BLE001
            verdict, secs = f"ERR:{exc}", 0.0
        total_time += secs
        ok = verdict == expected
        hits += ok
        detail.append((message, expected, verdict, secs, ok))
    print(f"\n=== {label} ({model}) ===")
    print(f"准确率 {hits}/{len(CASES)} = {hits / len(CASES):.0%}  平均 {total_time / len(CASES):.2f}s")
    for message, expected, verdict, secs, ok in detail:
        mark = "OK " if ok else "DIFF"
        print(f"  {mark} want={expected} got={verdict[:6]:6} {secs:.2f}s  {message[:26]}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8082/v1/chat/completions"
    key = sys.argv[2] if len(sys.argv) > 2 else "sk-judge-local"
    model = sys.argv[3] if len(sys.argv) > 3 else "qwen3-1.7b"
    run(model, url, key, model)
