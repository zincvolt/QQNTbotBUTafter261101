from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_peer\main.py")
s = p.read_text(encoding="utf-8")

bad = '''    STRICT_HINT = (
    "\\n\\n（回答要求，优先于上面的写法偏好：一次最多两句、总共不超过50字；"
    "不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字）"
)

@filter.on_waiting_llm_request()'''
good = '''    @filter.on_waiting_llm_request()'''
if bad in s:
    s = s.replace(bad, good)
    print("fixed indentation")

const = '''STRICT_HINT = (
    "\\n\\n（回答要求，优先于上面的写法偏好：一次最多两句、总共不超过50字；"
    "不写括号里的动作和神态；不确定的事实直接说不确定，不要编名字）"
)

'''
if "STRICT_HINT =" not in s:
    s = s.replace("class Main(star.Star):", const + "class Main(star.Star):", 1)
    print("re-inserted at module level")

p.write_text(s, encoding="utf-8")
