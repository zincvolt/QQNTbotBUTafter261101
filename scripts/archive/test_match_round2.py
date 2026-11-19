import ast, re
from pathlib import Path
PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
text = PLUGIN.read_text(encoding="utf-8")
block = re.search(r"COMMANDS: list\[tuple\[str, re\.Pattern\]\] = \[[\s\S]*?\n\]", text)
entries = []
for elt in ast.parse(block.group(0)).body[0].value.elts:
    entries.append((elt.elts[0].value, elt.elts[1].args[0].value))
funcs = re.search(r"def match_command[\s\S]*?(?=\nclass )", text).group(0)
cities = re.search(r"CITY_NAMES = \[[\s\S]*?\n\]", text).group(0)
provs = re.search(r"PROVINCES = \[[\s\S]*?\n\]", text).group(0)
ns = {"re": re}
exec('NAME_CALL = r"(阿灰|小灰|灰狼)"\nCOMMANDS = [\n'
     + "".join(f"    ({k!r}, re.compile({r!r})),\n" for k, r in entries)
     + "]\n" + provs + "\n" + cities + "\n" + funcs, ns)
match = ns["match_command"]
cases = ["/江苏下次展","/上海下次展","/广州上次展","/江苏有什么展","/成都下次展","/浙江上次展",
         "/启用功能","/关闭功能","/兽聚help","/下次展","/近期展","/运势","/群统计"]
for c in cases:
    slash = c.lstrip().startswith(("/","／"))
    body = re.sub(r"^\s*[/／]\s*", "", c).strip()
    k, city = match(body, slash=slash)
    print(f"{c:<16} -> {k or '-':<12} city={city}")
