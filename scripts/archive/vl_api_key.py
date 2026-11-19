from pathlib import Path
# peer 的本地 VL 调用要带 api-key
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")
old = '''            resp = await client.post(
                f"http://127.0.0.1:{port}/v1/chat/completions", json=payload
            )'''
new = '''            resp = await client.post(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                json=payload,
                headers={"Authorization": "Bearer sk-vl-local"},
            )'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("peer VL 带 key")
else:
    print("peer MISS")

q = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_visionmode\main.py")
t = q.read_text(encoding="utf-8")
old2 = '''            resp = await client.post(
                f"http://127.0.0.1:{port}/v1/chat/completions", json=payload
            )'''
new2 = '''            resp = await client.post(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                json=payload,
                headers={"Authorization": "Bearer sk-vl-local"},
            )'''
if old2 in t:
    t = t.replace(old2, new2, 1)
    q.write_text(t, encoding="utf-8")
    print("visionmode VL 带 key")
