from pathlib import Path
p = Path(r"D:\QQNTBOT\start-all.ps1")
s = p.read_text(encoding="utf-8")
for i in range(0, 4):
    s = s.replace(f"=== {i}/6", f"=== {i}/7")
p.write_text(s, encoding="utf-8")
print("编号统一为 /7")
