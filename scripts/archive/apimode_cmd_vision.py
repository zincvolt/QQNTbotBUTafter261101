from pathlib import Path
p = Path(r"D:\QQNTBOT\apps\AstrBot\data\plugins\astrbot_plugin_apimode\main.py")
s = p.read_text(encoding="utf-8")
old = '''                set_thinking("off")
                stopped = unload_local_models()'''
new = '''                set_thinking("off")
                set_vision_mode("third_party")
                stopped = unload_local_models()'''
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("切换命令也联动识图")
else:
    print("MISS")
