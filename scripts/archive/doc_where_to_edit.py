"""Rewrite COMMANDS.md section 1 into a complete "where to change what" map."""

from pathlib import Path

DOC = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = DOC.read_text(encoding="utf-8")

start = s.index("## 1. 词表存在哪")
end = s.index("## 2. 匹配规则")

new = '''## 1. 改哪里（速查）

**所有代码都在一个文件里**：

```
D:\\QQNTBOT\\apps\\AstrBot\\data\\plugins\\astrbot_plugin_furcon\\main.py
```

用记事本 / VSCode 打开，按 `Ctrl+G` 跳行号。行号会随改动漂移，**以符号名为准**
（VSCode 里 `Ctrl+Shift+O` 按名字跳）。

| 想改什么 | 符号 / 文件 | 当前行号 | 说明 |
|---|---|---|---|
| **指令触发词** | `COMMANDS` 列表 | 64 | 每条 `(key, 正则)`，从上往下匹配 |
| **认哪些城市** | `CITY_NAMES` | 133 | 市级，用于提取句中的城市名 |
| **认哪些省份** | `PROVINCES` | 127 | 只用于识别，不含城市 |
| **省份展开成哪些城市** | `PROVINCE_CITIES` | 80 | `/江苏下次展` 靠这个映射 |
| **管理员 QQ** | `ADMINS` | 62 | 决定谁能用 `/启用功能`、`/关心` |
| **帮助文案** | `HELP_TEXT` | 808 | `/兽聚help` 原样输出这段 |
| **运势等级/颜色** | `FORTUNE_LEVELS` | 141 | 目前按分数段算，改阈值在 `fortune_of()` |
| **运势提示语库** | `FORTUNE_TIPS` | 149 | 随机一句，按 QQ+日期定死 |
| **单场卡样式** | `render_next()` | 327 | 宣传图 + 大字倒计时 + 之后三场 |
| **多场卡样式** | `render_recent()` | 544 | 已结束在前 + 圆角卡片列表 |
| **单行卡片样式** | `_recent_row()` | 475 | 近期展/城市卡共用的一行 |
| **城市卡样式** | `render_city()` | 606 | 复用 `_recent_row()` |
| **运势卡样式** | `render_fortune()` | 690 | 900×740 |
| **群统计卡样式** | `render_stats()` | 760 | 发言榜 + 时段柱状图 |
| **展会全名怎么拼** | `_full_name()` | 459 | 主办 + 名称 |
| **指令匹配规则** | `match_command()` | 858 | 斜杠/喊名字/城市提取 |

### 数据文件（不用改代码，直接编辑 JSON）

| 文件 | 作用 | 改完要重启吗 |
|---|---|---|
| `data\\furcon_enabled.json` | 哪些群启用了功能 | 不用，读写即生效 |
| `data\\furcon_watch.json` | 特别关心的展会和播报时间 | 不用 |
| `data\\furcons_cache.json` | 展会数据缓存（2MB 以内） | 不用，删了就重新抓 |
| `data\\furcons_cards\\` | 生成过的图片（按天缓存） | 删掉会重新生成 |

### 其他相关配置（不属于本插件）

| 想改什么 | 文件 |
|---|---|
| 机器人人格 | `data\\persona.json`（**你自己维护，我不动**） |
| 判官提示词/触发词 | `data\\judge.json` |
| 回复频率、句号规则、双判官 | `data\\reply.json` |
| 群白名单、管理员 | `apps\\AstrBot\\data\\cmd_config.json` |

### 改完必须做的两件事

```powershell
# 1. 验证词表（不用发 QQ 消息，直接看匹配结果）
D:\\QQNTBOT\\apps\\AstrBot\\.venv\\Scripts\\python.exe D:\\QQNTBOT\\scripts\\archive\\dump_commands.py

# 2. 重启 AstrBot 让代码生效（约 10 秒）
D:\\QQNTBOT\\scripts\\restart-astrbot.ps1
```

改 JSON 数据文件（开关、特别关心）**不需要重启**。

---

'''

s = s[:start] + new + s[end:]
DOC.write_text(s, encoding="utf-8")
print("COMMANDS.md rewritten section 1:", len(s.splitlines()), "行")
