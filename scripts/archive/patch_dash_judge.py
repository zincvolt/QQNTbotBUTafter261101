from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
old = '''                json={
                    "model": "qwen2.5-1.5b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4,
                    "temperature": 0,
                },'''
new = '''                json={
                    "model": "Qwen3-1.7B",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4,
                    "temperature": 0,
                    "grammar": 'root ::= "0" | "1"',
                    "chat_template_kwargs": {"enable_thinking": False},
                },'''
if old in s:
    p.write_text(s.replace(old, new), encoding="utf-8")
    print("dashboard patched")
else:
    print("pattern not found")
