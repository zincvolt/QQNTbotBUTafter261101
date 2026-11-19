from pathlib import Path
p = Path(r"D:\QQNTBOT\start-all.ps1")
s = p.read_text(encoding="utf-8")
# 后续步骤编号顺延
for i in range(4, 8):
    s = s.replace(f"=== {i}/6", f"=== {i}/7")
p.write_text(s, encoding="utf-8")
print("步骤编号已更新")
