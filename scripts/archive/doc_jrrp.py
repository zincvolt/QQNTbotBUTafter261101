"""Document the jrrp algorithm and new aliases."""

from pathlib import Path

DOC = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = DOC.read_text(encoding="utf-8")

s = s.replace(
    "| 运势 | `fortune` | `运势` `运气` `抽个签` `求签` `吉凶` `今日份` `转运` |",
    "| 运势 / 人品 | `fortune` | `运势` `运气` `抽个签` `求签` `吉凶` `今日份` `转运` `人品` `jrrp` `jrys` |",
)

section = """
### 今日人品（jrrp）算法

```
seed = sha256(f"{QQ号}|{YYYYMMDD}")
jrrp = int(seed[:8], 16) % 101        # 0 ~ 100
提示语 = FORTUNE_TIPS[int(seed[8:12], 16) % len(FORTUNE_TIPS)]
```

- **同一 QQ + 同一天 → 结果恒定**，刷新多少次都一样
- 换一天自动重算
- 不同 QQ 相互独立，平均分约 50

等级划分：

| 分数 | 等级 | 占比（2000 次抽样） |
|---|---|---|
| 90~100 | 大吉 | 11% |
| 75~89 | 中吉 | 15% |
| 60~74 | 小吉 | 15% |
| 40~59 | 平 | 20% |
| 20~39 | 小凶 | 20% |
| 0~19 | 凶 | 20% |

要调口味改 `fortune_of()` 里的阈值即可，不用动别处。

"""

s = s.replace("### 省份查询", section + "### 省份查询", 1)
DOC.write_text(s, encoding="utf-8")
print("COMMANDS.md lines:", len(s.splitlines()))
