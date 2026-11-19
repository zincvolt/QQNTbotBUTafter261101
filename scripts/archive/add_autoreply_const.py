from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\app.py")
s = p.read_text(encoding="utf-8")
if 'AUTOREPLY_FILE =' not in s:
    s = s.replace(
        'WATER_FILE = ROOT / "data" / "water.json"',
        'WATER_FILE = ROOT / "data" / "water.json"\nAUTOREPLY_FILE = ROOT / "data" / "autoreply.json"',
    )
    p.write_text(s, encoding="utf-8")
    print("added AUTOREPLY_FILE")
else:
    print("already present")
