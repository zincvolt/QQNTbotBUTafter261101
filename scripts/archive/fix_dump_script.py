from pathlib import Path
p = Path(r"D:\QQNTBOT\scripts\archive\dump_commands.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '    node = ast.parse(block.group(0).split("=", 1)[1].strip())\n    entries = []\n    for elt in node.body[0].elts:',
    '    node = ast.literal_eval(block.group(0).split("=", 1)[1].strip().replace("re.compile(r", "re.compile(str(").replace(")", "))", 1)) if False else None\n    entries = []\n    for elt in ast.parse(block.group(0)).body[0].value.elts:',
)
p.write_text(s, encoding="utf-8")
print("patched")
