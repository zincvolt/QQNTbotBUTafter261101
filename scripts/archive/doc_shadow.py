from pathlib import Path
p = Path(r"D:\QQNTBOT\docs\COMMANDS.md")
s = p.read_text(encoding="utf-8")
old = '''- 背景是宣传图，但**统一压灰压暗**（去色 + 与底色混合 58%），当纹理用，不和文字打架
- 卡片底部最后 48% 再做一次柔和过渡到卡片底色，收尾无色偏'''
new = '''- **未开始的保留原色**（只压 18% 亮度防过曝），**已结束的整张转灰**
- 文字不靠遮罩压暗，而是给文字加**柔和阴影**（四向 + 右下偏移各铺一层，模糊 2px），
  这样背景颜色不会被盖掉
- 卡片底部最后 45% 轻微过渡到卡片底色，收尾自然'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("docs updated")
else:
    print("MISS")
