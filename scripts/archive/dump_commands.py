import ast, re
from pathlib import Path
PLUGIN = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
SAMPLES = ["/下次展","/近期展","/运势","/群统计","/兽聚help","/哪里下次展","/哪里上次展",
           "/有什么展","/成都哪里下次展","/广州有什么展","/上海下次展在哪",
           "阿灰 下次展","小灰运势","/关心 海洋之泪 09:00","/取消关心",
           "/乱写的指令","今天天气不错"]
text = PLUGIN.read_text(encoding="utf-8")
block = re.search(r"COMMANDS: list\[tuple\[str, re\.Pattern\]\] = \[[\s\S]*?\n\]", text)
entries = []
for elt in ast.parse(block.group(0)).body[0].value.elts:
    entries.append((elt.elts[0].value, elt.elts[1].args[0].value))
print(f"共 {len(entries)} 条规则\n")
for k, r in entries:
    print(f"{k:<12} {r}")
funcs = re.search(r"def match_command[\s\S]*?(?=\nclass )", text).group(0)
cities = re.search(r"CITY_NAMES = \[[\s\S]*?\n\]", text).group(0)
ns = {"re": re}
exec('NAME_CALL = r"(阿灰|小灰|灰狼)"\nCOMMANDS = [\n'
     + "".join(f"    ({k!r}, re.compile({r!r})),\n" for k, r in entries)
     + "]\n" + cities + "\n" + funcs, ns)
match = ns["match_command"]
print("\n=== 样例 ===")
for case in SAMPLES:
    slash = case.lstrip().startswith(("/", "／"))
    body = re.sub(r"^\s*[/／]\s*", "", case).strip()
    k, city = match(body, slash=slash)
    print(f"{case:<22} -> {k or '-':<10} {city}")
