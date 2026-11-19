from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

old = '''    if len(images) >= 3:
        return True
    # 大图（长截图、照片）通常是内容图，小图多是表情包
    for url in images:
        if isinstance(url, str) and len(url) > 60000:
            return True
    return False'''
new = '''    if len(images) >= 3:
        return True
    # 图够大（长截图/照片）基本是内容图
    for url in images:
        if isinstance(url, str) and len(url) > 25000:
            return True
    # 带文字的图消息通常是在说事，不是单纯刷表情
    if len(lowered.strip()) >= 3:
        return True
    return False'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("读图判断已放宽")
else:
    print("MISS")
