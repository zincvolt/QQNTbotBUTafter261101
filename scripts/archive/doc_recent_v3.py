from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = p.read_text(encoding="utf-8")
old_start = s.index("**多展会卡**（`/近期展`）")
old_end = s.index("| key | 输出 | 缓存 |")
new = '''**多展会卡**（`/近期展`）—— 每场一张通栏宣传图，底部加深色渐变压字：

```
近期展会
已结束 2 场 · 即将举办 10 场

已结束
[宣传图] 18 天前  魔法万圣夜小聚
                  2026-10-31~2026-10-31 · 长沙
[宣传图] 16 天前  餘獸重生 The last of …
                  2026-10-30~2026-11-01 · 台中

即将举办
[宣传图] 9 天  海洋之泪
               2026-11-27~2026-11-29 · 嘉兴
...
```

规则：

- **已结束的排在前面**（按时间倒序，最近的先），然后才是即将举办
- 每行高度 230px，宣传图铺满整行，底部 26% 起做渐变（指数 0.45，压得比较快）
- 左侧大字是**天数**：即将举办橙色「N 天」，已结束灰色「N 天前」
- 第二行是 `日期 · 城市 · 规模`，**城市取 region（城市名），不是酒店名**
- 一次最多 2 场已结束 + 10 场即将举办

'''
s = s[:old_start] + new + s[old_end:]
p.write_text(s, encoding="utf-8")
print("COMMANDS.md updated:", len(s.splitlines()), "行")
