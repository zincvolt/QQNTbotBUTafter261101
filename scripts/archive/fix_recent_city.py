from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

# meta 里用 region（城市名）而不是 placeName（酒店），已结束不重复写"已结束"
old = '''    meta = " · ".join(
        x
        for x in (
            f"{event['start']}~{event['end']}",
            str(event.get("city", ""))[:14],
            label,
        )
        if x
    )'''
new = '''    meta = " · ".join(
        x
        for x in (
            f"{event['start']}~{event['end']}",
            str(event.get("region") or event.get("city", ""))[:12],
            label,
        )
        if x
    )'''
if old in s:
    s = s.replace(old, new, 1)
    print("meta uses region")

# 已结束行的 label 留空（数字后面已经有"天前"）
s = s.replace(
    'img.paste(_recent_row(ev, width, row_h, f"已结束 {over} 天", over, False),',
    'img.paste(_recent_row(ev, width, row_h, "", over, False),',
)
p.write_text(s, encoding="utf-8")
print("past label cleaned")
