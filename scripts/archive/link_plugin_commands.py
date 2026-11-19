from pathlib import Path

# 1) COMMANDS.md 顶部加跳转
p = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = p.read_text(encoding="utf-8")
if "PLUGIN-COMMANDS.md" not in s:
    s = s.replace(
        "> 这份文档是**改词表时的唯一参考**。代码里的词表和这里必须一致。",
        "> 这份文档只讲**兽聚/运势/统计**这几个指令的词表。\n"
        "> 全部指令（含框架自带、表情管理、记忆、识图、API 切换）见 "
        "**[PLUGIN-COMMANDS.md](PLUGIN-COMMANDS.md)**。\n"
        "> 代码里的词表和这里必须一致。",
        1,
    )
    p.write_text(s, encoding="utf-8")
    print("COMMANDS.md 已加跳转")

# 2) PROJECT.md 文档索引
p2 = Path(r"D:\QQNTBOT\docs\PROJECT.md")
t = p2.read_text(encoding="utf-8")
if "PLUGIN-COMMANDS.md" not in t:
    t = t.replace(
        "都有 **[COMMANDS.md](COMMANDS.md)**",
        "都有 **[COMMANDS.md](COMMANDS.md)**；全部指令总表见 "
        "**[PLUGIN-COMMANDS.md](PLUGIN-COMMANDS.md)**",
        1,
    )
    p2.write_text(t, encoding="utf-8")
    print("PROJECT.md 已加索引")

# 3) README
p3 = Path(r"D:\QQNTBOT\README.md")
r = p3.read_text(encoding="utf-8")
if "PLUGIN-COMMANDS.md" not in r:
    r = r.replace(
        "指令词表见 `docs\\COMMANDS.md`",
        "指令词表见 `docs\\COMMANDS.md`，全部指令总表见 `docs\\PLUGIN-COMMANDS.md`",
    )
    p3.write_text(r, encoding="utf-8")
    print("README 已加索引")
