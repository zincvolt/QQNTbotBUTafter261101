from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

start = s.index('MARKER_RE = re.compile(')
end = s.index('@filter.on_decorating_result()', start)
helper = s[start:end]
s = s[:start] + s[end:]

# 修好被顶掉的缩进
s = s.replace('\n@filter.on_decorating_result()', '\n    @filter.on_decorating_result()', 1)

# helper 放到 class 之前
anchor = 'class Main('
idx = s.index(anchor)
s = s[:idx] + helper.strip() + '\n\n\n' + s[idx:]

p.write_text(s, encoding="utf-8")
print("helper 已移到类外，装饰器缩进已修")
