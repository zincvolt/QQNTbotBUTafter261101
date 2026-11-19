from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = p.read_text(encoding="utf-8")
if "生成耗时" not in s:
    s = s.replace(
        "| `help` | 纯文字帮助 | 无 |",
        "| `help` | 纯文字帮助 | 无 |\n\n"
        "**生成耗时**：每张卡片底部都有「生成于 MM-DD HH:MM · N ms」。\n"
        "N 是**首次画这张图**的耗时（含下载宣传图），当天再问同一个指令会直接复用文件，\n"
        "所以底部仍是首次生成时的时间/耗时——这是对的，不是 bug。",
        1,
    )
    p.write_text(s, encoding="utf-8")
    print("docs updated")
else:
    print("already documented")
