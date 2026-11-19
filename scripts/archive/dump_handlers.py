from pathlib import Path
s = Path(r"D:\QQNTBOT\dashboard\app.py").read_text(encoding="utf-8")
import re
for name in ("get_thinking","save_thinking","get_sampling","save_sampling","models","switch_model"):
    m = re.search(rf'@app\.(get|post)\("[^"]+"\)\n(?:async )?def {name}\([\s\S]*?(?=\n@app\.|\n# ---)', s)
    if m:
        print(f"--- {name} ({len(m.group(0))} chars) ---")
        print(m.group(0)[:900])
        print()
