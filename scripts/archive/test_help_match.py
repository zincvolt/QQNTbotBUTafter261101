import ast, re
from pathlib import Path
PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
text = PLUGIN.read_text(encoding="utf-8")
block = re.search(r"COMMANDS: list\[tuple\[str, re\.Pattern\]\] = \[[\s\S]*?\n\]", text)
entries = [(e.elts[0].value, e.elts[1].args[0].value) for e in ast.parse(block.group(0)).body[0].value.elts]
funcs = re.search(r"def match_command[\s\S]*?(?=\nclass )", text).group(0)
cities = re.search(r"CITY_NAMES = \[[\s\S]*?\n\]", text).group(0)
provs = re.search(r"PROVINCES = \[[\s\S]*?\n\]", text).group(0)
ns = {"re": re}
exec('NAME_CALL = r"(阿灰|小灰|灰狼)"\nCOMMANDS = [\n'
     + "".join(f"    ({k!r}, re.compile({r!r})),\n" for k, r in entries)
     + "]\n" + provs + "\n" + cities + "\n" + funcs, ns)
m = ns["match_command"]
for body, slash in [("兽聚help", True), ("help", True), ("帮助", True), ("阿灰 帮助", False), ("兽聚help", False)]:
    print(f"{body!r} slash={slash} -> {m(body, slash=slash)}")
help_txt = re.search(r'HELP_TEXT = """(.*?)"""', text, re.S).group(1)
print("\n帮助文案前 3 行:")
for line in help_txt.splitlines()[:4]:
    print("  ", line)
