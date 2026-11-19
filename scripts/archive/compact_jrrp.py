from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_furcon\main.py")
s = p.read_text(encoding="utf-8")

# 1) 去掉那行说明
s = s.replace('''    draw.text((60, 596), "同一 QQ 同一天结果固定，明天重算", font=small,
              fill=(140, 146, 160))
''', "")

# 2) 高度 900 -> 740
s = s.replace("    width, height = 900, 900\n    img = Image.new(\"RGB\", (width, height), (24, 26, 32))\n    draw = ImageDraw.Draw(img)\n    big, huge, mid, small = _font(48), _font(150), _font(34), _font(24)",
              "    width, height = 900, 740\n    img = Image.new(\"RGB\", (width, height), (24, 26, 32))\n    draw = ImageDraw.Draw(img)\n    big, huge, mid, small = _font(48), _font(140), _font(32), _font(24)")

# 3) 元素上移，观感更紧凑
s = s.replace('draw.text((60, 176), str(jrrp), font=huge, fill=color)', 'draw.text((60, 166), str(jrrp), font=huge, fill=color)')
s = s.replace('draw.text((offset, 268), "分", font=mid, fill=color)', 'draw.text((offset, 246), "分", font=mid, fill=color)')
s = s.replace('draw.text((60, 380), level, font=big, fill=color)', 'draw.text((60, 340), level, font=big, fill=color)')
s = s.replace('draw.rectangle((60, 470, 820, 502), outline=(70, 74, 84), width=2)', 'draw.rectangle((60, 430, 820, 462), outline=(70, 74, 84), width=2)')
s = s.replace('draw.rectangle((60, 470, 60 + int(760 * jrrp / 100), 502), fill=color)', 'draw.rectangle((60, 430, 60 + int(760 * jrrp / 100), 462), fill=color)')
s = s.replace('draw.text((60, 530), f"今日提示：{tip}"', 'draw.text((60, 496), f"今日提示：{tip}"')
s = s.replace('draw.text((60, height - 56), f"{day} · 仅供娱乐"', 'draw.text((60, height - 48), f"{day} · 仅供娱乐"')

p.write_text(s, encoding="utf-8")
print("jrrp card compacted")
