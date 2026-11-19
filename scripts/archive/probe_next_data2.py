import json
from pathlib import Path
d = json.loads(Path(r"D:\QQNTBOT\_tmp_next.json").read_text(encoding="utf-8-sig"))
props = d.get("props", {}).get("pageProps", {})
print("pageProps keys:", list(props.keys())[:12])
for k, v in props.items():
    if isinstance(v, list) and v and isinstance(v[0], dict):
        print(f"\n=== {k}: {len(v)} 条，字段 {list(v[0].keys())}")
        for item in v[:2]:
            print("  ", {kk: str(vv)[:40] for kk, vv in list(item.items())[:8]})
