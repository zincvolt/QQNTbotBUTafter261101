from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\PROJECT.md")
s = p.read_text(encoding="utf-8")
if "COMMANDS.md" not in s:
    anchor = "## 10. 控制台"
    block = """## 9.5 指令功能（兽聚/运势/统计）

全部斜杠触发，输出一张图，不进模型。模糊词表、加词方法、权限、
缓存规则都在 **[COMMANDS.md](COMMANDS.md)**。

| 指令 | 作用 |
|---|---|
| `/下次展` | 下一场兽聚倒计时 |
| `/近期展` | 10 场即将举办 + 2 场刚结束（缩略图网格） |
| `/哪里有什么展` | 同上 |
| `/哪里下次展` `/哪里上次展` | 按城市查（可带城市名） |
| `/运势` | 今日运势 |
| `/群统计` | 本群近 7 天活跃 |
| `/兽聚help` | 帮助 |
| `/关心 <展会> [HH:MM]` | 管理员设置每日播报 |

---

"""
    s = s.replace(anchor, block + anchor, 1)
    p.write_text(s, encoding="utf-8")
    print("PROJECT §9.5 added")

r = Path(r"D:\QQNTBOT\README.md")
t = r.read_text(encoding="utf-8")
if "COMMANDS.md" not in t:
    t = t.replace("踩坑心得见 `docs\\LESSONS.md`",
                  "踩坑心得见 `docs\\LESSONS.md`，指令词表见 `docs\\COMMANDS.md`")
    r.write_text(t, encoding="utf-8")
    print("README linked")
