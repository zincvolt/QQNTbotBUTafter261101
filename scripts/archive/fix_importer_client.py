from pathlib import Path
p = Path(r"D:\QQNTBOT\scripts\import_kb.py")
s = p.read_text(encoding="utf-8")
s = s.replace("import json\nimport time", "import contextlib\nimport json\nimport time")
s = s.replace("    with client_with_token() as c:", "    with contextlib.closing(client_with_token()) as c:")
p.write_text(s, encoding="utf-8")
print("fixed client reuse")
