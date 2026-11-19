import json
from pathlib import Path
d = json.loads(Path(r"D:\QQNTBOT\_tmp_next.json").read_text(encoding="utf-8-sig"))
evs = d["props"]["pageProps"]["events"]
for e in evs[:3]:
    print(e["name"], "| thumbnail:", json.dumps(e.get("thumbnail"), ensure_ascii=False)[:200])
    print("   media:", json.dumps(e.get("media"), ensure_ascii=False)[:200])
