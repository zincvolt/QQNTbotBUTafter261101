from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

# 名称右移，避免和"天前"重叠
s = s.replace('draw.text((190, y - 4), ev["name"][:16]', 'draw.text((214, y - 4), ev["name"][:16]')
s = s.replace('draw.text((190, y + 40), sub[:34]', 'draw.text((214, y + 40), sub[:30]')
s = s.replace('draw.text((190, y - 4), ev["name"][:16], font=mid, fill=(150, 154, 166))',
              'draw.text((214, y - 4), ev["name"][:16], font=mid, fill=(150, 154, 166))')
s = s.replace('draw.text((190, y + 40), f"已结束 {over} 天"',
              'draw.text((214, y + 40), f"{ev[\'start\']}~{ev[\'end\']} · 已结束 {over} 天"')
# 副标题只保留日期+城市，避免截断
s = s.replace('''        sub = " · ".join(
            x for x in (f"{ev['start']}~{ev['end']}", ev.get("city", ""),
                        ev.get("scale", "")) if x
        )''',
'''        sub = " · ".join(
            x for x in (f"{ev['start']}~{ev['end']}", ev.get("city", "")) if x
        )''')
p.write_text(s, encoding="utf-8")
print("layout refined")
