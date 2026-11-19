from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "- 右边三行：名称 / 日期 / **城市 · 场馆**（城市取 `region`，场馆取 `placeName`）",
    "- 右边三行：**全名** / 日期 / **城市 · 场馆**（城市取 `region`，场馆取 `placeName`）\n"
    "- **全名 = 主办 + 名称**：数据里只有 `name='双澜遗珠'`、`org='绒萌世界'`，\n"
    "  显示时要拼成「绒萌世界双澜遗珠」；若 `name` 已包含主办则不重复拼（`_full_name()`）",
)
s = s.replace(
    "| `city_next` | 该城市/省份即将举办的展会（最多 6 场，带天数） | 当天 + 城市 |",
    "| `city_next` | 该城市/省份即将举办的展会（最多 6 场，**带宣传图卡片**） | 当天 + 城市 |",
)
s = s.replace(
    "| `city_past` | 该城市/省份已举办的展会（最多 6 场） | 当天 + 城市 |",
    "| `city_past` | 该城市/省份已举办的展会（最多 6 场，灰色卡片） | 当天 + 城市 |",
)
p.write_text(s, encoding="utf-8")
print("docs updated")
