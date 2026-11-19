from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\PROJECT.md")
s = p.read_text(encoding="utf-8")
if "改哪里" not in s:
    s = s.replace(
        "全部斜杠触发，输出一张图，不进模型。模糊词表、加词方法、权限、\n缓存规则都在 **[COMMANDS.md](COMMANDS.md)**。",
        "全部斜杠触发，输出一张图，不进模型。\n\n"
        "**要改触发词/城市表/帮助文案/卡片样式，看 [COMMANDS.md §1 改哪里速查](COMMANDS.md)**——\n"
        "里面有每个符号的文件和行号，以及数据文件（开关、特别关心）的位置。",
        1,
    )
    p.write_text(s, encoding="utf-8")
    print("PROJECT pointer updated")
else:
    print("already there")
