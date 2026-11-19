import json
from pathlib import Path
d = json.loads(Path(r"D:\QQNTBOT\_tmp_next.json").read_text(encoding="utf-8"))
def walk(o, path="", depth=0):
    if depth > 4: return
    if isinstance(o, dict):
        for k, v in list(o.items())[:12]:
            p = f"{path}.{k}"
            if isinstance(v, (dict, list)):
                print(f"{p}  ({type(v).__name__}, len={len(v)})")
                walk(v, p, depth+1)
            else:
                print(f"{p} = {str(v)[:60]}")
    elif isinstance(o, list) and o:
        walk(o[0], path+"[0]", depth+1)
walk(d)
